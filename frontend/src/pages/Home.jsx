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

function WeekChart({ weekData, targetCal }) {
  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - 6 + i);
    return d.toISOString().slice(0, 10);
  });

  const lookup = {};
  (weekData || []).forEach(r => { lookup[r.log_date] = Math.round(r.total_cal || 0); });
  const vals = days.map(d => lookup[d] || 0);

  const DAY_ABBR = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
  const labels = days.map(d => DAY_ABBR[new Date(d + "T12:00:00").getDay()]);

  const W = 300, H = 130;
  const PAD = { t: 18, b: 28, l: 6, r: 36 };
  const cW = W - PAD.l - PAD.r;
  const cH = H - PAD.t - PAD.b;

  const maxVal = Math.max(targetCal * 1.3, ...vals, 1);
  const step   = cW / 7;
  const barW   = step * 0.55;
  const scaleY = v => cH * (1 - v / maxVal);
  const targetY = PAD.t + scaleY(targetCal);

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`}>
      {vals.map((v, i) => {
        const cx = PAD.l + i * step + step / 2;
        const bH = (v / maxVal) * cH;
        const y  = PAD.t + scaleY(v);
        const isToday = i === 6;
        return (
          <g key={i}>
            <rect x={cx - barW / 2} y={PAD.t} width={barW} height={cH}
                  fill="var(--linen-dark)" rx={3} opacity={0.35} />
            {v > 0 && (
              <rect x={cx - barW / 2} y={y} width={barW} height={bH}
                    fill={isToday ? "var(--green-deep)" : "var(--green-light)"}
                    rx={3} />
            )}
            {isToday && v > 0 && (
              <text x={cx} y={y - 4} textAnchor="middle"
                    fontSize={8} fontWeight="700" fill="var(--green-deep)">
                {v}
              </text>
            )}
          </g>
        );
      })}

      <line x1={PAD.l} y1={targetY} x2={W - PAD.r} y2={targetY}
            stroke="var(--green-deep)" strokeWidth={1.5}
            strokeDasharray="4,3" opacity={0.6} />
      <text x={W - PAD.r + 4} y={targetY + 4}
            fontSize={8} fill="var(--green-deep)" opacity={0.7}>
        {targetCal}
      </text>

      {labels.map((lbl, i) => {
        const cx = PAD.l + i * step + step / 2;
        return (
          <text key={i} x={cx} y={H - PAD.b + 14} textAnchor="middle"
                fontSize={9.5}
                fill={i === 6 ? "var(--green-deep)" : "var(--text-muted)"}
                fontWeight={i === 6 ? "700" : "400"}>
            {lbl}
          </text>
        );
      })}
    </svg>
  );
}

export default function Home({ user, setPage, onNudgeCount, onLogout }) {
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
        if (e?.detail?.toLowerCase?.().includes("invalid") ||
            e?.detail?.toLowerCase?.().includes("expired")) {
          onLogout?.();
          return;
        }
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

  const rollingDeficit = weekData.reduce((s, d) => s + (targetCal - (d.total_cal || 0)), 0);
  const adaptiveAdj = weekData.length > 0 ? Math.round(rollingDeficit * 0.25) : 0;
  const adaptiveCal = Math.max(800, targetCal + adaptiveAdj);
  const showAdaptive = weekData.length > 0 && Math.abs(adaptiveAdj) >= 50;

  if (loading) return (
    <div className="page loading-center"><span className="spinner" /></div>
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Good day, {user.name.split(" ")[0]} 👋</h1>
      </div>

      {/* Today's Calories */}
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
        <MacroBar label="Carbs" val={totalCarb}
                  target={Math.round(targetCal * 0.50 / 4)}
                  color="var(--carbs)" />
        <div style={{ marginTop: 6 }} />
        <MacroBar label="Fat" val={totalFat}
                  target={Math.round(targetCal * 0.20 / 9)}
                  color="var(--fat)" />

        {showAdaptive && (
          <div className="adaptive-indicator">
            <span className="adaptive-indicator-label">
              {adaptiveAdj > 0 ? "▲" : "▼"} Adaptive target
            </span>
            <span className="adaptive-indicator-val">
              {adaptiveCal} kcal
              <span style={{ fontWeight: 400, fontSize: 11, marginLeft: 4, opacity: 0.8 }}>
                ({adaptiveAdj > 0 ? "+" : ""}{adaptiveAdj} this week)
              </span>
            </span>
          </div>
        )}
      </div>

      {/* Streak + 7-day avg */}
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

      {/* 7-day performance chart */}
      <div className="card">
        <div className="card-title">7-Day Performance</div>
        <WeekChart weekData={weekData} targetCal={targetCal} />
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
    </div>
  );
}
