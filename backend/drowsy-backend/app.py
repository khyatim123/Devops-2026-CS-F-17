import sys
import time
import threading
import urllib.request
import os
import shutil
import subprocess
import tempfile
import wave
import math
import asyncio
from collections import deque
import struct
from dataclasses import dataclass
from pathlib import Path

# Ensure backend directory is available for local imports
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import cv2
import mediapipe as mp
import numpy as np

from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from metrics import (
    HTTP_REQUESTS,
    HTTP_LATENCY,
    DETECTOR_RESTARTS,
    ALERT_EVENTS,
    update_detector_metrics,
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Spectra Drowsiness Detection API",
    description="Webcam-based drowsiness detection backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# PROMETHEUS METRICS
# =========================================================

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# =========================================================
# SHARED STATE AND THREAD MANAGEMENT
# =========================================================

stop_event = threading.Event()

status_lock = threading.Lock()
detector_lock = threading.Lock()

detector_thread = None

# Latest annotated frame (JPEG) shared with the video endpoints
frame_lock = threading.Lock()
latest_jpeg = None
latest_frame_id = 0

SHOW_WINDOW = os.getenv("SPECTRA_SHOW_WINDOW", "1") == "1"


def publish_frame(frame):

    global latest_jpeg, latest_frame_id

    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])

    if ok:
        with frame_lock:
            latest_jpeg = buffer.tobytes()
            latest_frame_id += 1


def clear_frame():

    global latest_jpeg

    with frame_lock:
        latest_jpeg = None

detector_status = {
    "running": False,
    "eyes": "UNKNOWN",
    "ear": None,
    "closure_duration": 0.0,
    "alert": False,
    "alert_count": 0,
    "last_alert_at": None,
    "perclos": 0.0,
    "perclos_high": False,
    "mar": None,
    "yawning": False,
    "yawn_count": 0,
    "message": "Detector is stopped"
}


def update_status(**kwargs):
    with status_lock:
        detector_status.update(kwargs)


def get_status_snapshot():
    with status_lock:
        return detector_status.copy()


# =========================================================
# HTTP MONITORING MIDDLEWARE
# =========================================================

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):

    handler = request.url.path

    if handler in ("/metrics", "/metrics/"):
        update_detector_metrics(get_status_snapshot())

    start = time.perf_counter()

    response: Response = await call_next(request)

    duration = time.perf_counter() - start

    HTTP_REQUESTS.labels(
        method=request.method,
        handler=handler,
        status_code=str(response.status_code)
    ).inc()

    HTTP_LATENCY.labels(
        handler=handler
    ).observe(duration)

    return response


# =========================================================
# EYE LANDMARK INDEXES
# =========================================================

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)

# Inner-mouth landmarks: left corner, 3 upper-lip points, right corner,
# then the 3 matching lower-lip points (in the same order, mirrored)
MOUTH = (78, 81, 13, 311, 308, 402, 14, 178)

PERCLOS_WINDOW = 60.0     # seconds of history used for PERCLOS
PERCLOS_ALERT = 0.15      # >=15% eyes-closed time => fatigue warning
MAR_THRESHOLD = 0.5       # mouth opening ratio that counts as "wide open"
YAWN_SECONDS = 1.5        # mouth must stay wide open this long = a yawn


# =========================================================
# EYE ASPECT RATIO
# =========================================================

def eye_aspect_ratio(eye_points):

    p0, p1, p2, p3, p4, p5 = eye_points

    vertical_one = np.linalg.norm(p1 - p5)
    vertical_two = np.linalg.norm(p2 - p4)
    horizontal = np.linalg.norm(p0 - p3)

    if horizontal <= 0:
        return 0.0

    return (
        vertical_one + vertical_two
    ) / (2.0 * horizontal)


# =========================================================
# LANDMARKS TO PIXEL COORDINATES
# =========================================================

def mouth_aspect_ratio(m):
    """MAR = average mouth opening / mouth width (large when yawning)."""
    vertical = (
        np.linalg.norm(m[1] - m[7])
        + np.linalg.norm(m[2] - m[6])
        + np.linalg.norm(m[3] - m[5])
    ) / 3.0
    horizontal = np.linalg.norm(m[0] - m[4])
    return float(vertical / horizontal) if horizontal > 0 else 0.0


