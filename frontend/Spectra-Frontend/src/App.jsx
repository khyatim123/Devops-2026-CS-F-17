import React, { useState } from "react";
import {
  Activity, AlertTriangle, ArrowUpRight, BarChart3, Bell, BrainCircuit,
  CarFront, ChevronRight, CircleHelp, LayoutDashboard, Mail, Menu,
  Monitor, Settings, ShieldCheck, ShieldAlert, SlidersHorizontal, X
} from "lucide-react";

const DRIVER_URL = import.meta.env.VITE_DRIVER_APP_URL || "http://localhost:5174";
const EMAIL_URL = import.meta.env.VITE_EMAIL_APP_URL || "http://localhost:5175";

const nav = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Driver Safety", icon: CarFront, url: DRIVER_URL },
  { label: "Email Intelligence", icon: Mail, url: EMAIL_URL },
  { label: "Analytics", icon: BarChart3 },
  { label: "System Monitoring", icon: Monitor },
  { label: "Settings", icon: Settings }
];

function App() {
  const [page, setPage] = useState("Overview");
  const [mobileOpen, setMobileOpen] = useState(false);

  const launch = (url) => window.open(url, "_blank", "noopener,noreferrer");
  const select = (item) => {
    setPage(item.label);
    setMobileOpen(false);
    if (item.url) launch(item.url);
  };

  return (
    <div className="shell">
      {mobileOpen && <button className="scrim" aria-label="Close menu" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><BrainCircuit size={23}/></div>
          <div><div className="brand-name">SPECTRA</div><div className="brand-sub">INTELLIGENCE SYSTEM</div></div>
          <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={19}/></button>
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="nav-list">
          {nav.map(item => {
            const Icon = item.icon;
            return <button key={item.label} onClick={() => select(item)}
              className={`nav-link ${page === item.label ? "selected" : ""}`}>
              <Icon size={18}/><span>{item.label}</span>{item.url && <ArrowUpRight className="nav-external" size={14}/>}
            </button>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="platform-note"><ShieldCheck size={17}/><span>AI-powered security</span></div>
          <div className="user-row"><div className="avatar">SA</div><div><strong>Spectra Admin</strong><small>Administrator</small></div><SlidersHorizontal size={16}/></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu/></button>
          <div className="breadcrumb">SPECTRA <span>/</span> {page.toUpperCase()}</div>
          <div className="topbar-right"><span className="system-live"><i/> Dashboard running</span><button className="icon-button" aria-label="Notifications"><Bell size={18}/></button><div className="top-avatar">SA</div></div>
        </header>

        <section className="page-heading">
          <div><div className="eyebrow">UNIFIED SECURITY OPERATIONS</div><h1>{page === "Overview" ? "Security Overview" : page}</h1><p>One workspace for your AI-powered monitoring and intelligence systems.</p></div>
          <div className="heading-chip"><Activity size={15}/> CONTROL CENTER</div>
        </section>

        {page === "Overview" && <Overview launch={launch}/>}
        {page === "Driver Safety" && <ModulePage title="Driver Safety & Drowsiness Detection" icon={<CarFront/>} description="Your existing webcam-based driver monitoring application. It opens separately and remains an independent project." url={DRIVER_URL} launch={launch} />}
        {page === "Email Intelligence" && <ModulePage title="Email Fraud & Spam Detection" icon={<Mail/>} description="Your existing MailShield email classification application. It opens separately and remains an independent project." url={EMAIL_URL} launch={launch} />}
        {page === "Analytics" && <InfoPage title="Analytics workspace" description="A unified place for detection statistics, historical trends and model performance. Live charts can be enabled after connecting the module APIs." rows={[["Driver Safety","Awaiting live API data"],["Email Intelligence","Awaiting live API data"],["Historical trends","Not connected yet"]]}/>}
        {page === "System Monitoring" && <InfoPage title="Configured services" description="These are configured endpoints, not verified live health checks." rows={[["SPECTRA frontend","Running in browser"],["Driver backend",import.meta.env.VITE_DRIVER_API_URL || "http://127.0.0.1:8001"],["Email backend",import.meta.env.VITE_EMAIL_API_URL || "http://127.0.0.1:8002"]]}/>}
        {page === "Settings" && <InfoPage title="Application connections" description="Change the frontend addresses in the .env file and restart the development server." rows={[["Driver Safety frontend",DRIVER_URL],["Email Intelligence frontend",EMAIL_URL],["Driver Safety API",import.meta.env.VITE_DRIVER_API_URL || "http://127.0.0.1:8001"],["Email Detection API",import.meta.env.VITE_EMAIL_API_URL || "http://127.0.0.1:8002"]]}/>}
        <footer className="footer">SPECTRA AI SECURITY PLATFORM <span>•</span> UNIFIED INTELLIGENCE DASHBOARD</footer>
      </main>
    </div>
  );
}

function Overview({ launch }) {
  return <>
    <section className="stats-grid">
      <Stat icon={<ShieldCheck/>} label="Platform" value="SPECTRA" note="Unified control center" tone="violet"/>
      <Stat icon={<CarFront/>} label="Security module 01" value="Driver Safety" note="Drowsiness detection" tone="blue"/>
      <Stat icon={<Mail/>} label="Security module 02" value="Email Shield" note="Fraud and spam detection" tone="cyan"/>
      <Stat icon={<Activity/>} label="Dashboard status" value="Available" note="Frontend is running" tone="green"/>
    </section>

    <div className="section-title"><div><h2>Intelligence modules</h2><p>Launch your existing applications without merging or replacing their code.</p></div><span className="count-pill">02 MODULES</span></div>
    <section className="module-grid">
      <ModuleCard number="01" icon={<CarFront size={25}/>} title="Driver Safety" category="COMPUTER VISION" description="Webcam-based driver monitoring that detects prolonged eye closure and drowsiness, with an alert system." accent="violet" url={DRIVER_URL} launch={launch}/>
      <ModuleCard number="02" icon={<Mail size={25}/>} title="Email Intelligence" category="EMAIL SECURITY" description="AI-powered email analysis to identify spam and potentially fraudulent messages." accent="cyan" url={EMAIL_URL} launch={launch}/>
    </section>

    <section className="bottom-grid">
      <div className="panel">
        <div className="panel-heading"><div><h3>Platform components</h3><p>Independent applications connected through one dashboard</p></div><span className="subtle-pill">OVERVIEW</span></div>
        <div className="component-row"><div className="component-icon purple"><CarFront/></div><div className="component-copy"><strong>Driver Safety</strong><small>Existing drowsiness detection frontend</small></div><span className="component-type">MODULE 01</span></div>
        <div className="component-row"><div className="component-icon teal"><Mail/></div><div className="component-copy"><strong>Email Intelligence</strong><small>Existing MailShield frontend</small></div><span className="component-type">MODULE 02</span></div>
        <div className="component-row"><div className="component-icon blue"><LayoutDashboard/></div><div className="component-copy"><strong>SPECTRA Control Center</strong><small>Central navigation and module launcher</small></div><span className="component-type">MAIN UI</span></div>
      </div>
      <div className="panel">
        <div className="panel-heading"><div><h3>Service configuration</h3><p>Local development endpoints</p></div><Monitor size={18} className="muted-icon"/></div>
        <div className="service-row"><span>Dashboard</span><b className="text-green">Running</b></div>
        <div className="service-row"><span>Driver API</span><b>Port 8001</b></div>
        <div className="service-row"><span>Email API</span><b>Port 8002</b></div>
        <div className="service-row"><span>Architecture</span><b>Modular</b></div>
        <div className="notice"><AlertTriangle size={15}/> Backend health and detection metrics are not yet connected.</div>
      </div>
    </section>
  </>;
}

function Stat({ icon, label, value, note, tone }) {
  return <div className="stat-card"><div className="stat-top"><span>{label}</span><div className={`stat-icon ${tone}`}>{icon}</div></div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;
}

function ModuleCard({ number, icon, title, category, description, accent, url, launch }) {
  return <article className={`module-card ${accent}`}>
    <div className="module-card-top"><div className="large-module-icon">{icon}</div><span className="module-number">MODULE / {number}</span></div>
    <div className="module-category">{category}</div><h3>{title}</h3><p>{description}</p>
    <div className="module-card-bottom"><span className="endpoint">{url}</span><button className="launch-button" onClick={() => launch(url)}>Launch application <ArrowUpRight size={16}/></button></div>
  </article>;
}

function ModulePage({ title, icon, description, url, launch }) {
  return <div className="wide-panel standalone-module"><div className="large-module-icon">{icon}</div><div className="module-category">CONNECTED APPLICATION</div><h2>{title}</h2><p>{description}</p><div className="endpoint-box"><span>Frontend URL</span><strong>{url}</strong></div><button className="launch-button" onClick={() => launch(url)}>Open in a new browser tab <ArrowUpRight size={16}/></button><div className="notice"><CircleHelp size={15}/> If the application does not open, start its own frontend development server and verify the URL in the .env file.</div></div>;
}

function InfoPage({ title, description, rows }) {
  return <div className="wide-panel"><div className="panel-heading"><div><h2>{title}</h2><p>{description}</p></div><ShieldAlert className="muted-icon"/></div>{rows.map(([name,value]) => <div className="info-row" key={name}><span>{name}</span><strong>{value}</strong></div>)}</div>;
}

export default App;
