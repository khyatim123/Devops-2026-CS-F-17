import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page">

      {/* ================= SIDEBAR ================= */}
      <aside className="dashboard-sidebar">

        <div className="dashboard-logo">
          <div className="logo-box">S</div>

          <div>
            <h2>SPECTRA</h2>
            <span>AI SAFETY PLATFORM</span>
          </div>
        </div>

        <p className="menu-title">MAIN MENU</p>

        <div className="side-menu active">
          <span>⌂</span>
          Dashboard
        </div>

        <div
          className="side-menu"
          onClick={() => navigate("/driver-safety")}
        >
          <span>🚗</span>
          Driver Safety
        </div>

        <div className="side-menu">
          <span>💳</span>
          Fraud Detection
        </div>
<div
  className="side-menu"
  onClick={() => navigate("/analytics")}
>
  <span>📊</span>
  Analytics
</div>

        <p className="menu-title">SYSTEM</p>

        <div className="side-menu">
          <span>👤</span>
          Profile
        </div>

        <div className="side-menu">
          <span>⚙️</span>
          Settings
        </div>

        <div
          className="side-menu logout"
          onClick={() => navigate("/login")}
        >
          <span>↪</span>
          Logout
        </div>

      </aside>

      {/* ================= MAIN ================= */}
      <main className="dashboard-main">

        {/* HEADER */}
        <header className="dashboard-header">

          <div>
            <h1>Dashboard</h1>

            <p>
              Welcome back to SPECTRA AI Safety Platform.
            </p>
          </div>

          <div className="user-profile">

            <div className="user-avatar">
              Y
            </div>

            <div>
              <strong>Yogesh</strong>
              <small>Administrator</small>
            </div>

          </div>

        </header>

        {/* ================= WELCOME ================= */}
        <section className="welcome-card">

          <div>
            <span className="welcome-label">
              SPECTRA AI
            </span>

            <h2>
              Intelligent Safety Starts Here
            </h2>

            <p>
              Monitor road safety and detect online fraud
              using multimodal artificial intelligence.
            </p>
          </div>

          <div className="welcome-icon">
            🛡️
          </div>

        </section>

        {/* ================= STATISTICS ================= */}
        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-icon blue">
              🚗
            </div>

            <div>
              <span>DRIVER SAFETY</span>
              <h3>98%</h3>
              <p>Safety Score</p>
            </div>

          </div>

          <div className="stat-card">

            <div className="stat-icon red">
              ⚠️
            </div>

            <div>
              <span>SAFETY ALERTS</span>
              <h3>12</h3>
              <p>This Week</p>
            </div>

          </div>

          <div className="stat-card">

            <div className="stat-icon purple">
              💳
            </div>

            <div>
              <span>FRAUD CHECKS</span>
              <h3>156</h3>
              <p>Transactions</p>
            </div>

          </div>

          <div className="stat-card">

            <div className="stat-icon green">
              🛡️
            </div>

            <div>
              <span>THREATS BLOCKED</span>
              <h3>24</h3>
              <p>This Month</p>
            </div>

          </div>

        </section>

        {/* ================= MODULES ================= */}
        <section className="modules-section">

          <div className="section-header">

            <div>
              <h2>Safety Modules</h2>

              <p>
                Choose an AI-powered safety module.
              </p>
            </div>

          </div>

          <div className="modules-grid">

            {/* DRIVER SAFETY */}
            <div className="module-card">

              <div className="module-top">

                <div className="module-icon driver">
                  🚗
                </div>

                <span className="module-status">
                  ACTIVE
                </span>

              </div>

              <h3>Driver Safety</h3>

              <p>
                Detect drowsiness, distraction, seatbelt
                violations and dangerous driving behavior.
              </p>

              <button
                onClick={() =>
                  navigate("/driver-safety")
                }
              >
                Open Driver Safety →
              </button>

            </div>

            {/* FRAUD DETECTION */}
            <div className="module-card">

              <div className="module-top">

                <div className="module-icon fraud">
                  💳
                </div>

                <span className="module-status">
                  ACTIVE
                </span>

              </div>

              <h3>Fraud Detection</h3>

              <p>
                Analyze transactions and identify suspicious
                online financial activities.
              </p>

            <button onClick={() => navigate("/fraud-detection")}>
              Open Fraud Detection →
</button>
            </div>

          </div>

        </section>

        {/* ================= RECENT ACTIVITY ================= */}
        <section className="activity-section">

          <div className="section-header">

            <div>
              <h2>Recent Activity</h2>

              <p>
                Latest SPECTRA AI system events.
              </p>
            </div>

            <button className="view-all">
              View All
            </button>

          </div>

          <div className="activity-list">

            <div className="activity-item">

              <div className="activity-icon green">
                ✓
              </div>

              <div className="activity-text">

                <strong>
                  Safe driving session completed
                </strong>

                <span>
                  Driver Safety • 10 minutes ago
                </span>

              </div>

              <span className="activity-safe">
                SAFE
              </span>

            </div>

            <div className="activity-item">

              <div className="activity-icon red">
                !
              </div>

              <div className="activity-text">

                <strong>
                  Drowsiness alert detected
                </strong>

                <span>
                  Driver Safety • 35 minutes ago
                </span>

              </div>

              <span className="activity-danger">
                HIGH
              </span>

            </div>

            <div className="activity-item">

              <div className="activity-icon purple">
                $
              </div>

              <div className="activity-text">

                <strong>
                  Transaction analysis completed
                </strong>

                <span>
                  Fraud Detection • 1 hour ago
                </span>

              </div>

              <span className="activity-safe">
                SAFE
              </span>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;