def landmarks_to_points(
    face_landmarks,
    indices,
    frame_width,
    frame_height
):

    landmarks = (
        face_landmarks.landmark
        if hasattr(face_landmarks, "landmark")
        else face_landmarks
    )

    points = []

    for index in indices:

        landmark = landmarks[index]

        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)

        points.append([x, y])

    return np.array(points, dtype=np.float32)


# =========================================================
# EYE CLOSURE TRACKER
# =========================================================

@dataclass
class ClosureTracker:

    threshold_seconds: float = 2.0

    # Open-eye frames shorter than this do not reset the timer, so a single
    # noisy landmark frame can no longer cancel a real closure.
    open_grace_seconds: float = 0.2

    closed_since: float | None = None
    _open_since: float | None = None

    def reset(self):

        self.closed_since = None
        self._open_since = None

    def update(self, eyes_closed, now=None):

        if now is None:
            now = time.monotonic()

        if eyes_closed:

            self._open_since = None

            if self.closed_since is None:
                self.closed_since = now

            return now - self.closed_since

        # Eyes open
        if self.closed_since is None:
            return 0.0

        if self._open_since is None:
            self._open_since = now

        # Only reset once eyes stayed open longer than the grace window
        if now - self._open_since >= self.open_grace_seconds:
            self.reset()
            return 0.0

        return now - self.closed_since

    def alert_active(self, closure_duration):

        return closure_duration >= self.threshold_seconds


# =========================================================
# SOUND ALERT
# =========================================================

class PerclosTracker:
    """PERCLOS = share of recent time the eyes were closed (time-weighted)."""

    def __init__(self, window=PERCLOS_WINDOW, min_seconds=5.0):

        self.window = window
        self.min_seconds = min_seconds
        self.samples = deque()   # (timestamp, dt, closed)
        self.last = None

    def update(self, closed, now):

        if self.last is not None:
            self.samples.append((now, min(now - self.last, 0.5), closed))

        self.last = now

        while self.samples and now - self.samples[0][0] > self.window:
            self.samples.popleft()

        total = sum(dt for _, dt, _ in self.samples)

        if total < self.min_seconds:
            return 0.0

        closed_time = sum(dt for _, dt, c in self.samples if c)

        return closed_time / total


class AlarmPlayer:
    """
    Plays the alarm in its own thread so the detection loop is never blocked,
    and keeps repeating it for as long as the alert is active.
    Works on Windows, macOS and Linux (falls back to the terminal bell).
    """

    def __init__(self):

        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._wav_path = None
        self._warned = False

    def _ensure_wav(self):

        if self._wav_path and os.path.exists(self._wav_path):
            return self._wav_path

        path = os.path.join(tempfile.gettempdir(), "spectra_alarm.wav")

        rate = 22050
        frames = bytearray()

        # Two-tone siren: 880 Hz then 1320 Hz, 0.25 s each
        for freq in (880, 1320):
            for i in range(int(rate * 0.25)):
                value = int(24000 * math.sin(2 * math.pi * freq * i / rate))
                frames += struct.pack("<h", value)

        with wave.open(path, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(bytes(frames))

        self._wav_path = path
        return path

    def is_playing(self):

        return self._thread is not None and self._thread.is_alive()

    def start(self):

        with self._lock:

            if self.is_playing():
                return

            self._stop.clear()
            self._warned = False

            self._thread = threading.Thread(
                target=self._loop,
                name="alarm-player",
                daemon=True
            )

            self._thread.start()

    def stop(self):

        self._stop.set()

    def _loop(self):

        while not self._stop.is_set():

            self._play_once()

            self._stop.wait(0.1)

    def _play_once(self):

        try:

            wav = self._ensure_wav()

            if sys.platform == "win32":

                import winsound

                winsound.PlaySound(wav, winsound.SND_FILENAME)
                return

            if sys.platform == "darwin" and shutil.which("afplay"):

                subprocess.run(["afplay", wav], timeout=5, check=False)
                return

            for command in (
                ["paplay", wav],
                ["aplay", "-q", wav],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav],
            ):

                if shutil.which(command[0]):

                    subprocess.run(command, timeout=5, check=False)
                    return

        except Exception as exc:

            print(f"Alarm playback error: {exc}")

        # Fallback: terminal bell + message (no audio player available)
        if not self._warned:

            print("ALERT: Prolonged eye closure detected! "
                  "(no audio player found on server)")

            self._warned = True

        sys.stdout.write("\a")
        sys.stdout.flush()

        self._stop.wait(0.5)


