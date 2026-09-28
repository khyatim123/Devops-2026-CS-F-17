import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";
import Dashboard from "./pages/Dashboard";
import DriverSafety from "./pages/DriverSafety";
import FraudDetection from "./pages/FraudDetection";
import Analytics from "./pages/Analytics";


function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Home />} />

        <Route path="/login" element={<Login />} />

        <Route path="/register" element={<CreateAccount />} />

        <Route path="/dashboard" element={<Dashboard />} />

        <Route
          path="/driver-safety"
          element={<DriverSafety />}
        />

        <Route
          path="/fraud-detection"
          element={<FraudDetection />}
        />
<Route path="/analytics" element={<Analytics />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;