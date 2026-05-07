import { useState, useEffect, useCallback } from "react";
import { getLogs, addLog, updateLog, deleteLog, getRecipes } from "../api.js";

const MEAL_TYPES = ["breakfast", "lunch", "snack", "dinner"];

function EditModal({ entry, recipes, onSave, onClose }) {
  const [mealType, setMealType] = useState(entry.meal_type);
  const [calories, setCalories] = useState(entry.calories);
  const [protein,  setProtein]  = useState(entry.protein_g);
  const [carb,     setCarb]     = useState(entry.carb_g);
  const [fat,      setFat]      = useState(entry.fat_g);
  const [saving,   setSaving]   = useState(false);

  // If recipe in DB, let user pick portion and auto-compute macros
  const recipe = recipes.find(r => r.name === entry.recipe_name);
  const [portion, setPortion] = useState(
    recipe ? Math.round((entry.calories / recipe.calories) * 10) / 10 : 1.0
  );

  useEffect(() => {
    if (recipe) {
      setCalories(Math.round(recipe.calories    * portion));
      setProtein (Math.round(recipe.protein     * portion * 10) / 10);
      setCarb    (Math.round(recipe.carbohydrate* portion * 10) / 10);
      setFat     (Math.round(recipe.fat         * portion * 10) / 10);
    }
  }, [portion, recipe]);

  async function save() {
    setSaving(true);
    try {
      await updateLog(entry.id, {
        meal_type: mealType,
        calories: Number(calories),
        protein_g: Number(protein),
        carb_g: Number(carb),
        fat_g: Number(fat),
      });
      onSave();
    } catch(e) { alert(e?.detail || "Save failed"); setSaving(false); }
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-title">Edit: {entry.recipe_name}</div>

        <div className="form-group">
          <label className="form-label">Meal type</label>
          <select className="form-select" value={mealType}
                  onChange={e => setMealType(e.target.value)}>
            {MEAL_TYPES.map(m => (
              <option key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</option>
            ))}
          </select>
        </div>

        {recipe ? (
          <div className="form-group">
            <label className="form-label">Portion</label>
            <div style={{ display: "flex", gap: 6 }}>
              {[0.5, 1.0, 1.5, 2.0].map(p => (
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
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
              {calories} kcal · P:{protein}g · C:{carb}g · F:{fat}g
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {[["Calories (kcal)", calories, setCalories],
              ["Protein (g)", protein, setProtein],
              ["Carbs (g)", carb, setCarb],
              ["Fat (g)", fat, setFat]].map(([l, v, s]) => (
              <div className="form-group" key={l}>
                <label className="form-label">{l}</label>
                <input className="form-input" type="number" min="0" step="0.1"
                       value={v} onChange={e => s(e.target.value)} />
              </div>
            ))}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button className="btn btn-secondary" style={{ flex: 1 }}
                  onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" style={{ flex: 1 }}
                  onClick={save} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddModal({ logDate, recipes, onSave, onClose }) {
  const [selected, setSelected] = useState("");
  const [mealType, setMealType] = useState("lunch");
  const [portion,  setPortion]  = useState(1.0);
  const [saving,   setSaving]   = useState(false);

  const recipe = recipes.find(r => r.name === selected);
  const cal  = recipe ? Math.round(recipe.calories      * portion) : 0;
  const prot = recipe ? Math.round(recipe.protein       * portion * 10) / 10 : 0;
  const carb = recipe ? Math.round(recipe.carbohydrate  * portion * 10) / 10 : 0;
  const fat  = recipe ? Math.round(recipe.fat           * portion * 10) / 10 : 0;

  async function save() {
    if (!recipe) { alert("Select a recipe."); return; }
    setSaving(true);
    try {
      await addLog({
        log_date: logDate, recipe_name: recipe.name,
        meal_type: mealType, calories: cal,
        protein_g: prot, carb_g: carb, fat_g: fat,
      });
      onSave();
    } catch(e) { alert(e?.detail || "Failed to log"); setSaving(false); }
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-title">Add Meal</div>

        <div className="form-group">
          <label className="form-label">Recipe</label>
          <select className="form-select" value={selected}
                  onChange={e => setSelected(e.target.value)}>
            <option value="">— Select recipe —</option>
            {recipes.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Meal type</label>
          <select className="form-select" value={mealType}
                  onChange={e => setMealType(e.target.value)}>
            {MEAL_TYPES.map(m => (
              <option key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Portion</label>
          <div style={{ display: "flex", gap: 6 }}>
            {[0.5, 1.0, 1.5, 2.0].map(p => (
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
                        padding: "10px", marginBottom: 14, textAlign: "center" }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
              {cal} kcal · P:{prot}g · C:{carb}g · F:{fat}g
            </span>
          </div>
        )}

        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" style={{ flex: 1 }}
                  onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" style={{ flex: 1 }}
                  onClick={save} disabled={!recipe || saving}>
            {saving ? <span className="spinner" /> : "Log Meal"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Diary({ user }) {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate]       = useState(today);
  const [logs, setLogs]       = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editEntry, setEditEntry] = useState(null);
  const [showAdd, setShowAdd]     = useState(false);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLogs(date);
      setLogs(data || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  }, [date]);

  useEffect(() => {
    async function loadAll() {
      const [rec] = await Promise.all([getRecipes(), loadLogs()]);
      setRecipes((rec || []).filter(r => r.category === "recipe"));
    }
    loadAll();
  }, []);

  useEffect(() => { loadLogs(); }, [loadLogs]);

  async function handleDelete(id) {
    if (!confirm("Delete this entry?")) return;
    await deleteLog(id);
    loadLogs();
  }

  const totalCal  = logs.reduce((s, r) => s + (r.calories  || 0), 0);
  const totalProt = logs.reduce((s, r) => s + (r.protein_g || 0), 0);
  const totalCarb = logs.reduce((s, r) => s + (r.carb_g    || 0), 0);
  const totalFat  = logs.reduce((s, r) => s + (r.fat_g     || 0), 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Diary</h1>
        <button className="btn btn-primary"
                style={{ padding: "8px 14px", fontSize: 13 }}
                onClick={() => setShowAdd(true)}>
          + Add
        </button>
      </div>

      <div className="date-row">
        <input type="date" value={date} max={today}
               onChange={e => setDate(e.target.value)} />
      </div>

      {/* Daily totals */}
      {logs.length > 0 && (
        <div className="stat-grid" style={{ marginBottom: 12 }}>
          {[["Cal", Math.round(totalCal), "kcal"],
            ["Protein", Math.round(totalProt), "g"],
            ["Carbs", Math.round(totalCarb), "g"],
            ["Fat", Math.round(totalFat), "g"]].map(([l, v, u]) => (
            <div className="stat-card" key={l}>
              <div className="stat-label">{l}</div>
              <div className="stat-val">{v}</div>
              <div className="stat-sub">{u}</div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading-center"><span className="spinner" /></div>
        ) : logs.length === 0 ? (
          <div style={{ color: "var(--text-muted)", textAlign: "center",
                        padding: "20px 0", fontSize: 14 }}>
            No meals logged for this date.
          </div>
        ) : (
          logs.map(lg => (
            <div key={lg.id} className="log-row">
              <div className="log-info">
                <div className="log-name">{lg.recipe_name}</div>
                <div className="log-detail">
                  <span className={`meal-pill ${lg.meal_type}`}>{lg.meal_type}</span>
                  {lg.calories} kcal · P:{Math.round(lg.protein_g)}g ·
                  C:{Math.round(lg.carb_g)}g · F:{Math.round(lg.fat_g)}g
                </div>
              </div>
              <div className="log-actions">
                <button className="icon-btn" onClick={() => setEditEntry(lg)}>✏️</button>
                <button className="icon-btn" onClick={() => handleDelete(lg.id)}>🗑️</button>
              </div>
            </div>
          ))
        )}
      </div>

      {editEntry && (
        <EditModal
          entry={editEntry}
          recipes={recipes}
          onSave={() => { setEditEntry(null); loadLogs(); }}
          onClose={() => setEditEntry(null)}
        />
      )}

      {showAdd && (
        <AddModal
          logDate={date}
          recipes={recipes}
          onSave={() => { setShowAdd(false); loadLogs(); }}
          onClose={() => setShowAdd(false)}
        />
      )}
    </div>
  );
}