alarm = AlarmPlayer()


# =========================================================
# CAMERA OPENING (tries several backends, verifies a real frame)
# =========================================================

def _backends():

    if sys.platform == "win32":
        return [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("ANY", cv2.CAP_ANY)]

    if sys.platform == "darwin":
        return [("AVFOUNDATION", cv2.CAP_AVFOUNDATION), ("ANY", cv2.CAP_ANY)]

    return [("V4L2", cv2.CAP_V4L2), ("ANY", cv2.CAP_ANY)]


def open_camera(camera_index):

    tried = []

    for name, backend in _backends():

        cap = cv2.VideoCapture(camera_index, backend)

        if cap.isOpened():

            # Some cameras open but never deliver frames; warm up and check.
            for _ in range(15):

                ok, frame = cap.read()

                if ok and frame is not None:
                    print(f"Camera {camera_index} opened using {name}.")
                    return cap

                time.sleep(0.1)

            tried.append(f"{name}: opened but returned no frames")

        else:
            tried.append(f"{name}: could not open")

        cap.release()

    raise RuntimeError(
        f"Could not open camera {camera_index} ({'; '.join(tried)}). "
        "Close other apps using the camera (Zoom/Teams/browser tabs), "
        "check OS camera permissions, or try another camera_index."
    )


# =========================================================
# ENSURE MEDIAPIPE MODEL EXISTS
# =========================================================

def ensure_model(model_path):

    if model_path.exists() and model_path.stat().st_size > 0:
        return

    print("Downloading MediaPipe face landmarker model...")

    model_url = (
        "https://storage.googleapis.com/"
        "mediapipe-models/face_landmarker/"
        "face_landmarker/float16/1/"
        "face_landmarker.task"
    )

    temporary_path = model_path.with_suffix(
        model_path.suffix + ".download"
    )

    try:

        urllib.request.urlretrieve(
            model_url,
            str(temporary_path)
        )

        if temporary_path.stat().st_size == 0:
            raise RuntimeError("Downloaded model file is empty.")

        temporary_path.replace(model_path)

        print("Model downloaded successfully.")

    except Exception:

        if temporary_path.exists():
            temporary_path.unlink()

        raise


# =========================================================
# MAIN DROWSINESS DETECTOR
# =========================================================

