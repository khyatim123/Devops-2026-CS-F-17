import { useState } from "react";
import "./CreateAccount.css";

function CreateAccount() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleRegister = (e) => {
    e.preventDefault();

    const form = e.target;

    const password = form.password.value;
    const confirmPassword = form.confirmPassword.value;

    if (password !== confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    alert("Account created successfully!");
  };

  return (
    <div className="register-page">
      <div className="register-container">

        {/* Left Section */}
        <div className="register-left">
          <div className="register-brand">
            SPECTRA<span> AI</span>
          </div>

          <div className="register-content">
            <p className="register-tagline">
              MULTIMODAL AI SAFETY PLATFORM
            </p>

            <h1>
              Join the future of
              <br />
              <span>Intelligent Safety.</span>
            </h1>

            <p>
              Create your SPECTRA AI account and get access to
              intelligent driver safety and fraud detection solutions.
            </p>

            <div className="register-features">
              <div>
                <span>✓</span>
                AI-powered Driver Safety
              </div>

              <div>
                <span>✓</span>
                Intelligent Fraud Detection
              </div>

              <div>
                <span>✓</span>
                Real-time Safety Monitoring
              </div>
            </div>
          </div>

          <div className="register-security">
            <span>●</span>
            Your data is protected by SPECTRA AI
          </div>
        </div>

        {/* Right Section */}
        <div className="register-right">
          <div className="register-box">

            <div className="register-heading">
              <h2>Create Account</h2>
              <p>Fill in the details to create your account</p>
            </div>

            <form onSubmit={handleRegister}>

              {/* Name */}
              <div className="name-row">

                <div className="input-group">
                  <label htmlFor="firstName">First Name</label>

                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    placeholder="First name"
                    required
                  />
                </div>

                <div className="input-group">
                  <label htmlFor="lastName">Last Name</label>

                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    placeholder="Last name"
                    required
                  />
                </div>

              </div>

              {/* Email */}
              <div className="input-group">
                <label htmlFor="email">Email Address</label>

                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="Enter your email"
                  required
                />
              </div>

              {/* Phone */}
              <div className="input-group">
                <label htmlFor="phone">Phone Number</label>

                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  placeholder="Enter phone number"
                  required
                />
              </div>

              {/* Role */}
              <div className="input-group">
                <label htmlFor="role">Account Type</label>

                <select id="role" name="role" required>
                  <option value="">Select account type</option>
                  <option value="user">User</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              {/* Password */}
              <div className="input-group">
                <label htmlFor="password">Password</label>

                <div className="register-password">
                  <input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    name="password"
                    placeholder="Create password"
                    required
                    minLength="6"
                  />

                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div className="input-group">
                <label htmlFor="confirmPassword">
                  Confirm Password
                </label>

                <div className="register-password">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="Confirm password"
                    required
                    minLength="6"
                  />

                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() =>
                      setShowConfirmPassword(!showConfirmPassword)
                    }
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* Terms */}
              <div className="terms-row">
                <label>
                  <input type="checkbox" required />
                  <span>
                    I agree to the Terms & Conditions and Privacy Policy.
                  </span>
                </label>
              </div>

              {/* Submit */}
              <button type="submit" className="register-submit">
                Create Account
              </button>

            </form>

            <div className="register-divider">
              <span>OR</span>
            </div>

            <div className="login-link">
              <p>
                Already have an account?
                <button
                  type="button"
                  onClick={() =>
                    (window.location.href = "/login")
                  }
                >
                  Sign In
                </button>
              </p>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

export default CreateAccount;