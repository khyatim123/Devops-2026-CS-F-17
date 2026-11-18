import { useEffect, useRef, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
const SPECTRA_URL = import.meta.env.VITE_SPECTRA_URL || "http://localhost:5173";
const POLL_MS = 500;
const DEFAULTS = { camera_index: 0, eye_threshold: 0.21, closure_seconds: 2, alarm: true };
const loadSettings = () => {
  try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem("spectra-settings")) }; } catch { return DEFAULTS; }
};
const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

// Browser siren (Web Audio) - unlocked by the Start click
function useSiren() {
  const ctx = useRef(null), timer = useRef(null);
  const unlock = () => { ctx.current ||= new (window.AudioContext || window.webkitAudioContext)(); ctx.current.resume(); };
  const beep = (f) => {
    const c = ctx.current; if (!c) return;
    const o = c.createOscillator(), g = c.createGain();
    o.type = "square"; o.frequency.value = f; g.gain.value = 0.15;
    o.connect(g).connect(c.destination); o.start(); o.stop(c.currentTime + 0.22);
  };
  const start = () => { if (timer.current) return; let hi = false; timer.current = setInterval(() => { beep(hi ? 1320 : 880); hi = !hi; }, 260); };
  const stop = () => { clearInterval(timer.current); timer.current = null; };
  return { unlock, start, stop };
}

