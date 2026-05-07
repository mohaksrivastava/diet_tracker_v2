import { useState, useEffect } from "react";
import { getLogs, getStreak, getWeekLogs, getNudges } from "../api.js";

function MacroBar({ label, val, target, color }) {
  const pct = target > 0 ? Math.min((val / target) * 100, 100) : 0;
  return (
    <div className="macro-bar-wrap">
      <div className="macro-bar-label">
        <span style={{ fontWeight: 600, fontSize: 12 }}>{label}</span>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          {Math.round(val)}g / {Math.round(target)}g
        </span>
      </div>
      <div className="macro-bar-track">
        <div className="macro-bar-fill"
             style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function Home({ user, setPage, onNudgeCount }) {
  const [logs, setLogs]         = useState([]);
  const [streak, setStreak]     = useState(0);
  const [weekData, setWeekData] = useState([]);
  const [nudge, setNudge]       = useState(null);
  const [loading, setLoading]   = useState(true);

  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    async function load() {
      try {
        const [logsData, streakData, weekRes, nudgesData] = await Promise.all([
          getLogs(today),
          getStreak(),
          getWeekLogs(),
          getNudges(),
        ]);
        setLogs(logsData || []);
        setStreak(streakData?.streak || 0);
        setWeekData(weekRes || []);
        const unread = (nudgesData || []).filter(n => !n.seen);
        onNudgeCount?.(unread.length);
        if (nudgesData?.length) setNudge(nudgesData[0]);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [today]);

  const totalCal  = logs.reduce((s, r) => s + (r.calories  || 0), 0);
  const totalProt = logs.reduce((s, r) => s + (r.protein_g || 0), 0);
  const totalCarb = logs.reduce((s, r) => s + (r.carb_g    || 0), 0);
  const totalFat  = logs.reduce((s, r) => s + (r.fat_g     || 0), 0);
  const targetCal = user.daily_cal || 1800;

  const avgCal = weekData.length
    ? Math.round(weekData.reduce((s, d) => s + (d.total_cal || 0), 0) / weekData.length)
    : 0;

  if (loading) return (
    <div className="page loading-center"><span className="spinner" /></div>
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Good day, {user.name.split(" ")[0]} 👋</h1>
      </div>

      {/* Calories stat */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between",
                      alignItems: "flex-end", marginBottom: 12 }}>
          <div>
            <div className="card-title">Today's Calories</div>
            <div style={{ fontSize: 36, fontWeight: 700,
                          color: "var(--green-deep)", lineHeight: 1 }}>
              {Math.round(totalCal)}
              <span style={{ fontSize: 16, fontWeight: 400,
                             color: "var(--text-muted)", marginLeft: 4 }}>
                / {targetCal} kcal
              </span>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "var(--text-muted)",
                          textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Remaining
            </div>
            <div style={{ fontSize: 22, fontWeight: 700,
                          color: totalCal > targetCal ? "#dc2626" : "var(--green-mid)" }}>
              {Math.max(0, targetCal - Math.round(totalCal))} kcal
            </div>
          </div>
        </div>

        <MacroBar label="Protein" val={totalProt}
                  target={Math.round(targetCal * 0.30 / 4)}
                  color="var(--protein)" />
        <div style={{ marginTop: 6 }} />
        <MacroBar label="Carbs"   val={totalCarb}
                  target={Math.round(targetCal * 0.50 / 4)}
                  color="var(--carbs)" />
        <div style={{ marginTop: 6 }} />
        <MacroBar label="Fat"     val={totalFat}
                  target={Math.round(targetCal * 0.20 / 9)}
                  color="var(--fat)" />
      </div>

      {/* Streak + avg */}
      <div className="stat-grid-2">
        <div className="stat-card">
          <div className="stat-label">Streak</div>
          <div className="stat-val">{streak}</div>
          <div className="stat-sub">days 🔥</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">7-day avg</div>
          <div className="stat-val">{avgCal}</div>
          <div className="stat-sub">kcal/day</div>
        </div>
      </div>

      {/* Latest nudge */}
      {nudge && (
        <>
          <div className="section-header">Latest Nudge</div>
          <div className={`nudge-card ${!nudge.seen ? "unread" : ""}`}>
            <div className="nudge-text">{nudge.nudge_text}</div>
            <div className="nudge-meta">
              {nudge.generated_on} · {nudge.days_analyzed} days analysed
            </div>
          </div>
        </>
      )}

      {/* Quick actions */}
      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
        <button className="btn btn-primary" style={{ flex: 1 }}
                onClick={() => setPage("plan")}>
          🗓️ Generate Plan
        </button>
        <button className="btn btn-secondary" style={{ flex: 1 }}
                onClick={() => setPage("diary")}>
          📖 View Diary
        </button>
      </div>
    </div>
  );
}
