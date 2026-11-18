import { useState } from 'react'
import axios from 'axios'
import { ShieldCheck, ShieldAlert, Mail, ScanSearch, RotateCcw } from 'lucide-react'

const API_URL = 'http://127.0.0.1:8002/api/predict'
const SPECTRA_URL = import.meta.env.VITE_SPECTRA_URL || 'http://localhost:5173'

export default function App() {
  const [email, setEmail] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState([])

  async function handleCheck(e) {
    e.preventDefault()
    if (email.trim().length < 3) {
      setError('Please enter an email message to analyze.')
      return
    }
    setLoading(true); setError(''); setResult(null)
    try {
      const response = await axios.post(API_URL, { text: email.trim() })
      setResult(response.data)
      setHistory(old => [{ ...response.data, preview: email.trim().slice(0, 75), id: Date.now() }, ...old].slice(0, 5))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not connect to the API. Make sure FastAPI is running.')
    } finally {
      setLoading(false)
    }
  }

  function reset() { setEmail(''); setResult(null); setError('') }

  return <main className="page">
    <nav className="nav"><div className="brand"><span className="brand-icon"><Mail size={20}/></span> Mail<span>Shield</span></div><a className="spectra-link" href={SPECTRA_URL}>← Back to Spectra</a><span className="status"><i/> ML SYSTEM</span></nav>
    <section className="hero">
      <div className="eyebrow"><ScanSearch size={15}/> AI-POWERED EMAIL ANALYSIS</div>
      <h1>Keep your inbox<br/><span>safe and clean.</span></h1>
      <p>Analyze an email with machine learning and identify suspicious messages before you interact with them.</p>
    </section>
    <section className="workspace">
      <div className="panel">
        <div className="panel-heading"><div><h2>Analyze an email</h2><p>Paste the subject and body below</p></div><span className="step">01 / INPUT</span></div>
        <form onSubmit={handleCheck}>
          <label htmlFor="email">EMAIL CONTENT</label>
          <textarea id="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={"Subject: Congratulations! You've won a prize...\\n\\nPaste the complete email message here..."} maxLength={20000}/>
          <div className="under-input"><span>{email.length.toLocaleString()} / 20,000 characters</span><button type="button" className="clear" onClick={reset}><RotateCcw size={13}/> Clear</button></div>
          <button className="analyze" type="submit" disabled={loading || !email.trim()}>{loading ? 'Analyzing email...' : <><ScanSearch size={17}/> Analyze email</>}</button>
        </form>
        {error && <div className="error" role="alert">{error}</div>}
        {result && <div className={`result ${result.label === 'spam' ? 'spam' : 'safe'}`} aria-live="polite">
          <div className="result-icon">{result.label === 'spam' ? <ShieldAlert size={25}/> : <ShieldCheck size={25}/>}</div>
          <div className="result-copy"><span className="result-kicker">ANALYSIS RESULT</span><h3>{result.prediction}</h3><p>{result.message}</p></div>
          <div className="confidence"><strong>{result.confidence}%</strong><span>confidence</span></div>
        </div>}
        <p className="disclaimer">Machine-learning predictions can be wrong. Do not treat this result as a guarantee of email safety.</p>
      </div>
      <aside className="side">
        <div className="side-card"><span className="side-number">01</span><h3>Text processing</h3><p>Email text is converted into numerical features using TF-IDF.</p></div>
        <div className="side-card"><span className="side-number">02</span><h3>ML classification</h3><p>A Naive Bayes model estimates whether the message is spam or legitimate.</p></div>
        <div className="side-card"><span className="side-number">03</span><h3>Instant result</h3><p>The API returns a predicted label and its model confidence.</p></div>
      </aside>
    </section>
    {history.length > 0 && <section className="history"><div className="history-title"><h2>Recent analyses</h2><span>THIS SESSION</span></div>{history.map(item => <div className="history-row" key={item.id}><span className={item.label === 'spam' ? 'dot red' : 'dot green'}/><p>{item.preview}{item.preview.length >= 75 ? '…' : ''}</p><b className={item.label === 'spam' ? 'red-text' : 'green-text'}>{item.prediction}</b></div>)}</section>}
    <footer><span>MAILSHIELD / EMAIL SPAM DETECTION</span><span>FASTAPI · REACT · SCIKIT-LEARN</span></footer>
  </main>
}