def run(
    camera_index=0,
    eye_threshold=0.21,
    closure_seconds=2.0,
    stop_signal=None
):

    FACE_LOSS_GRACE = 1.0          # head dips / tracking drops while eyes closed
    ALERT_FACE_LOSS_HOLD = 10.0    # keep ringing this long if face is lost mid-alert
    MAX_FAILED_READS = 30          # tolerate transient camera hiccups


    if stop_signal is None:
        stop_signal = threading.Event()

    camera = None
    face_landmarker = None

    previous_alert_state = False
    last_timestamp_ms = 0
    face_lost_since = None
    failed_reads = 0

    perclos_tracker = PerclosTracker()
    perclos_value = 0.0
    mouth_open_since = None
    yawn_total = 0
    yawn_was_active = False

    try:

        # ---------------------------------------------
        # LOAD MODEL
        # ---------------------------------------------

        model_path = Path(__file__).with_name(
            "face_landmarker.task"
        )

        ensure_model(model_path)

        # ---------------------------------------------
        # INITIALIZE MEDIAPIPE
        # ---------------------------------------------

        options = mp.tasks.vision.FaceLandmarkerOptions(

            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(model_path)
            ),

            running_mode=mp.tasks.vision.RunningMode.VIDEO,

            num_faces=1,

            min_face_detection_confidence=0.5,

            min_face_presence_confidence=0.5,

            min_tracking_confidence=0.5
        )

        face_landmarker = (
            mp.tasks.vision.FaceLandmarker.create_from_options(
                options
            )
        )

        # ---------------------------------------------
        # OPEN WEBCAM
        # ---------------------------------------------

        camera = open_camera(camera_index)

        print("Webcam opened successfully.")
        print("Starting Spectra Drowsiness Detector...")
        print("Press Q or Esc to quit.")

        tracker = ClosureTracker(
            threshold_seconds=closure_seconds
        )

        update_status(
            running=True,
            eyes="NO FACE",
            ear=None,
            closure_duration=0.0,
            alert=False,
            perclos=0.0,
            perclos_high=False,
            mar=None,
            yawning=False,
            yawn_count=0,
            message="Detector is running"
        )

        # =============================================
        # DETECTION LOOP
        # =============================================

        while not stop_signal.is_set():

            success, frame = camera.read()

            if not success:

                failed_reads += 1

                if failed_reads >= MAX_FAILED_READS:

                    raise RuntimeError(
                        "Could not read frame from webcam."
                    )

                time.sleep(0.03)

                continue

            failed_reads = 0

            now = time.monotonic()

            frame_height, frame_width = frame.shape[:2]

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame
            )

            # MediaPipe VIDEO mode requires increasing timestamps
            timestamp_ms = max(
                int(time.monotonic() * 1000),
                last_timestamp_ms + 1
            )

            last_timestamp_ms = timestamp_ms

            result = face_landmarker.detect_for_video(
                mp_image,
                timestamp_ms
            )

            eyes_status = "NO FACE"
            average_ear = None
            mar_value = None
            yawning = False
            closure_duration = 0.0
            alert_active = False

            # =========================================
            # FACE DETECTED
            # =========================================

            if result.face_landmarks:

                face_lost_since = None

                face_landmarks = result.face_landmarks[0]

                left_eye = landmarks_to_points(
                    face_landmarks,
                    LEFT_EYE,
                    frame_width,
                    frame_height
                )

                right_eye = landmarks_to_points(
                    face_landmarks,
                    RIGHT_EYE,
                    frame_width,
                    frame_height
                )

                # Calculate EAR for both eyes
                left_ear = eye_aspect_ratio(left_eye)

                right_ear = eye_aspect_ratio(right_eye)

                average_ear = (
                    left_ear + right_ear
                ) / 2.0

                # Determine eye state
                eyes_closed = average_ear < eye_threshold

                # Track continuous eye closure
                closure_duration = tracker.update(
                    eyes_closed
                )

                # Determine alert state
                alert_active = tracker.alert_active(
                    closure_duration
                )

                eyes_status = (
                    "CLOSED" if eyes_closed else "OPEN"
                )

                # PERCLOS: share of the last 60 s with eyes closed
                perclos_value = perclos_tracker.update(eyes_closed, now)

                # Yawning: mouth wide open for YAWN_SECONDS or longer
                mouth = landmarks_to_points(
                    face_landmarks, MOUTH, frame_width, frame_height
                )

                mar_value = mouth_aspect_ratio(mouth)

                if mar_value > MAR_THRESHOLD:

                    if mouth_open_since is None:
                        mouth_open_since = now

                    yawning = (now - mouth_open_since) >= YAWN_SECONDS

                else:

                    mouth_open_since = None

                if yawning and not yawn_was_active:
                    yawn_total += 1

                yawn_was_active = yawning

                cv2.polylines(
                    frame,
                    [mouth.astype(np.int32)],
                    True,
                    (0, 165, 255) if yawning else (255, 200, 0),
                    1
                )

                cv2.putText(
                    frame,
                    f"PERCLOS: {perclos_value * 100:.0f}%   "
                    f"MAR: {mar_value:.2f}   Yawns: {yawn_total}",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 165, 255) if (yawning or perclos_value >= PERCLOS_ALERT)
                    else (255, 255, 255),
                    2
                )

                # Draw eye outlines
                cv2.polylines(
                    frame,
                    [left_eye.astype(np.int32)],
                    True,
                    (0, 255, 0),
                    2
                )

                cv2.polylines(
                    frame,
                    [right_eye.astype(np.int32)],
                    True,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"EAR: {average_ear:.2f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

            # =========================================
            # NO FACE DETECTED
            # =========================================

            else:

                mouth_open_since = None
                yawn_was_active = False

                # IMPORTANT:
                # Reset closure tracking when face disappears.
                # This prevents false alerts after face returns.

                if tracker.closed_since is not None:

                    if face_lost_since is None:
                        face_lost_since = now

                    hold = (
                        ALERT_FACE_LOSS_HOLD
                        if previous_alert_state
                        else FACE_LOSS_GRACE
                    )

                    if now - face_lost_since <= hold:

                        # Head dropped / face lost while eyes were closed:
                        # keep counting instead of silently cancelling.
                        closure_duration = tracker.update(True, now)

                        alert_active = tracker.alert_active(
                            closure_duration
                        )

                        eyes_status = "CLOSED"

                    else:

                        tracker.reset()

                else:

                    face_lost_since = None

            # =========================================
            # UPDATE API STATUS
            # =========================================

            update_status(

                running=True,

                eyes=eyes_status,

                ear=(
                    round(float(average_ear), 3)
                    if average_ear is not None
                    else None
                ),

                closure_duration=round(
                    float(closure_duration), 2
                ),

                alert=bool(alert_active),

                perclos=round(float(perclos_value), 3),

                perclos_high=bool(perclos_value >= PERCLOS_ALERT),

                mar=(
                    round(float(mar_value), 3)
                    if mar_value is not None
                    else None
                ),

                yawning=bool(yawning),

                yawn_count=yawn_total,

                message="Detector is running"
            )

            # =========================================
            # TRIGGER SOUND ALERT ONCE
            # =========================================

            if alert_active and not previous_alert_state:

                with status_lock:
                    detector_status["alert_count"] += 1
                    detector_status["last_alert_at"] = time.time()

                ALERT_EVENTS.inc()

            # Alarm repeats while the alert is active; stops when it clears
            if alert_active:
                alarm.start()
            else:
                alarm.stop()

            previous_alert_state = alert_active

            # =========================================
            # DISPLAY STATUS
            # =========================================

            cv2.putText(
                frame,
                f"EYES: {eyes_status}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"CLOSED: {closure_duration:.1f}s",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            if alert_active:

                cv2.putText(
                    frame,
                    "DROWSINESS ALERT!",
                    (20, 170),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    3
                )

                cv2.putText(
                    frame,
                    "TAKE A BREAK",
                    (20, 210),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            # =========================================
            # DISPLAY WEBCAM WINDOW
            # =========================================

            # Share the annotated frame with the web frontend
            publish_frame(frame)

            if SHOW_WINDOW:

                try:

                    cv2.imshow(
                        "SPECTRA Drowsiness Detector",
                        frame
                    )

                    key = cv2.waitKey(1) & 0xFF

                    if key == ord("q") or key == 27:
                        break

                except cv2.error:

                    # Supports environments without GUI
                    time.sleep(0.01)

            else:

                time.sleep(0.005)

    finally:

        alarm.stop()

        clear_frame()

        # ---------------------------------------------
        # RELEASE CAMERA
        # ---------------------------------------------

        if camera is not None:

            camera.release()

        # ---------------------------------------------
        # CLOSE MEDIAPIPE
        # ---------------------------------------------

        if face_landmarker is not None:

            face_landmarker.close()

        # ---------------------------------------------
        # CLOSE WINDOWS
        # ---------------------------------------------

        try:

            cv2.destroyAllWindows()

        except cv2.error:

            pass

        # ---------------------------------------------
        # UPDATE STATUS
        # ---------------------------------------------

        update_status(
            running=False,
            alert=False,
            message="Detector is stopped"
        )

        print("Drowsiness detector stopped.")


# =========================================================
# BACKGROUND DETECTOR WORKER
# =========================================================

def detector_worker(**config):

    try:

        run(
            stop_signal=stop_event,
            **config
        )

    except Exception as exc:

        print(f"Detector error: {exc}")

        update_status(
            running=False,
            alert=False,
            message=f"Detector error: {exc}"
        )

    finally:

        with status_lock:

            detector_status["running"] = False


# =========================================================
# API: HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "api": "Spectra Drowsiness API",
        "status": "healthy"
    }


# =========================================================
# API: START DETECTOR
# =========================================================

@app.post("/start")
def start_detector(
    camera_index: int = Query(0, ge=0, le=10),
    eye_threshold: float = Query(0.21, gt=0.05, lt=0.5),
    closure_seconds: float = Query(2.0, gt=0.2, le=30),
):

    global detector_thread

    with detector_lock:

        if (
            detector_thread is not None
            and detector_thread.is_alive()
        ):

            return {
                "message": "Detector is already running",
                "status": get_status_snapshot()
            }

        stop_event.clear()

        update_status(
            running=True,
            eyes="UNKNOWN",
            ear=None,
            closure_duration=0.0,
            alert=False,
            message="Starting detector"
        )

        DETECTOR_RESTARTS.inc()

        detector_thread = threading.Thread(
            target=detector_worker,
            kwargs=dict(
                camera_index=camera_index,
                eye_threshold=eye_threshold,
                closure_seconds=closure_seconds,
            ),
            name="detector-worker",
            daemon=True
        )

        detector_thread.start()

    return {
        "message": "Detector start requested",
        "status": get_status_snapshot()
    }


# =========================================================
# API: STOP DETECTOR
# =========================================================

@app.post("/stop")
def stop_detector():

    with detector_lock:

        thread = detector_thread

        if thread is None or not thread.is_alive():

            update_status(
                running=False,
                alert=False,
                message="Detector is stopped"
            )

            return {
                "message": "Detector is already stopped",
                "running": False
            }

        stop_event.set()

    # Wait outside the lifecycle lock
    thread.join(timeout=5)

    still_running = thread.is_alive()

    return {
        "message": (
            "Stop requested; detector is finishing its current frame"
            if still_running
            else "Detector stopped"
        ),
        "running": still_running
    }


# =========================================================
# API: LIVE DETECTOR STATUS
# =========================================================

@app.get("/status")
def get_detector_status():

    snapshot = get_status_snapshot()

    update_detector_metrics(snapshot)

    snapshot["alarm_playing"] = alarm.is_playing()

    return snapshot


# =========================================================
# API: LIVE VIDEO FOR THE FRONTEND
# =========================================================
# Use in the frontend:  <img src="http://localhost:8001/video_feed" />

@app.get("/snapshot")
def snapshot():

    with frame_lock:
        jpeg = latest_jpeg

    if jpeg is None:
        return Response(
            content="No frame available. Start the detector first.",
            status_code=503
        )

    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"}
    )


@app.get("/video_feed")
async def video_feed(request: Request):

    async def frames():

        last_id = -1

        while True:

            if await request.is_disconnected():
                break

            with frame_lock:
                jpeg, frame_id = latest_jpeg, latest_frame_id

            if jpeg is not None and frame_id != last_id:

                last_id = frame_id

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg + b"\r\n"
                )

            await asyncio.sleep(0.03)

    return StreamingResponse(
        frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"}
    )


