import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./DriverSafety.css";

function DriverSafety() {
  const navigate = useNavigate();

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);

  // START CAMERA
  const startCamera = async () => {
    try {
      setCameraError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("Camera is not supported by this browser.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });

      streamRef.current = stream;
      setCameraOn(true);
    } catch (error) {
      console.error(error);
      setCameraError(
        "Camera permission denied or camera is not available."
      );
    }
  };

  // CONNECT CAMERA TO VIDEO
  useEffect(() => {
    if (cameraOn && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;

      videoRef.current.play().catch(() => {});
    }
  }, [cameraOn]);

  // STOP CAMERA
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOn(false);
  };

  // CLEANUP
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
        });
      }
    };
  }, []);

  // VIDEO UPLOAD
  const handleVideoUpload = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.type.startsWith("video/")) {
      alert("Please select a valid video file.");
      return;
    }

    const videoURL = URL.createObjectURL(file);

    setSelectedVideo(videoURL);
    setAnalysisDone(false);
  };

  // AI ANALYSIS DEMO
  const runAnalysis = () => {
    if (!selectedVideo) {
      alert("Please upload a driving video first.");
      return;
    }

    setAnalyzing(true);
    setAnalysisDone(false);

    setTimeout(() => {
      setAnalyzing(false);
      setAnalysisDone(true);
    }, 2000);
  };

  return (
    <div className="driver-page">

      {/* SIDEBAR */}
      <aside className="driver-sidebar">

        <div className="driver-logo">
          <div className="driver-logo-icon">S</div>

          <div>
            <h2>SPECTRA</h2>
            <span>AI SAFETY PLATFORM</span>
          </div>
        </div>

        <p className="sidebar-title">MAIN MENU</p>

        <div
          className="driver-menu"
          onClick={() => navigate("/dashboard")}
        >
          <span>⌂</span>
          Dashboard
        </div>

        <div className="driver-menu selected">
          <span>🚗</span>
          Driver Safety
        </div>

        <div
          className="driver-menu"
          onClick={() => navigate("/fraud-detection")}
        >
          <span>💳</span>
          Fraud Detection
        </div>

        <div className="driver-menu">
          <span>📊</span>
          Analytics
        </div>

        <p className="sidebar-title">SYSTEM</p>

        <div className="driver-menu">
          <span>👤</span>
          Profile
        </div>

        <div className="driver-menu">
          <span>⚙️</span>
          Settings
        </div>

        <div
          className="driver-menu logout"
          onClick={() => navigate("/login")}
        >
          <span>↪</span>
          Logout
        </div>

      </aside>

      {/* MAIN CONTENT */}
      <main className="driver-main">

        {/* HEADER */}
        <header className="driver-header">

          <div>
            <h1>Driver Safety</h1>

            <p>
              Monitor driver behavior using SPECTRA AI
              vision technology.
            </p>
          </div>

          <div className="driver-profile">

            <div className="driver-avatar">
              Y
            </div>

            <div>
              <strong>Yogesh</strong>
              <small>Administrator</small>
            </div>

          </div>

        </header>

        {/* DRIVER STATUS */}
        <section className="driver-status-card">

          <div className="status-info">

            <div className="safe-circle">
              ✓
            </div>

            <div>
              <span>DRIVER STATUS</span>

              <h2>
                {analysisDone
                  ? "Safe"
                  : cameraOn
                  ? "Monitoring"
                  : "Ready"}
              </h2>

              <p>
                {analysisDone
                  ? "No dangerous behavior detected."
                  : cameraOn
                  ? "Live camera monitoring is active."
                  : "Start camera or upload a video to begin."}
              </p>
            </div>

          </div>

          <div className="score">
            <span>SAFETY SCORE</span>

            <strong>
              {analysisDone ? "98%" : "--"}
            </strong>
          </div>

        </section>

        {/* CAMERA + UPLOAD */}
        <section className="driver-tools">

          {/* CAMERA CARD */}
          <div className="tool-card">

            <div className="tool-icon">
              📷
            </div>

            <h3>Live Camera</h3>

            <p>
              Monitor driver behavior through your device
              camera.
            </p>

            {!cameraOn ? (
              <button
                className="primary-btn"
                onClick={startCamera}
              >
                Start Camera
              </button>
            ) : (
              <button
                className="stop-btn"
                onClick={stopCamera}
              >
                Stop Camera
              </button>
            )}

            {cameraError && (
              <div className="camera-error">
                ⚠️ {cameraError}
              </div>
            )}

            {cameraOn && (
              <div className="camera-preview">

                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                />

                <div className="camera-live">
                  <span className="camera-dot"></span>
                  LIVE
                </div>

              </div>
            )}

          </div>

          {/* VIDEO UPLOAD CARD */}
          <div className="tool-card">

            <div className="tool-icon">
              📤
            </div>

            <h3>Video Upload</h3>

            <p>
              Upload a driving video for AI safety analysis.
            </p>

            <label className="upload-button">

              Choose Video

              <input
                type="file"
                accept="video/*"
                onChange={handleVideoUpload}
              />

            </label>

            {selectedVideo && (
              <div className="upload-success">
                ✓ Video selected successfully
              </div>
            )}

          </div>

        </section>

        {/* AI ANALYSIS */}
        <section className="analysis-card">

          <div className="analysis-heading">

            <div>
              <h2>AI Safety Analysis</h2>

              <p>
                Analyze driving footage for safety
                violations.
              </p>
            </div>

            <span className="ai-ready">
              ● AI READY
            </span>

          </div>

          <div className="analysis-area">

            {/* VIDEO */}
            <div className="video-box">

              {selectedVideo ? (
                <video
                  src={selectedVideo}
                  controls
                  className="uploaded-video"
                />
              ) : (
                <>
                  <div className="video-play">
                    ▶
                  </div>

                  <p>
                    Upload a driving video to preview it here.
                  </p>
                </>
              )}

            </div>

            {/* RESULTS */}
            <div className="analysis-results">

              <div className="result-row">
                <span>😴 Drowsiness</span>

                <strong className="safe">
                  {analysisDone ? "LOW" : "--"}
                </strong>
              </div>

              <div className="result-row">
                <span>📱 Distraction</span>

                <strong className="safe">
                  {analysisDone ? "LOW" : "--"}
                </strong>
              </div>

              <div className="result-row">
                <span>🪢 Seatbelt</span>

                <strong className="safe">
                  {analysisDone ? "DETECTED" : "--"}
                </strong>
              </div>

              <div className="result-row">
                <span>🚗 Dangerous Driving</span>

                <strong className="safe">
                  {analysisDone ? "NONE" : "--"}
                </strong>
              </div>

              <button
                className="analyze-button"
                onClick={runAnalysis}
                disabled={analyzing}
              >
                {analyzing
                  ? "AI Analyzing..."
                  : "Run AI Analysis"}
              </button>

            </div>

          </div>

          {analyzing && (
            <div className="analyzing-message">
              🤖 SPECTRA AI is analyzing the driving video...
            </div>
          )}

          {analysisDone && (
            <div className="analysis-success">
              ✓ AI analysis completed successfully.
            </div>
          )}

        </section>

        {/* ALERT HISTORY */}
        <section className="alert-section">

          <div className="section-heading">

            <h2>Alert History</h2>

            <p>
              Recent driver safety events.
            </p>

          </div>

          <div className="alert-table">

            <div className="alert-head">
              <span>ALERT</span>
              <span>RISK</span>
              <span>TIME</span>
              <span>STATUS</span>
            </div>

            <div className="alert-row">

              <span>
                😴 Drowsiness detected
              </span>

              <span className="high">
                HIGH
              </span>

              <span>
                10:42 AM
              </span>

              <span>
                Reviewed
              </span>

            </div>

            <div className="alert-row">

              <span>
                📱 Driver distraction
              </span>

              <span className="medium">
                MEDIUM
              </span>

              <span>
                10:15 AM
              </span>

              <span>
                Resolved
              </span>

            </div>

            <div className="alert-row">

              <span>
                ✓ Safe driving detected
              </span>

              <span className="low">
                LOW
              </span>

              <span>
                09:45 AM
              </span>

              <span>
                Normal
              </span>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default DriverSafety;