function Spark({ data, min, max, threshold, color = "#34d399" }) {
  const W = 300, H = 80;
  const y = (v) => H - ((Math.min(Math.max(v, min), max) - min) / (max - min)) * H;
  const pts = data.map((v, i) => v == null ? null : `${(i / Math.max(data.length - 1, 1)) * W},${y(v)}`).filter(Boolean).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-24 w-full rounded-lg bg-slate-950/60">
      {threshold != null && <line x1="0" x2={W} y1={y(threshold)} y2={y(threshold)} stroke="#f87171" strokeDasharray="4 4" strokeWidth="1" />}
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

const TONES = {
  slate: "border-slate-800 text-slate-100", green: "border-emerald-500/50 text-emerald-300",
  red: "border-red-500 text-red-300", amber: "border-amber-500/60 text-amber-300",
};
const Card = ({ label, value, tone = "slate", icon }) => (
  <div className={`rounded-2xl border bg-slate-900/70 p-4 backdrop-blur ${TONES[tone]}`}>
    <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400"><span>{label}</span><span>{icon}</span></div>
    <div className="mt-1 text-2xl font-semibold">{value}</div>
  </div>
);
const Panel = ({ title, children }) => (
  <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4"><h2 className="mb-3 font-semibold">{title}</h2>{children}</section>
);

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [settings, setSettings] = useState(loadSettings);
  const [status, setStatus] = useState(null);
  const [up, setUp] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [streamKey, setStreamKey] = useState(0);
  const [history, setHistory] = useState([]);
  const [samples, setSamples] = useState([]);
  const [elapsed, setElapsed] = useState(0);
  const siren = useSiren();
  const lastCount = useRef(null), runStart = useRef(null), maxClosure = useRef(0);

  useEffect(() => localStorage.setItem("spectra-settings", JSON.stringify(settings)), [settings]);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const d = await (await fetch(`${API}/status`)).json();
        if (!alive) return;
        setUp(true); setStatus(d);
        if (d.running) {
          setSamples((s) => [...s.slice(-119), { ear: d.ear, perclos: d.perclos }]);
          maxClosure.current = Math.max(maxClosure.current, d.closure_duration || 0);
        }
      } catch { if (alive) { setUp(false); setStatus(null); } }
    };
    tick(); const id = setInterval(tick, POLL_MS);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const running = !!status?.running, alert = !!status?.alert;

  useEffect(() => {
    if (running && !runStart.current) { runStart.current = Date.now(); setSamples([]); maxClosure.current = 0; }
    if (!running) runStart.current = null;
    const id = setInterval(() => setElapsed(runStart.current ? Math.floor((Date.now() - runStart.current) / 1000) : 0), 1000);
    return () => clearInterval(id);
  }, [running]);

  useEffect(() => { if (alert && settings.alarm) siren.start(); else siren.stop(); return siren.stop; }, [alert, settings.alarm]);

  useEffect(() => {
    if (!status) return;
    if (lastCount.current !== null && status.alert_count > lastCount.current)
      setHistory((h) => [{ time: new Date().toLocaleTimeString(), closure: status.closure_duration }, ...h].slice(0, 30));
    lastCount.current = status.alert_count;
  }, [status?.alert_count]);

  const post = async (path) => {
    setBusy(true);
    try {
      const r = await fetch(`${API}${path}`, { method: "POST" });
      if (!r.ok) throw new Error(`${path.split("?")[0]} failed (${r.status})`);
      if (path.startsWith("/start")) setStreamKey((k) => k + 1);
      setError("");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const start = () => { siren.unlock(); post(`/start?camera_index=${settings.camera_index}&eye_threshold=${settings.eye_threshold}&closure_seconds=${settings.closure_seconds}`); };
  const set = (k, v) => setSettings((s) => ({ ...s, [k]: v }));

  const eyes = status?.eyes ?? "—";
  const driver = !running ? "Inactive" : alert ? "DROWSY" : status?.perclos_high || status?.yawning ? "Fatigued" : eyes === "NO FACE" ? "No face" : "Normal";
  const dTone = alert ? "red" : !running ? "slate" : driver === "Normal" ? "green" : "amber";
  const glow = alert ? "border-red-500 shadow-[0_0_40px_-5px_rgba(239,68,68,.6)]" : running ? "border-emerald-500/50 shadow-[0_0_30px_-8px_rgba(16,185,129,.5)]" : "border-slate-800";
  const ears = samples.map((s) => s.ear).filter((v) => v != null);
  const avgEar = ears.length ? (ears.reduce((a, b) => a + b, 0) / ears.length).toFixed(2) : "—";
  const detErr = status?.message?.startsWith("Detector error") ? status.message : "";

  const nav = [["dashboard", "📡", "Dashboard"], ["analytics", "📊", "Analytics"], ["settings", "⚙️", "Settings"]];

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900 text-slate-100">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-slate-800 bg-slate-950/80 p-4 md:flex">
        <div className="mb-8 text-xl font-bold tracking-widest">DRIVER SAFETY</div>
        {nav.map(([id, icon, name]) => (
          <button key={id} onClick={() => setTab(id)} className={`mb-1 rounded-lg px-3 py-2 text-left text-sm ${tab === id ? "bg-emerald-500/15 text-emerald-300" : "text-slate-400 hover:bg-slate-800"}`}>{icon} {name}</button>
        ))}
        <div className="mt-auto text-xs text-slate-500">Driver Safety Module<br />Prototype safety aid</div>
      </aside>

      <main className="min-w-0 flex-1 p-5">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div><h1 className="text-xl font-bold">{nav.find((n) => n[0] === tab)[2]}</h1><p className="text-sm text-slate-400">Real-time driver fatigue monitoring</p></div>
          <div className="flex items-center gap-2 text-sm">
            <a href={SPECTRA_URL} className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-200 hover:bg-slate-800">← Back to Spectra</a>
            <div className="flex gap-1 md:hidden">{nav.map(([id, icon]) => <button key={id} onClick={() => setTab(id)} className={`rounded-lg px-2 py-1 ${tab === id ? "bg-slate-700" : ""}`}>{icon}</button>)}</div>
            {running && <span className="rounded-full bg-slate-800 px-3 py-1 font-mono">⏱ {fmt(elapsed)}</span>}
            <span className={`rounded-full px-3 py-1 ${up ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"}`}>● Backend {up ? "online" : "offline"}</span>
          </div>
        </header>

        {alert && <div className="mb-5 animate-pulse rounded-2xl border border-red-500 bg-red-600/20 p-4"><div className="text-lg font-bold text-red-300">🚨 DROWSINESS DETECTED</div><div className="text-red-200">Prolonged eye closure detected. Please take a break.</div></div>}
        {!alert && running && (status?.perclos_high || status?.yawning) && <div className="mb-5 rounded-2xl border border-amber-500 bg-amber-500/15 p-4"><div className="font-bold text-amber-300">⚠️ Signs of fatigue</div><div className="text-amber-200">{status.yawning && "You are yawning. "}{status.perclos_high && `Eyes closed ${(status.perclos * 100).toFixed(0)}% of the last minute. `}Consider taking a break.</div></div>}
        {(error || detErr) && <div className="mb-5 rounded-2xl border border-amber-500/60 bg-amber-500/10 p-3 text-amber-200">{detErr || error}</div>}
        {!up && <div className="mb-5 rounded-2xl border border-slate-700 bg-slate-900 p-3 text-slate-300">Cannot reach the backend at <code>{API}</code>. Start it with <code>python app.py</code>.</div>}

        {tab === "dashboard" && (
          <>
            <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Card icon="🟢" label="Monitoring" value={running ? "Active" : "Inactive"} tone={running ? "green" : "slate"} />
              <Card icon="👁️" label="Eye status" value={eyes} tone={eyes === "CLOSED" ? "red" : "slate"} />
              <Card icon="📏" label="EAR" value={status?.ear ?? "—"} />
              <Card icon="⏳" label="Eyes closed" value={`${(status?.closure_duration ?? 0).toFixed(1)}s`} tone={status?.closure_duration > 0.5 ? "amber" : "slate"} />
              <Card icon="🧠" label="Driver status" value={driver} tone={dTone} />
              <Card icon="📉" label="PERCLOS (60 s)" value={`${((status?.perclos ?? 0) * 100).toFixed(0)}%`} tone={status?.perclos_high ? "amber" : "slate"} />
              <Card icon="🥱" label="Yawns" value={status?.yawn_count ?? 0} tone={status?.yawning ? "amber" : "slate"} />
              <Card icon="🚨" label="Alerts this run" value={status?.alert_count ?? 0} />
            </div>
            <div className="grid gap-5 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <div className={`relative aspect-video overflow-hidden rounded-2xl border-2 bg-black transition-shadow ${glow}`}>
                  {running ? <>
                    <img key={streamKey} src={`${API}/video_feed?k=${streamKey}`} alt="Live camera" className="h-full w-full object-contain" />
                    <span className="absolute left-3 top-3 rounded-full bg-black/60 px-3 py-1 text-xs font-semibold"><span className="mr-1 text-red-500">●</span>LIVE</span>
                  </> : <div className="flex h-full items-center justify-center text-slate-500">Camera preview — press Start</div>}
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button onClick={start} disabled={!up || busy || running} className="rounded-xl bg-emerald-600 px-6 py-2.5 font-medium hover:bg-emerald-500 disabled:opacity-40">▶ Start monitoring</button>
                  <button onClick={() => post("/stop")} disabled={!up || busy || !running} className="rounded-xl bg-red-600 px-6 py-2.5 font-medium hover:bg-red-500 disabled:opacity-40">■ Stop</button>
                  <button onClick={() => { siren.unlock(); set("alarm", !settings.alarm); }} className="rounded-xl border border-slate-600 px-5 py-2.5 hover:bg-slate-800">{settings.alarm ? "🔔 Alarm on" : "🔇 Alarm off"}</button>
                </div>
              </div>
              <div className="space-y-5">
                <Panel title="Live EAR"><Spark data={samples.map((s) => s.ear)} min={0} max={0.45} threshold={settings.eye_threshold} /><p className="mt-1 text-xs text-slate-400">Red dashed line = closed-eye threshold ({settings.eye_threshold})</p></Panel>
                <Panel title="Alert history">
                  {history.length === 0 ? <p className="text-sm text-slate-400">No drowsiness events this session.</p> :
                    <ul className="max-h-60 space-y-2 overflow-auto">{history.map((h, i) => <li key={i} className="flex justify-between rounded-lg bg-slate-800 px-3 py-2 text-sm"><span>{h.time}</span><span className="text-red-300">closed {h.closure}s</span></li>)}</ul>}
                </Panel>
              </div>
            </div>
          </>
        )}

        {tab === "analytics" && (
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="grid grid-cols-2 gap-3 lg:col-span-2 lg:grid-cols-4">
              <Card icon="⏱" label="Session time" value={fmt(elapsed)} />
              <Card icon="🚨" label="Alerts" value={status?.alert_count ?? 0} tone={status?.alert_count ? "red" : "slate"} />
              <Card icon="🥱" label="Yawns" value={status?.yawn_count ?? 0} />
              <Card icon="📏" label="Average EAR" value={avgEar} />
              <Card icon="👁️" label="Longest eye closure" value={`${maxClosure.current.toFixed(1)}s`} />
              <Card icon="📉" label="PERCLOS now" value={`${((status?.perclos ?? 0) * 100).toFixed(0)}%`} tone={status?.perclos_high ? "amber" : "slate"} />
            </div>
            <Panel title="EAR over the last minute"><Spark data={samples.map((s) => s.ear)} min={0} max={0.45} threshold={settings.eye_threshold} /></Panel>
            <Panel title="PERCLOS over the last minute"><Spark data={samples.map((s) => s.perclos)} min={0} max={0.5} threshold={0.15} color="#fbbf24" /><p className="mt-1 text-xs text-slate-400">Dashed line = 15% fatigue limit</p></Panel>
          </div>
        )}

        {tab === "settings" && (
          <div className="max-w-xl space-y-5">
            <Panel title="Detection settings">
              <label className="mb-4 block text-sm">Camera index
                <input type="number" min="0" max="10" value={settings.camera_index} onChange={(e) => set("camera_index", +e.target.value)} className="mt-1 block w-24 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5" /></label>
              <label className="mb-4 block text-sm">Eye-closed threshold (EAR): <b>{settings.eye_threshold}</b>
                <input type="range" min="0.15" max="0.30" step="0.01" value={settings.eye_threshold} onChange={(e) => set("eye_threshold", +e.target.value)} className="mt-1 block w-full" /></label>
              <label className="block text-sm">Alert after eyes closed for: <b>{settings.closure_seconds}s</b>
                <input type="range" min="0.5" max="5" step="0.5" value={settings.closure_seconds} onChange={(e) => set("closure_seconds", +e.target.value)} className="mt-1 block w-full" /></label>
              <p className="mt-3 text-xs text-slate-400">Applied the next time you press Start{running && " — stop and start again to use changes"}.</p>
            </Panel>
            <Panel title="Alarm">
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={settings.alarm} onChange={(e) => { siren.unlock(); set("alarm", e.target.checked); }} /> Play siren in the browser</label>
              <button onClick={() => post("/alarm/test?seconds=2")} disabled={!up} className="mt-3 rounded-lg border border-slate-600 px-4 py-1.5 text-sm hover:bg-slate-800 disabled:opacity-40">Test server alarm</button>
            </Panel>
            <Panel title="Connection"><p className="text-sm text-slate-300">Backend: <code>{API}</code></p></Panel>
          </div>
        )}
      </main>
    </div>
  );
}
