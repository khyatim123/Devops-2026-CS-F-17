import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./FraudDetection.css";

function FraudDetection() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    amount: "",
    type: "",
    merchant: "",
    location: "",
    device: "",
  });

  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [transactions, setTransactions] = useState([]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAnalyze = (e) => {
    e.preventDefault();

    if (
      !formData.amount ||
      !formData.type ||
      !formData.merchant ||
      !formData.location ||
      !formData.device
    ) {
      alert("Please fill all transaction details.");
      return;
    }

    setIsAnalyzing(true);

    setTimeout(() => {
      const amount = Number(formData.amount);

      let risk = "LOW";
      let score = 92;
      let status = "SAFE";

      if (amount > 50000) {
        risk = "HIGH";
        score = 28;
        status = "FRAUD";
      } else if (amount > 20000) {
        risk = "MEDIUM";
        score = 61;
        status = "REVIEW";
      }

      const result = {
        risk,
        score,
        status,
      };

      setAnalysis(result);

      const newTransaction = {
        ...formData,
        risk,
        status,
        time: new Date().toLocaleTimeString(),
      };

      setTransactions((prev) => [newTransaction, ...prev]);

      setIsAnalyzing(false);
    }, 1000);
  };

  const handleLogout = () => {
    localStorage.removeItem("spectraUser");
    sessionStorage.removeItem("spectraUser");
    navigate("/login");
  };

  return (
    <div className="fraud-page">

      {/* ================= SIDEBAR ================= */}

      <aside className="fraud-sidebar">

        <div className="fraud-logo">
          <div className="logo-box">S</div>

          <div>
            <h2>SPECTRA</h2>
            <span>AI SAFETY PLATFORM</span>
          </div>
        </div>

        <p className="menu-title">MAIN MENU</p>

        <div
          className="side-menu"
          onClick={() => navigate("/dashboard")}
        >
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

        <div className="side-menu active">
          <span>💳</span>
          Fraud Detection
        </div>

        <div className="side-menu">
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
          onClick={handleLogout}
        >
          <span>↪</span>
          Logout
        </div>

      </aside>

      {/* ================= MAIN ================= */}

      <main className="fraud-main">

        {/* HEADER */}

        <header className="fraud-header">

          <div>
            <h1>Fraud Detection</h1>

            <p>
              Analyze transactions using SPECTRA AI
              risk detection technology.
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


        {/* ================= STATISTICS ================= */}

        <section className="fraud-stats">

          <div className="fraud-stat-card">

            <div className="stat-icon blue">
              💳
            </div>

            <div>
              <span>TRANSACTIONS</span>
              <h3>{156 + transactions.length}</h3>
              <p>Analyzed</p>
            </div>

          </div>


          <div className="fraud-stat-card">

            <div className="stat-icon red">
              ⚠️
            </div>

            <div>
              <span>FRAUD DETECTED</span>
              <h3>08</h3>
              <p>This month</p>
            </div>

          </div>


          <div className="fraud-stat-card">

            <div className="stat-icon green">
              🛡️
            </div>

            <div>
              <span>SAFE TRANSACTIONS</span>
              <h3>148</h3>
              <p>Verified</p>
            </div>

          </div>

        </section>


        {/* ================= ANALYSIS ================= */}

        <section className="fraud-analysis-grid">

          {/* TRANSACTION FORM */}

          <div className="transaction-card">

            <div className="card-heading">

              <div>
                <h2>Transaction Analysis</h2>

                <p>
                  Enter transaction details for AI analysis.
                </p>
              </div>

              <span className="ai-ready">
                ● AI READY
              </span>

            </div>


            <form onSubmit={handleAnalyze}>

              <div className="form-grid">

                {/* AMOUNT */}

                <div className="form-group">

                  <label>
                    Transaction Amount
                  </label>

                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    placeholder="Enter amount"
                  />

                </div>


                {/* TYPE */}

                <div className="form-group">

                  <label>
                    Transaction Type
                  </label>

                  <select
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                  >
                    <option value="">
                      Select transaction type
                    </option>

                    <option value="Online Payment">
                      Online Payment
                    </option>

                    <option value="Bank Transfer">
                      Bank Transfer
                    </option>

                    <option value="Credit Card">
                      Credit Card
                    </option>

                    <option value="Debit Card">
                      Debit Card
                    </option>

                    <option value="UPI">
                      UPI
                    </option>

                  </select>

                </div>


                {/* MERCHANT */}

                <div className="form-group">

                  <label>
                    Merchant
                  </label>

                  <input
                    type="text"
                    name="merchant"
                    value={formData.merchant}
                    onChange={handleChange}
                    placeholder="Merchant name"
                  />

                </div>


                {/* LOCATION */}

                <div className="form-group">

                  <label>
                    Location
                  </label>

                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    placeholder="Transaction location"
                  />

                </div>


                {/* DEVICE */}

                <div className="form-group">

                  <label>
                    Device
                  </label>

                  <input
                    type="text"
                    name="device"
                    value={formData.device}
                    onChange={handleChange}
                    placeholder="Device used"
                  />

                </div>

              </div>


              {/* ANALYZE BUTTON */}

              <button
                type="submit"
                className="analyze-btn"
                disabled={isAnalyzing}
              >

                {isAnalyzing
                  ? "Analyzing Transaction..."
                  : "🔍 Analyze Transaction"}

              </button>

            </form>

          </div>


          {/* RISK ANALYSIS */}

          <div className="risk-card">

            <div className="risk-heading">

              <h2>Risk Analysis</h2>

              <span>
                REAL-TIME
              </span>

            </div>


            {!analysis ? (

              <div className="no-analysis">

                <div className="shield-icon">
                  🛡️
                </div>

                <h3>
                  No Analysis Yet
                </h3>

                <p>
                  Enter transaction details
                  <br />
                  and run AI analysis.
                </p>

              </div>

            ) : (

              <div className="analysis-result">

                <div className="result-icon">
                  {analysis.status === "SAFE"
                    ? "✓"
                    : analysis.status === "FRAUD"
                    ? "!"
                    : "⚠"}
                </div>

                <h3>
                  {analysis.status}
                </h3>

                <div className="risk-score">
                  <span>Risk Score</span>

                  <strong>
                    {analysis.score}/100
                  </strong>
                </div>

                <div className="risk-level">
                  Risk Level:
                  <strong>
                    {analysis.risk}
                  </strong>
                </div>

                <p>
                  AI analysis completed successfully.
                </p>

              </div>

            )}

          </div>

        </section>


        {/* ================= HISTORY ================= */}

        <section className="history-card">

          <div className="card-heading">

            <div>
              <h2>Transaction History</h2>

              <p>
                Recently analyzed transactions.
              </p>
            </div>

          </div>


          {transactions.length === 0 ? (

            <div className="empty-history">
              No transactions analyzed yet.
            </div>

          ) : (

            <div className="transaction-table">

              <div className="table-header">
                <span>Merchant</span>
                <span>Amount</span>
                <span>Type</span>
                <span>Risk</span>
                <span>Status</span>
              </div>

              {transactions.map((transaction, index) => (

                <div
                  className="table-row"
                  key={index}
                >

                  <span>
                    {transaction.merchant}
                  </span>

                  <span>
                    ₹{transaction.amount}
                  </span>

                  <span>
                    {transaction.type}
                  </span>

                  <span>
                    {transaction.risk}
                  </span>

                  <span
                    className={
                      transaction.status === "SAFE"
                        ? "status-safe"
                        : transaction.status === "FRAUD"
                        ? "status-fraud"
                        : "status-review"
                    }
                  >
                    {transaction.status}
                  </span>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default FraudDetection;