# =========================================================
# API: PROBE CAMERAS (diagnostics)
# =========================================================

@app.get("/camera/probe")
def probe_cameras():

    with detector_lock:

        if detector_thread is not None and detector_thread.is_alive():

            return {
                "message": "Detector is running and using the camera; "
                           "call POST /stop before probing."
            }

    found = []

    for index in range(4):

        try:

            cap = open_camera(index)
            ok, frame = cap.read()
            h, w = frame.shape[:2] if ok else (0, 0)
            cap.release()
            found.append({"index": index, "working": True, "resolution": f"{w}x{h}"})

        except Exception as exc:

            found.append({"index": index, "working": False, "error": str(exc)})

    return {"platform": sys.platform, "cameras": found}


# =========================================================
# API: TEST THE ALARM SOUND
# =========================================================

@app.post("/alarm/test")
def test_alarm(seconds: float = Query(2.0, gt=0.5, le=10)):

    alarm.start()

    threading.Timer(
        seconds,
        lambda: (
            None
            if get_status_snapshot().get("alert")
            else alarm.stop()
        )
    ).start()

    return {
        "message": f"Playing test alarm for {seconds:.1f}s on the server"
    }


# =========================================================
# STANDALONE ENTRY POINT
# =========================================================

if __name__ == "__main__":

    import uvicorn

    port = int(os.getenv("PORT", 8001))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )