import { useState, useEffect } from "react";
import { getNudges, markNudgeSeen } from "../api.js";

export default function Nudges({ onNudgeCount }) {
  const [nudges,  setNudges]  = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getNudges();
        setNudges(data || []);
        const unread = (data || []).filter(n => !n.seen).length;
        onNudgeCount?.(unread);
      } catch(e) { console.error(e); }
      finally { setLoading(false); }
    }
    load();
  }, []);

  async function markSeen(id) {
    await markNudgeSeen(id);
    setNudges(prev => prev.map(n => n.id === id ? { ...n, seen: true } : n));
    const unread = nudges.filter(n => n.id !== id && !n.seen).length;
    onNudgeCount?.(unread);
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Nudges</h1>
      </div>

      {loading ? (
        <div className="loading-center"><span className="spinner" /></div>
      ) : nudges.length === 0 ? (
        <div className="card" style={{ textAlign: "center", color: "var(--text-muted)",
                                       padding: "32px 16px" }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>💬</div>
          <div>No nudges yet. Nudges are generated overnight based on your logs.</div>
        </div>
      ) : (
        nudges.map(n => (
          <div key={n.id} className={`nudge-card ${!n.seen ? "unread" : ""}`}>
            <div className="nudge-text">{n.nudge_text}</div>
            <div style={{ display: "flex", justifyContent: "space-between",
                          alignItems: "center", marginTop: 8 }}>
              <div className="nudge-meta">
                {n.generated_on} · {n.days_analyzed} days analysed
              </div>
              {!n.seen && (
                <button
                  style={{ background: "none", border: "none", cursor: "pointer",
                           fontSize: 12, fontWeight: 600, color: "var(--green-mid)" }}
                  onClick={() => markSeen(n.id)}>
                  Mark read ✓
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
