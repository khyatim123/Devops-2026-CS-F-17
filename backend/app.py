import sys
import time
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Ensure backend directory is in sys.path so metrics import works from anywhere
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import cv2
import mediapipe as mp
import numpy as np

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from metrics import (
    HTTP_REQUESTS,
    HTTP_LATENCY,
    DETECTOR_RESTARTS,
    update_detector_metrics,
)


# =========================================================
# FASTAPI APPLICATION AND SHARED STATE
# =========================================================

app = FastAPI(
    title="Spectra Drowsiness Detection API",
    description="Webcam-based drowsiness detection backend",
    version="1.0.0"
)

# Enable CORS for frontend and monitoring dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# PROMETHEUS METRICS ENDPOINT
# =========================================================

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# =========================================================
# HTTP INSTRUMENTATION MIDDLEWARE
# =========================================================

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    handler = request.url.path
    if handler in ("/metrics", "/metrics/"):
        snapshot = get_status_snapshot()
        update_detector_metrics(snapshot)
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start
    HTTP_REQUESTS.labels(
        method=request.method,
        handler=handler,
        status_code=str(response.status_code),
    ).inc()
    HTTP_LATENCY.labels(handler=handler).observe(duration)
    return response


stop_event = threading.Event()
status_lock = threading.Lock()
detector_thread = None

detector_status = {
    "running": False,
    "eyes": "UNKNOWN",
    "ear": None,
    "closure_duration": 0.0,
    "alert": False,
    "message": "Detector is stopped"
}


def update_status(**kwargs):
    """Safely update shared detector status."""
    with status_lock:
        detector_status.update(kwargs)


def get_status_snapshot():
    """Return a copy of the current detector status."""
    with status_lock:
        return detector_status.copy()


# =========================================================
# EYE LANDMARK INDEXES
# =========================================================

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)


# =========================================================
# CALCULATE EYE ASPECT RATIO (EAR)
# =========================================================

def eye_aspect_ratio(eye_points):
    p0, p1, p2, p3, p4, p5 = eye_points

    vertical_one = np.linalg.norm(p1 - p5)
    vertical_two = np.linalg.norm(p2 - p4)
    horizontal = np.linalg.norm(p0 - p3)

    if horizontal == 0:
        return 0.0

    return (vertical_one + vertical_two) / (2.0 * horizontal)


# =========================================================
# CONVERT LANDMARKS TO PIXEL COORDINATES
# =========================================================

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
# TRACK EYE CLOSURE DURATION
# =========================================================

@dataclass
class ClosureTracker:
    threshold_seconds: float = 2.0
    closed_since: float | None = None

    def update(self, eyes_closed, now=None):
        if now is None:
            now = time.monotonic()

        if not eyes_closed:
            self.closed_since = None
            return 0.0

        if self.closed_since is None:
            self.closed_since = now
            return 0.0

        return now - self.closed_since

    def alert_active(self, closure_duration):
        return closure_duration >= self.threshold_seconds


# =========================================================
# PLAY DROWSINESS ALERT
# =========================================================

def play_alert():
    try:
        import winsound
        winsound.Beep(1000, 350)
    except Exception:
        print("ALERT: prolonged eye closure detected")


# =========================================================
# ENSURE MEDIAPIPE MODEL EXISTS
# =========================================================

def ensure_model(model_path):
    if model_path.exists():
        return

    print("Downloading MediaPipe face landmarker model...")

    model_url = (
        "https://storage.googleapis.com/"
        "mediapipe-models/face_landmarker/"
        "face_landmarker/float16/1/"
        "face_landmarker.task"
    )

    urllib.request.urlretrieve(model_url, str(model_path))

    print("Model downloaded successfully.")


# =========================================================
# MAIN DROWSINESS DETECTOR
# =========================================================

