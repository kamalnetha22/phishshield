import { useState, useEffect } from "react";

const API = "https://phishshield-production-9182.up.railway.app";

const RISK_CONFIG = {
  high:   { color: "#E24B4A", bg: "#FCEBEB", label: "HIGH RISK",   icon: "⛔" },
  medium: { color: "#BA7517", bg: "#FAEEDA", label: "MEDIUM RISK", icon: "⚠️" },
  low:    { color: "#639922", bg: "#EAF3DE", label: "LOW RISK",    icon: "🔔" },
  safe:   { color: "#1D9E75", bg: "#E1F5EE", label: "SAFE",        icon: "✅" },
};

function ConfidenceBar({ value, isPhishing }) {
  const color = isPhishing
    ? value > 85 ? "#E24B4A" : value > 65 ? "#BA7517" : "#639922"
    : "#1D9E75";
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#888", marginBottom: 4 }}>
        <span>Confidence</span>
        <span style={{ fontWeight: 600, color }}>{value}%</span>
      </div>
      <div style={{ height: 8, background: "#f0f0f0", borderRadius: 99, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${value}%`, background: color,
          borderRadius: 99, transition: "width 0.8s cubic-bezier(.4,0,.2,1)"
        }} />
      </div>
    </div>
  );
}

function ResultCard({ result }) {
  const cfg = RISK_CONFIG[result.risk_level] || RISK_CONFIG.safe;
  return (
    <div style={{
      border: `2px solid ${cfg.color}`,
      borderRadius: 16, padding: "20px 24px",
      background: cfg.bg, marginTop: 20,
      animation: "fadeIn 0.4s ease"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: 24 }}>{cfg.icon}</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, color: cfg.color }}>{cfg.label}</div>
          <div style={{ fontSize: 12, color: "#666", marginTop: 1 }}>
            {result.type === "url" ? "URL Analysis" : "Email Analysis"} · {new Date(result.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>

      <div style={{
        fontSize: 13, color: "#444", background: "rgba(255,255,255,0.6)",
        borderRadius: 8, padding: "8px 12px", wordBreak: "break-all",
        fontFamily: "monospace", marginBottom: 12
      }}>
        {result.input}
      </div>

      <ConfidenceBar value={result.confidence} isPhishing={result.is_phishing} />

      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#666", marginBottom: 8, letterSpacing: "0.05em" }}>
          TOP SIGNAL FEATURES
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
          {result.top_features.map((f, i) => (
            <div key={i} style={{
              background: "rgba(255,255,255,0.7)", borderRadius: 8,
              padding: "6px 10px", fontSize: 12
            }}>
              <span style={{ color: "#666" }}>{f.feature}</span>
              <span style={{ float: "right", fontWeight: 600, color: "#333" }}>{f.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function HistoryItem({ item }) {
  const cfg = RISK_CONFIG[item.risk_level] || RISK_CONFIG.safe;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "10px 14px", borderRadius: 10,
      background: "#fafafa", border: "1px solid #eee",
      marginBottom: 6, fontSize: 13
    }}>
      <span style={{ fontSize: 16 }}>{cfg.icon}</span>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#333",
          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {item.input}
        </div>
        <div style={{ fontSize: 11, color: "#aaa", marginTop: 2 }}>
          {item.type} · {new Date(item.timestamp).toLocaleTimeString()}
        </div>
      </div>
      <span style={{ fontSize: 11, fontWeight: 700, color: cfg.color,
        background: cfg.bg, padding: "2px 8px", borderRadius: 99 }}>
        {item.confidence}%
      </span>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("url");
  const [url, setUrl] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sender, setSender] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchHistory();
  }, [result]);

  async function fetchStats() {
    try {
      const r = await fetch(`${API}/stats`);
      setStats(await r.json());
    } catch {}
  }

  async function fetchHistory() {
    try {
      const r = await fetch(`${API}/history?limit=10`);
      const d = await r.json();
      setHistory(d.results || []);
    } catch {}
  }

  async function analyze() {
    setError(""); setResult(null); setLoading(true);
    try {
      const endpoint = tab === "url" ? "/analyze-url" : "/analyze-email";
      const payload = tab === "url"
        ? { url }
        : { subject, body, sender };

      const r = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail || "Analysis failed");
      }
      setResult(await r.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = tab === "url" ? url.trim().length > 3 : body.trim().length > 5;

  return (
    <div style={{ minHeight: "100vh", background: "#f7f8fa", fontFamily: "'Segoe UI', system-ui, sans-serif" }}>
      <style>{`
        @keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }
        @keyframes spin { to { transform: rotate(360deg) } }
        * { box-sizing: border-box; }
        textarea, input { outline: none; font-family: inherit; }
        textarea:focus, input:focus { border-color: #378ADD !important; box-shadow: 0 0 0 3px rgba(55,138,221,0.12); }
      `}</style>

      <div style={{ maxWidth: 960, margin: "0 auto", padding: "32px 20px" }}>

        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>🛡️</div>
          <h1 style={{ fontSize: 32, fontWeight: 800, color: "#1a1a2e", margin: 0, letterSpacing: "-0.5px" }}>
            PhishShield
          </h1>
          <p style={{ color: "#888", marginTop: 6, fontSize: 15 }}>
            Real-time phishing detection powered by ML ensemble (Random Forest + XGBoost)
          </p>
        </div>

        {stats && stats.total > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 24 }}>
            {[
              { label: "Total Analyzed", value: stats.total, color: "#378ADD" },
              { label: "Phishing Detected", value: stats.phishing, color: "#E24B4A" },
              { label: "Phishing Rate", value: `${stats.phishing_rate}%`, color: "#BA7517" },
            ].map((s, i) => (
              <div key={i} style={{
                background: "#fff", borderRadius: 12, padding: "14px 18px",
                border: "1px solid #eee", textAlign: "center"
              }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20, alignItems: "start" }}>

          <div style={{ background: "#fff", borderRadius: 16, padding: 24, border: "1px solid #eee" }}>
            <div style={{ display: "flex", gap: 6, marginBottom: 20 }}>
              {["url", "email"].map(t => (
                <button key={t} onClick={() => { setTab(t); setResult(null); setError(""); }}
                  style={{
                    padding: "8px 20px", borderRadius: 99, border: "none",
                    cursor: "pointer", fontSize: 14, fontWeight: 600, transition: "all 0.2s",
                    background: tab === t ? "#1a1a2e" : "#f0f0f0",
                    color: tab === t ? "#fff" : "#666"
                  }}>
                  {t === "url" ? "🔗 URL" : "📧 Email"}
                </button>
              ))}
            </div>

            {tab === "url" ? (
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: "#444", display: "block", marginBottom: 6 }}>
                  URL to analyze
                </label>
                <input
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && canSubmit && analyze()}
                  placeholder="https://example.com or paste any suspicious URL"
                  style={{
                    width: "100%", padding: "12px 16px", borderRadius: 10,
                    border: "1.5px solid #e0e0e0", fontSize: 14, color: "#333",
                    background: "#fafafa", transition: "all 0.2s"
                  }}
                />
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#444", display: "block", marginBottom: 6 }}>Sender email</label>
                  <input value={sender} onChange={e => setSender(e.target.value)}
                    placeholder="sender@example.com"
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 10, border: "1.5px solid #e0e0e0", fontSize: 13, background: "#fafafa" }} />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#444", display: "block", marginBottom: 6 }}>Subject line</label>
                  <input value={subject} onChange={e => setSubject(e.target.value)}
                    placeholder="Email subject..."
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 10, border: "1.5px solid #e0e0e0", fontSize: 13, background: "#fafafa" }} />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#444", display: "block", marginBottom: 6 }}>Email body</label>
                  <textarea value={body} onChange={e => setBody(e.target.value)}
                    placeholder="Paste the email body here..."
                    rows={5}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 10, border: "1.5px solid #e0e0e0", fontSize: 13, background: "#fafafa", resize: "vertical" }} />
                </div>
              </div>
            )}

            <button
              onClick={analyze}
              disabled={!canSubmit || loading}
              style={{
                width: "100%", marginTop: 16, padding: "13px", borderRadius: 10,
                border: "none", cursor: canSubmit && !loading ? "pointer" : "not-allowed",
                background: canSubmit && !loading ? "#1a1a2e" : "#ccc",
                color: "#fff", fontSize: 15, fontWeight: 700,
                transition: "all 0.2s", letterSpacing: "0.02em"
              }}>
              {loading
                ? <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                    <span style={{ display: "inline-block", width: 16, height: 16, border: "2px solid #fff",
                      borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                    Analyzing...
                  </span>
                : "Analyze Now →"}
            </button>

            {error && (
              <div style={{ marginTop: 12, padding: "10px 14px", background: "#FCEBEB",
                borderRadius: 8, color: "#A32D2D", fontSize: 13 }}>
                ⚠️ {error}
              </div>
            )}

            {result && <ResultCard result={result} />}
          </div>

          <div style={{ background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #eee" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#333", marginBottom: 14, letterSpacing: "0.05em" }}>
              RECENT ANALYSES
            </div>
            {history.length === 0
              ? <div style={{ color: "#bbb", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
                  No analyses yet
                </div>
              : history.map((item, i) => <HistoryItem key={i} item={item} />)
            }
          </div>

        </div>

        <div style={{ textAlign: "center", marginTop: 28, fontSize: 12, color: "#bbb" }}>
          PhishShield · Random Forest + XGBoost Ensemble · Built with FastAPI + React
        </div>
      </div>
    </div>
  );
}
