import { useNavigate } from "react-router-dom";
import "./Analytics.css";

function Analytics() {
  const navigate = useNavigate();

  return (
    <div className="analytics-page">

      {/* SIDEBAR */}
      <aside className="analytics-sidebar">

        <div className="analytics-logo">
          <div className="analytics-logo-box">S</div>

          <div>
            <h2>SPECTRA</h2>
            <span>AI SAFETY PLATFORM</span>
          </div>
        </div>

        <p className="analytics-menu-title">MAIN MENU</p>

        <div
          className="analytics-menu"
          onClick={() => navigate("/dashboard")}
        >
          <span>⌂</span>
          Dashboard
        </div>

        <div
          className="analytics-menu"
          onClick={() => navigate("/driver-safety")}
        >
          <span>🚗</span>
          Driver Safety
        </div>

        <div
          className="analytics-menu"
          onClick={() => navigate("/fraud-detection")}
        >
          <span>💳</span>
          Fraud Detection
        </div>

        <div className="analytics-menu active">
          <span>📊</span>
          Analytics
        </div>

        <p className="analytics-menu-title">SYSTEM</p>

        <div className="analytics-menu">
          <span>👤</span>
          Profile
        </div>

        <div className="analytics-menu">
          <span>⚙️</span>
          Settings
        </div>

        <div
          className="analytics-menu logout"
          onClick={() => navigate("/login")}
        >
          <span>↪</span>
          Logout
        </div>

      </aside>

      {/* MAIN */}
      <main className="analytics-main">

        {/* HEADER */}
        <header className="analytics-header">

          <div>
            <h1>Analytics</h1>

            <p>
              Monitor SPECTRA AI safety and fraud detection performance.
            </p>
          </div>

          <div className="analytics-user">

            <div className="analytics-avatar">
              Y
            </div>

            <div>
              <strong>Yogesh</strong>
              <small>Administrator</small>
            </div>

          </div>

        </header>

        {/* STATISTICS */}
        <section className="analytics-stats">

          <div className="analytics-stat-card">

            <div className="analytics-stat-icon blue">
              🚗
            </div>

            <div>
              <span>DRIVER SAFETY SCORE</span>
              <h3>98%</h3>
              <p>+4.2% this month</p>
            </div>

          </div>

          <div className="analytics-stat-card">

            <div className="analytics-stat-icon purple">
              💳
            </div>

            <div>
              <span>FRAUD CHECKS</span>
              <h3>156</h3>
              <p>+18 this week</p>
            </div>

          </div>

          <div className="analytics-stat-card">

            <div className="analytics-stat-icon red">
              ⚠️
            </div>

            <div>
              <span>THREATS DETECTED</span>
              <h3>24</h3>
              <p>8 high risk</p>
            </div>

          </div>

          <div className="analytics-stat-card">

            <div className="analytics-stat-icon green">
              🛡️
            </div>

            <div>
              <span>THREATS BLOCKED</span>
              <h3>92%</h3>
              <p>Protection rate</p>
            </div>

          </div>

        </section>

        {/* CHARTS */}
        <section className="analytics-grid">

          {/* SAFETY CHART */}
          <div className="analytics-card">

            <div className="analytics-card-header">

              <div>
                <h2>Safety Performance</h2>
                <p>Driver safety score over the week</p>
              </div>

              <span className="chart-badge">
                THIS WEEK
              </span>

            </div>

            <div className="bar-chart">

              <div className="bar-column">
                <span>92%</span>
                <div className="bar bar-1"></div>
                <small>Mon</small>
              </div>

              <div className="bar-column">
                <span>95%</span>
                <div className="bar bar-2"></div>
                <small>Tue</small>
              </div>

              <div className="bar-column">
                <span>91%</span>
                <div className="bar bar-3"></div>
                <small>Wed</small>
              </div>

              <div className="bar-column">
                <span>96%</span>
                <div className="bar bar-4"></div>
                <small>Thu</small>
              </div>

              <div className="bar-column">
                <span>94%</span>
                <div className="bar bar-5"></div>
                <small>Fri</small>
              </div>

              <div className="bar-column">
                <span>98%</span>
                <div className="bar bar-6"></div>
                <small>Sat</small>
              </div>

              <div className="bar-column">
                <span>98%</span>
                <div className="bar bar-7"></div>
                <small>Sun</small>
              </div>

            </div>

          </div>


          {/* FRAUD OVERVIEW */}
          <div className="analytics-card">

            <div className="analytics-card-header">

              <div>
                <h2>Fraud Overview</h2>
                <p>Transaction risk distribution</p>
              </div>

              <span className="chart-badge">
                156 TOTAL
              </span>

            </div>

            <div className="fraud-overview">

              <div className="donut">
                <div className="donut-inner">
                  <strong>156</strong>
                  <span>Checks</span>
                </div>
              </div>

              <div className="risk-legend">

                <div>
                  <span className="legend-dot safe"></span>
                  <span>Safe</span>
                  <strong>148</strong>
                </div>

                <div>
                  <span className="legend-dot review"></span>
                  <span>Review</span>
                  <strong>6</strong>
                </div>

                <div>
                  <span className="legend-dot danger"></span>
                  <span>Fraud</span>
                  <strong>2</strong>
                </div>

              </div>

            </div>

          </div>

        </section>


        {/* ALERTS + ACTIVITY */}
        <section className="analytics-bottom-grid">

          {/* ALERT SUMMARY */}
          <div className="analytics-card">

            <div className="analytics-card-header">

              <div>
                <h2>Safety Alerts</h2>
                <p>Detected safety violations</p>
              </div>

            </div>

            <div className="alert-list">

              <div className="alert-row">
                <span className="alert-icon red-icon">!</span>

                <div>
                  <strong>Drowsiness</strong>
                  <small>8 alerts</small>
                </div>

                <b>HIGH</b>
              </div>

              <div className="alert-row">
                <span className="alert-icon orange-icon">!</span>

                <div>
                  <strong>Distraction</strong>
                  <small>5 alerts</small>
                </div>

                <b>MEDIUM</b>
              </div>

              <div className="alert-row">
                <span className="alert-icon yellow-icon">!</span>

                <div>
                  <strong>Seatbelt</strong>
                  <small>3 alerts</small>
                </div>

                <b>LOW</b>
              </div>

            </div>

          </div>


          {/* SYSTEM PERFORMANCE */}
          <div className="analytics-card">

            <div className="analytics-card-header">

              <div>
                <h2>System Performance</h2>
                <p>SPECTRA AI platform statistics</p>
              </div>

            </div>

            <div className="performance-item">

              <div>
                <span>AI Detection Accuracy</span>
                <strong>96%</strong>
              </div>

              <div className="progress">
                <div className="progress-fill accuracy"></div>
              </div>

            </div>

            <div className="performance-item">

              <div>
                <span>Threat Response</span>
                <strong>91%</strong>
              </div>

              <div className="progress">
                <div className="progress-fill response"></div>
              </div>

            </div>

            <div className="performance-item">

              <div>
                <span>Platform Reliability</span>
                <strong>99%</strong>
              </div>

              <div className="progress">
                <div className="progress-fill reliability"></div>
              </div>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Analytics;