def run(
    camera_index=0,
    eye_threshold=0.21,
    closure_seconds=2.0,
    stop_signal=None
):
    if stop_signal is None:
        stop_signal = threading.Event()

    camera = None
    face_landmarker = None
    previous_alert_state = False

    try:
        # Open webcam
        camera = cv2.VideoCapture(camera_index)

        if not camera.isOpened():
            raise RuntimeError("Could not open webcam.")

        print("Webcam opened successfully.")
        print("Starting Spectra Drowsiness Detector...")
        print("Press Q or Esc to quit.")

        # Load model
        model_path = Path(__file__).with_name(
            "face_landmarker.task"
        )

        ensure_model(model_path)

        # Configure MediaPipe
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

        tracker = ClosureTracker(
            threshold_seconds=closure_seconds
        )

        update_status(
            running=True,
            eyes="NO FACE",
            ear=None,
            closure_duration=0.0,
            alert=False,
            message="Detector is running"
        )

        # -----------------------------------------------------
        # DETECTION LOOP
        # -----------------------------------------------------

        while not stop_signal.is_set():

            success, frame = camera.read()

            if not success:
                raise RuntimeError(
                    "Could not read frame from webcam."
                )

            frame_height, frame_width = frame.shape[:2]

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame
            )

            timestamp_ms = int(time.monotonic() * 1000)

            result = face_landmarker.detect_for_video(
                mp_image,
                timestamp_ms
            )

            eyes_status = "NO FACE"
            average_ear = None
            closure_duration = 0.0
            alert_active = False

            # -------------------------------------------------
            # PROCESS FACE LANDMARKS
            # -------------------------------------------------

            if result.face_landmarks:

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

                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)

                average_ear = (left_ear + right_ear) / 2.0

                eyes_closed = average_ear < eye_threshold

                closure_duration = tracker.update(
                    eyes_closed
                )

                alert_active = tracker.alert_active(
                    closure_duration
                )

                eyes_status = (
                    "CLOSED" if eyes_closed else "OPEN"
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

            # -------------------------------------------------
            # UPDATE API STATUS
            # -------------------------------------------------

            update_status(
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
                message="Detector is running"
            )

            # Beep once when an alert first activates
            if alert_active and not previous_alert_state:
                play_alert()

            previous_alert_state = alert_active

            # -------------------------------------------------
            # DISPLAY DETECTION STATUS
            # -------------------------------------------------

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

            try:
                cv2.imshow(
                    "SPECTRA Drowsiness Detector",
                    frame
                )

                # Q or Esc also stops standalone detection
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    break
            except cv2.error:
                # Headless / GUI unavailable environment
                time.sleep(0.01)

    finally:
        if camera is not None:
            camera.release()

        if face_landmarker is not None:
            face_landmarker.close()

        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass

        update_status(
            running=False,
            alert=False,
            message="Detector is stopped"
        )

        print("Drowsiness detector stopped.")


# =========================================================
# BACKGROUND THREAD
# =========================================================

def detector_worker():
    try:
        run(stop_signal=stop_event)

    except Exception as exc:
        print(f"Detector error: {exc}")

        update_status(
            running=False,
            message=f"Detector error: {exc}"
        )

    finally:
        # Ensure status reflects the actual thread state
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
# API: START DETECTION
# =========================================================

@app.post("/start")
def start_detector():
    global detector_thread

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
        name="detector-worker",
        daemon=True
    )

    detector_thread.start()

    return {
        "message": "Detector start requested",
        "status": "starting"
    }


# =========================================================
# API: STOP DETECTION
# =========================================================

@app.post("/stop")
def stop_detector():
    if (
        detector_thread is None
        or not detector_thread.is_alive()
    ):
        return {
            "message": "Detector is already stopped",
            "running": False
        }

    stop_event.set()

    detector_thread.join(timeout=5)

    still_running = detector_thread.is_alive()

    return {
        "message": (
            "Stop requested; detector is finishing its current frame"
            if still_running
            else "Detector stopped"
        ),
        "running": still_running
    }


# =========================================================
# API: GET LIVE STATUS
# =========================================================

@app.get("/status")
def get_detector_status():
    snapshot = get_status_snapshot()
    update_detector_metrics(snapshot)
    return snapshot


# =========================================================
# STANDALONE ENTRY POINT
# =========================================================

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
