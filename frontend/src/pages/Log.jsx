import { useState, useEffect } from "react";
import { getRecipes, getLogs, addLog } from "../api.js";

const MEAL_TYPES = ["breakfast", "lunch", "snack", "dinner"];
const PORTIONS   = [0.5, 1.0, 1.5, 2.0];

export default function Log({ user, setPage }) {
  const today = new Date().toISOString().slice(0, 10);

  const [recipes, setRecipes]   = useState([]);
  const [todayLogs, setTodayLogs] = useState([]);
  const [selected, setSelected] = useState("");
  const [mealType, setMealType] = useState("lunch");
  const [portion, setPortion]   = useState(1.0);
  const [logDate, setLogDate]   = useState(today);
  const [loading, setLoading]   = useState(false);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [rec, logs] = await Promise.all([getRecipes(), getLogs(today)]);
        setRecipes((rec || []).filter(r => r.category === "recipe"));
        setTodayLogs(logs || []);
      } catch(e) { setError("Failed to load recipes."); }
      finally { setLoading(false); }
    }
    load();
  }, [today]);

  const recipe = recipes.find(r => r.name === selected);
  const cal    = recipe ? Math.round(recipe.calories   * portion) : 0;
  const prot   = recipe ? Math.round(recipe.protein    * portion * 10) / 10 : 0;
  const carb   = recipe ? Math.round(recipe.carbohydrate * portion * 10) / 10 : 0;
  const fat    = recipe ? Math.round(recipe.fat        * portion * 10) / 10 : 0;

  async function handleLog() {
    if (!recipe) { setError("Select a recipe first."); return; }
    setSaving(true); setError(""); setSuccess("");
    try {
      await addLog({
        log_date: logDate, recipe_name: recipe.name,
        meal_type: mealType, calories: cal,
        protein_g: prot, carb_g: carb, fat_g: fat,
      });
      setSuccess(`Logged ${recipe.name} (${cal} kcal)`);
      const updated = await getLogs(today);
      setTodayLogs(updated || []);
      setSelected(""); setPortion(1.0);
    } catch(e) { setError(e?.detail || "Failed to log."); }
    finally { setSaving(false); }
  }

  const totalCal = todayLogs.reduce((s, r) => s + (r.calories || 0), 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Log a Meal</h1>
        <button className="btn btn-secondary"
                style={{ padding: "6px 12px", fontSize: 13 }}
                onClick={() => setPage("diary")}>
          View Diary
        </button>
      </div>

      {error   && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card">
        <div className="form-group">
          <label className="form-label">Date</label>
          <input type="date" className="form-input" value={logDate}
                 onChange={e => setLogDate(e.target.value)} max={today} />
        </div>

        <div className="form-group">
          <label className="form-label">Recipe</label>
          <select className="form-select" value={selected}
                  onChange={e => setSelected(e.target.value)}>
            <option value="">— Select a recipe —</option>
            {recipes.map(r => (
              <option key={r.name} value={r.name}>{r.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Meal type</label>
          <select className="form-select" value={mealType}
                  onChange={e => setMealType(e.target.value)}>
            {MEAL_TYPES.map(m => (
              <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Portion</label>
          <div style={{ display: "flex", gap: 6 }}>
            {PORTIONS.map(p => (
              <button key={p}
                      style={{
                        flex: 1, padding: "8px 0", borderRadius: 8,
                        border: portion === p
                          ? "2px solid var(--green-deep)"
                          : "1.5px solid var(--linen-dark)",
                        background: portion === p ? "var(--green-deep)" : "white",
                        color: portion === p ? "white" : "var(--text)",
                        fontWeight: 600, fontSize: 13, cursor: "pointer",
                      }}
                      onClick={() => setPortion(p)}>
                {p}×
              </button>
            ))}
          </div>
        </div>

        {recipe && (
          <div style={{ background: "var(--linen)", borderRadius: 10,
                        padding: "10px 14px", marginBottom: 14,
                        display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
                        gap: 8, textAlign: "center" }}>
            {[["Cal", cal, "kcal"], ["Protein", prot, "g"],
              ["Carbs", carb, "g"], ["Fat", fat, "g"]].map(([l, v, u]) => (
              <div key={l}>
                <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase",
                              color: "var(--text-muted)", letterSpacing: "0.06em" }}>{l}</div>
                <div style={{ fontSize: 18, fontWeight: 700,
                              color: "var(--green-deep)" }}>{v}</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{u}</div>
              </div>
            ))}
          </div>
        )}

        <button className="btn btn-primary btn-full" onClick={handleLog}
                disabled={!recipe || saving}>
          {saving ? <span className="spinner" /> : "Log Meal"}
        </button>
      </div>

      {/* Today summary */}
      {todayLogs.length > 0 && (
        <>
          <div className="section-header">Today so far — {Math.round(totalCal)} kcal</div>
          <div className="card">
            {todayLogs.map((lg, i) => (
              <div key={i} className="log-row">
                <div className="log-info">
                  <div className="log-name">{lg.recipe_name}</div>
                  <div className="log-detail">
                    <span className={`meal-pill ${lg.meal_type}`}>{lg.meal_type}</span>
                    {lg.calories} kcal · P:{Math.round(lg.protein_g)}g
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
