import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

function Login() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();

    const email = e.target.email.value.trim();
    const password = e.target.password.value;

    setMessage("");

    // Email validation
    if (!email) {
      setMessage("Please enter your email address.");
      return;
    }

    // Password validation
    if (!password) {
      setMessage("Please enter your password.");
      return;
    }

    if (password.length < 6) {
      setMessage("Password must be at least 6 characters.");
      return;
    }

    // Loading effect
    setIsLoading(true);

    // Frontend demo login
    setTimeout(() => {
      const loginData = {
        email: email,
        loggedIn: true,
      };

      // Save login information
      if (rememberMe) {
        localStorage.setItem(
          "spectraUser",
          JSON.stringify(loginData)
        );
      } else {
        sessionStorage.setItem(
          "spectraUser",
          JSON.stringify(loginData)
        );
      }

      // Go to Dashboard
      navigate("/dashboard");

      setIsLoading(false);
    }, 800);
  };

  const handleForgotPassword = () => {
    setMessage(
      "Password reset feature will be available soon."
    );
  };

  const handleCreateAccount = () => {
    navigate("/register");
  };

  return (
    <div className="login-page">

      <div className="login-container">

        {/* ================= LEFT SECTION ================= */}

        <div className="login-left">

          <div className="login-brand">
            SPECTRA<span> AI</span>
          </div>

          <div className="login-message">

            <p className="login-tagline">
              MULTIMODAL AI SAFETY PLATFORM
            </p>

            <h1>
              Welcome back to
              <br />
              <span>SPECTRA AI</span>
            </h1>

            <p>
              Intelligent safety starts here. Sign in to access
              AI-powered driver safety and fraud detection.
            </p>

          </div>

          <div className="security-info">
            <span>●</span>
            Secure AI-Powered Platform
          </div>

        </div>


        {/* ================= RIGHT SECTION ================= */}

        <div className="login-right">

          <div className="login-box">

            {/* Heading */}

            <div className="login-heading">

              <h2>
                Sign In
              </h2>

              <p>
                Enter your credentials to continue
              </p>

            </div>


            {/* Login Form */}

            <form onSubmit={handleLogin}>

              {/* EMAIL */}

              <div className="input-group">

                <label htmlFor="email">
                  Email Address
                </label>

                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="Enter your email"
                  autoComplete="email"
                  required
                />

              </div>


              {/* PASSWORD */}

              <div className="input-group">

                <div className="password-label">

                  <label htmlFor="password">
                    Password
                  </label>

                  <button
                    type="button"
                    className="forgot-btn"
                    onClick={handleForgotPassword}
                  >
                    Forgot Password?
                  </button>

                </div>


                <div className="password-input">

                  <input
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    id="password"
                    name="password"
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    required
                  />

                  <button
                    type="button"
                    className="show-password"
                    onClick={() =>
                      setShowPassword(!showPassword)
                    }
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>

                </div>

              </div>


              {/* REMEMBER ME */}

              <div className="remember-row">

                <label>

                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) =>
                      setRememberMe(e.target.checked)
                    }
                  />

                  Remember me

                </label>

              </div>


              {/* MESSAGE */}

              {message && (
                <div className="login-message-box">
                  {message}
                </div>
              )}


              {/* SIGN IN */}

              <button
                type="submit"
                className="login-submit"
                disabled={isLoading}
              >

                {isLoading
                  ? "Signing In..."
                  : "Sign In"}

              </button>

            </form>


            {/* DIVIDER */}

            <div className="divider">
              <span>OR</span>
            </div>


            {/* CREATE ACCOUNT */}

            <div className="create-account">

              <p>

                Don't have an account?

                <button
                  type="button"
                  onClick={handleCreateAccount}
                >
                  Create Account
                </button>

              </p>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Login;