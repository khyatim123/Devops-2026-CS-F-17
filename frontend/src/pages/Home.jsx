import { useNavigate } from "react-router-dom";
import "./Home.css";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-page">

      {/* ================= NAVBAR ================= */}
      <nav className="navbar">

        <div className="logo">
          SPECTRA<span> AI</span>
        </div>

        <div className="nav-links">

          <a href="#home">Home</a>

          <a href="#features">Features</a>

          <a href="#about">About</a>

          <button
            className="login-btn"
            onClick={() => navigate("/login")}
          >
            Login
          </button>

        </div>

      </nav>


      {/* ================= HERO SECTION ================= */}
      <section className="hero" id="home">

        <div className="hero-content">

          <p className="tagline">
            MULTIMODAL AI SAFETY PLATFORM
          </p>

          <h1>
            Smarter Safety.
            <br />
            <span>Powered by AI.</span>
          </h1>

          <p className="hero-text">
            SPECTRA uses Artificial Intelligence to detect road safety
            violations and identify suspicious online transactions.
          </p>


          <div className="hero-buttons">

            <button
              className="primary-btn"
              onClick={() => navigate("/register")}
            >
              Get Started
            </button>

            <button
              className="secondary-btn"
              onClick={() =>
                document
                  .getElementById("features")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Explore SPECTRA
            </button>

          </div>

        </div>


        {/* ================= AI SYSTEM CARD ================= */}
        <div className="hero-card">

          <div className="card-header">

            <span className="status-dot"></span>

            SPECTRA AI SYSTEM

          </div>


          <div className="scan-box">

            <div className="scan-line"></div>

            <div className="scan-text">
              AI ANALYSIS ACTIVE
            </div>

          </div>


          <div className="detection">

            <div>

              <small>
                ROAD SAFETY
              </small>

              <strong>
                Monitoring
              </strong>

            </div>


            <div>

              <small>
                FRAUD DETECTION
              </small>

              <strong>
                Protected
              </strong>

            </div>

          </div>

        </div>

      </section>


      {/* ================= FEATURES SECTION ================= */}
      <section className="features" id="features">

        <h2>
          One Platform. Two Powerful AI Solutions.
        </h2>


        <div className="feature-grid">


          {/* DRIVER SAFETY */}
          <div className="feature-card">

            <div className="feature-icon">
              🚗
            </div>

            <h3>
              Driver Safety
            </h3>

            <p>
              Detect dangerous driving behaviour, drowsiness and
              road safety violations using AI-powered vision
              technology.
            </p>

          </div>


          {/* FRAUD DETECTION */}
          <div className="feature-card">

            <div className="feature-icon">
              🛡️
            </div>

            <h3>
              Fraud Detection
            </h3>

            <p>
              Analyze transactions and identify suspicious
              activities using intelligent fraud detection
              and risk scoring.
            </p>

          </div>


        </div>

      </section>


      {/* ================= ABOUT SECTION ================= */}
      <section className="about" id="about">

        <h2>
          Why SPECTRA?
        </h2>

        <p>
          SPECTRA brings multiple AI safety technologies together
          into a single intelligent platform designed for
          real-world protection.
        </p>

      </section>


      {/* ================= FOOTER ================= */}
      <footer>

        <p>
          © 2026 SPECTRA AI. Intelligent Safety Platform.
        </p>

      </footer>

    </div>
  );
}

export default Home;