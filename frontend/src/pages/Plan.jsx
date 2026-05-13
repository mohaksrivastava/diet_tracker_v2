import { useState, useEffect } from "react";
import { getSettings, runOptimizer, addLog, getRecipeDetail, getRecipes } from "../api.js";

const FOOD_PREFS = [
  { val: "vegan",   label: "Vegan" },
  { val: "veg",     label: "Vegetarian" },
  { val: "dairy",   label: "Dairy incl." },
  { val: "egg",     label: "Egg incl." },
  { val: "non-veg", label: "Non-veg" },
];

function RecipeModal({ name, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getRecipeDetail(name)
      .then(d => setDetail(d))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [name]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="modal-handle" />
        {loading ? (
          <div className="loading-center"><span className="spinner" /></div>
        ) : !detail ? (
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
            No details available for this recipe yet.
          </p>
        ) : (
          <>
            <div className="modal-title">{name}</div>
            {detail.serving_note && (
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>
                {detail.serving_note}
              </p>
            )}
            {detail.ingredients?.length > 0 && (
              <>
                <div className="card-title" style={{ marginTop: 8 }}>Ingredients</div>
                <ul style={{ paddingLeft: 18, marginBottom: 14 }}>
                  {detail.ingredients.map((ing, i) => (
                    <li key={i} style={{ fontSize: 14, marginBottom: 4 }}>{ing}</li>
                  ))}
                </ul>
              </>
            )}
            {detail.steps?.length > 0 && (
              <>
                <div className="card-title">Instructions</div>
                <ol style={{ paddingLeft: 18 }}>
                  {detail.steps.map((step, i) => (
                    <li key={i} style={{ fontSize: 14, marginBottom: 8, lineHeight: 1.5 }}>{step}</li>
                  ))}
                </ol>
              </>
            )}
            {!detail.ingredients?.length && !detail.steps?.length && (
              <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Recipe details coming soon.</p>
            )}
          </>
        )}
        <button className="btn btn-secondary btn-full" style={{ marginTop: 20 }} onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

function SlotCard({ slot, recipes, onRecipeClick, onUpdateRecipe, onRemoveRecipe, onAddRecipe }) {
  const slotType = slot.type;
  const [addRecipeId, setAddRecipeId] = useState("");
  const STEP = 0.25;

  return (
    <div className="slot-card">
      <div className={`slot-header ${slotType}`}>
        <span style={{ fontSize: 16 }}>
          {slotType === "breakfast" ? "🌅"
           : slotType === "lunch"   ? "☀️"
           : slotType === "dinner"  ? "🌙" : "🍎"}
        </span>
        {slotType.charAt(0).toUpperCase() + slotType.slice(1)} ·{" "}
        {Math.round(slot.total_cal)} kcal
      </div>
      <div className="slot-body">
        {slot.recipes?.map((r, i) => {
          const cal  = Math.round((r.calories || 0) * (r.portion || 1));
          const prot = Math.round((r.protein || 0) * (r.portion || 1) * 10) / 10;
          const port = r.portion || 1;
          return (
            <div key={i} style={{
              paddingTop: i > 0 ? 8 : 4,
              paddingBottom: 10,
              borderBottom: i < slot.recipes.length - 1 ? "1px solid rgba(0,0,0,0.06)" : "none",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                            alignItems: "flex-start", gap: 8 }}>
                <button
                  style={{
                    background: "none", border: "none", cursor: "pointer",
                    fontFamily: "DM Sans, sans-serif", fontSize: 14, fontWeight: 500,
                    color: "var(--green-mid)", textAlign: "left", flex: 1, padding: 0,
                    textDecoration: "underline", textDecorationStyle: "dotted",
                    textUnderlineOffset: "3px",
                  }}
                  onClick={() => onRecipeClick?.(r.name)}>
                  {r.name}{r.is_gap_filler ? " ★" : ""}
                </button>
                <span style={{ fontSize: 12, color: "var(--text-muted)",
                               whiteSpace: "nowrap", marginTop: 1 }}>
                  {cal} kcal · P:{prot}g
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Portion:</span>
                <div className="stepper">
                  <button className="stepper-btn" disabled={port <= 0.25}
                          onClick={() => onUpdateRecipe?.(slotType, i,
                            parseFloat(Math.max(0.25, port - STEP).toFixed(2)))}>
                    −
                  </button>
                  <span className="stepper-val">
                    {port % 1 === 0 ? port + "×" : port.toFixed(2) + "×"}
                  </span>
                  <button className="stepper-btn" disabled={port >= 3.0}
                          onClick={() => onUpdateRecipe?.(slotType, i,
                            parseFloat(Math.min(3.0, port + STEP).toFixed(2)))}>
                    +
                  </button>
                </div>
                <button
                  onClick={() => onRemoveRecipe?.(slotType, i)}
                  style={{ marginLeft: "auto", padding: "2px 8px", borderRadius: 4,
                           border: "1px solid #ff4d4f", color: "#ff4d4f",
                           background: "none", cursor: "pointer", fontSize: 12 }}>
                  ✕
                </button>
              </div>
            </div>
          );
        })}

        <div style={{ marginTop: 10, display: "flex", gap: 6 }}>
          <select className="form-select" value={addRecipeId}
                  onChange={e => setAddRecipeId(e.target.value)}
                  style={{ flex: 1, padding: "4px 8px", fontSize: "0.9em" }}>
            <option value="">Add recipe…</option>
            {recipes?.map((r, i) => (
              <option key={i} value={r.name}>{r.name}</option>
            ))}
          </select>
          <button className="btn btn-secondary"
                  style={{ padding: "4px 12px", fontSize: "0.9em" }}
                  disabled={!addRecipeId}
                  onClick={() => {
                    if (addRecipeId) { onAddRecipe?.(slotType, addRecipeId); setAddRecipeId(""); }
                  }}>
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

function MacroRow({ label, val, target, color }) {
  const pct  = target > 0 ? Math.min((val / target) * 100, 100) : 0;
  const diff = Math.round(val - target);
  const sign = diff > 0 ? "+" : "";
  return (
    <div className="macro-bar-wrap" style={{ marginBottom: 8 }}>
      <div className="macro-bar-label">
        <span style={{ fontWeight: 600, fontSize: 12 }}>{label}</span>
        <span style={{ fontSize: 12, color: Math.abs(diff) > 5 ? "#dc2626" : "var(--text-muted)" }}>
          {Math.round(val)}g {sign}{diff}g
        </span>
      </div>
      <div className="macro-bar-track">
        <div className="macro-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function Plan({ user, setPage, onLogout }) {
  const [settings,       setSettings]       = useState(null);
  const [recipes,        setRecipes]        = useState([]);
  const [plans,          setPlans]          = useState([]);
  const [activePlan,     setActivePlan]     = useState(0);
  const [activePlanData, setActivePlanData] = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [initLoading,    setInitLoading]    = useState(true);
  const [error,          setError]          = useState("");
  const [logSuccess,     setLogSuccess]     = useState(false);
  const [detailRecipe,   setDetailRecipe]   = useState(null);
  const [usedNt,         setUsedNt]         = useState(null);

  const [numMeals,      setNumMeals]      = useState(user.num_meals || 3);
  const [foodPref,      setFoodPref]      = useState(user.food_pref || "non-veg");
  const [targetCal,     setTargetCal]     = useState(user.daily_cal || 2000);
  const [cuisineFilter, setCuisineFilter] = useState("any");

  const cuisines = ["any", ...new Set(recipes.map(r => r.cuisine).filter(Boolean))];

  useEffect(() => {
    async function load() {
      try {
        const timeout = new Promise((_, rej) =>
          setTimeout(() => rej(new Error("timeout")), 15000));
        const [s, recs] = await Promise.race([
          Promise.all([getSettings(), getRecipes()]),
          timeout,
        ]);
        setSettings(s);
        setRecipes(recs || []);
        if (s?.user) {
          setNumMeals(s.user.num_meals || user.num_meals || 3);
          setFoodPref(s.user.food_pref || user.food_pref || "non-veg");
          setTargetCal(s.user.daily_cal ?? user.daily_cal ?? 2000);
        }
      } catch (e) {
        if (e?.detail?.toLowerCase?.().includes("invalid") ||
            e?.detail?.toLowerCase?.().includes("expired")) {
          onLogout?.();
          return;
        }
        console.error("load failed:", e.message || e);
      } finally {
        setInitLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    setActivePlanData(plans[activePlan]
      ? JSON.parse(JSON.stringify(plans[activePlan]))
      : null);
  }, [activePlan, plans]);

  function buildNt(cal) {
    const base = settings?.nutrition_target;
    if (base) {
      const r = cal / base.cal_target;
      return {
        ...base, cal_target: cal,
        protein_g: Math.round(base.protein_g * r),
        carb_g:    Math.round(base.carb_g    * r),
        fat_g:     Math.round(base.fat_g     * r),
        fiber_g:   Math.round(base.fiber_g   * r),
        k_protein_under: 3000,
      };
    }
    return {
      cal_target: cal,
      protein_g: Math.round(cal * 0.30 / 4),
      carb_g:    Math.round(cal * 0.50 / 4),
      fat_g:     Math.round(cal * 0.20 / 9),
      fiber_g: 30,
      cal_soft_pct: 0.08, protein_soft_lo: 0.05, fat_soft_hi: 0.10,
      carb_soft_pct: 0.15, fiber_soft_lo: 0.10,
      cal_hard_pct: 0.20, protein_hard_lo: 0.20, fat_hard_hi: 0.25,
      fat_hard_lo: 0.30, carb_hard_pct: 0.35, fiber_hard_lo: 0.30,
      k_cal: 1000, k_protein_under: 3000, k_fat_over: 1500,
      k_carb: 400, k_fiber_under: 800,
    };
  }

  function recalculateMacros(plan) {
    let totalCal = 0, totalProt = 0, totalCarb = 0, totalFat = 0;
    const slots = plan.slots.map(slot => {
      const cal  = slot.recipes.reduce((a, r) => a + (r.calories || 0) * (r.portion || 1), 0);
      const prot = slot.recipes.reduce((a, r) => a + (r.protein || 0) * (r.portion || 1), 0);
      const carb = slot.recipes.reduce((a, r) => a + (r.carbohydrate || 0) * (r.portion || 1), 0);
      const fat  = slot.recipes.reduce((a, r) => a + (r.fat || 0) * (r.portion || 1), 0);
      totalCal += cal; totalProt += prot; totalCarb += carb; totalFat += fat;
      return { ...slot, total_cal: Math.round(cal) };
    });
    return { ...plan, slots,
             total_cal: Math.round(totalCal),
             protein_g: Math.round(totalProt * 10) / 10,
             carb_g:    Math.round(totalCarb * 10) / 10,
             fat_g:     Math.round(totalFat * 10) / 10 };
  }

  function handleUpdateRecipe(slotType, recipeIndex, newPortion) {
    setActivePlanData(prev => {
      if (!prev) return prev;
      const slots = prev.slots.map(slot => {
        if (slot.type !== slotType) return slot;
        return { ...slot, recipes: slot.recipes.map((r, i) =>
          i === recipeIndex ? { ...r, portion: newPortion } : r) };
      });
      return recalculateMacros({ ...prev, slots });
    });
  }

  function handleRemoveRecipe(slotType, recipeIndex) {
    setActivePlanData(prev => {
      if (!prev) return prev;
      const slots = prev.slots.map(slot => {
        if (slot.type !== slotType) return slot;
        return { ...slot, recipes: slot.recipes.filter((_, i) => i !== recipeIndex) };
      });
      return recalculateMacros({ ...prev, slots });
    });
  }

  function handleAddRecipe(slotType, recipeName) {
    const template = recipes.find(r => r.name === recipeName);
    if (!template) return;
    setActivePlanData(prev => {
      if (!prev) return prev;
      const slots = prev.slots.map(slot => {
        if (slot.type !== slotType) return slot;
        return { ...slot, recipes: [...slot.recipes, { ...template, portion: 1 }] };
      });
      return recalculateMacros({ ...prev, slots });
    });
  }

  async function generate() {
    const cal = targetCal ?? (user.daily_cal || 2000);
    setLoading(true); setError(""); setPlans([]); setLogSuccess(false);
    const nt = buildNt(cal);
    try {
      const result = await runOptimizer({
        num_meals: numMeals,
        food_pref: foodPref,
        target_cal: cal,
        nutrition_target: nt,
        cuisine_filter: cuisineFilter,
      });
      setPlans(result.plans || []);
      setActivePlan(0);
      setUsedNt(nt);
    } catch (e) {
      setError(e?.detail || "Failed to generate plan.");
    } finally {
      setLoading(false);
    }
  }

  async function logAll() {
    if (!activePlanData) return;
    const today = new Date().toISOString().slice(0, 10);
    const entries = [];
    for (const slot of (activePlanData.slots || [])) {
      for (const r of (slot.recipes || [])) {
        entries.push({
          log_date:    today,
          recipe_name: r.name,
          meal_type:   slot.type,
          calories:    Math.round((r.calories || 0) * (r.portion || 1)),
          protein_g:   Math.round((r.protein || 0) * (r.portion || 1) * 10) / 10,
          carb_g:      Math.round((r.carbohydrate || 0) * (r.portion || 1) * 10) / 10,
          fat_g:       Math.round((r.fat || 0) * (r.portion || 1) * 10) / 10,
        });
      }
    }
    try {
      await Promise.all(entries.map(e => addLog(e)));
      setLogSuccess(true);
      setTimeout(() => setPage("diary"), 1500);
    } catch (e) {
      setError(e?.detail || "Failed to log some entries.");
    }
  }

  if (initLoading) return <div className="page loading-center"><span className="spinner" /></div>;

  const plan = activePlanData;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Meal Plan</h1>
      </div>

      {/* Controls */}
      <div className="card">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
          <div>
            <div className="form-label" style={{ marginBottom: 6 }}>Meals/day</div>
            <div style={{ display: "flex", gap: 4 }}>
              {[2, 3, 4, 5].map(n => (
                <button key={n}
                        style={{
                          flex: 1, padding: "7px 0", borderRadius: 7, cursor: "pointer",
                          border: numMeals === n ? "2px solid var(--green-deep)" : "1.5px solid var(--linen-dark)",
                          background: numMeals === n ? "var(--green-deep)" : "white",
                          color: numMeals === n ? "white" : "var(--text)",
                          fontWeight: 600, fontSize: 13,
                        }}
                        onClick={() => setNumMeals(n)}>
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="form-label" style={{ marginBottom: 6 }}>Food pref</div>
            <select className="form-select" style={{ padding: "7px 10px" }}
                    value={foodPref} onChange={e => setFoodPref(e.target.value)}>
              {FOOD_PREFS.map(f => <option key={f.val} value={f.val}>{f.label}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="form-label" style={{ marginBottom: 6 }}>Cuisine Filter</div>
          <select className="form-select" style={{ padding: "7px 10px" }}
                  value={cuisineFilter} onChange={e => setCuisineFilter(e.target.value)}>
            {cuisines.map(c => (
              <option key={c} value={c}>
                {c === "any" ? "Any Cuisine"
                 : c.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              </option>
            ))}
          </select>
        </div>

        {/* Calorie slider */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between",
                        alignItems: "center", marginBottom: 6 }}>
            <span className="form-label" style={{ marginBottom: 0 }}>Target Calories</span>
            <strong style={{ color: "var(--green-deep)", fontSize: 14 }}>
              {targetCal ?? (user.daily_cal || 2000)} kcal
            </strong>
          </div>
          <input type="range" className="cal-slider"
                 min={1000} max={3500} step={50}
                 value={targetCal ?? (user.daily_cal || 2000)}
                 onChange={e => setTargetCal(Number(e.target.value))} />
          <div style={{ display: "flex", justifyContent: "space-between",
                        fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>
            <span>1000</span><span>3500 kcal</span>
          </div>
        </div>

        <button className="btn btn-primary btn-full" onClick={generate} disabled={loading}>
          {loading
            ? <><span className="spinner" style={{ marginRight: 8 }} />Generating…</>
            : "✨ Generate Plans"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {logSuccess && <div className="alert alert-success">All meals logged! Redirecting…</div>}

      {plans.length > 0 && (
        <>
          <div className="plan-tabs">
            {plans.map((_, i) => (
              <button key={i} className={`plan-tab ${activePlan === i ? "active" : ""}`}
                      onClick={() => setActivePlan(i)}>
                Option {i + 1}
              </button>
            ))}
          </div>

          {plan && (
            <>
              {usedNt && (
                <div className="card">
                  <div className="card-title">Macro Breakdown</div>
                  <MacroRow label="Protein" val={plan.protein_g || 0}
                            target={usedNt.protein_g} color="var(--protein)" />
                  <MacroRow label="Carbs"   val={plan.carb_g    || 0}
                            target={usedNt.carb_g}    color="var(--carbs)" />
                  <MacroRow label="Fat"     val={plan.fat_g     || 0}
                            target={usedNt.fat_g}     color="var(--fat)" />
                  <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
                    Total: <strong>{Math.round(plan.total_cal || 0)}</strong> kcal
                    (target {usedNt.cal_target})
                  </div>
                </div>
              )}

              {(plan.slots || []).map(slot => (
                <SlotCard
                  key={slot.type}
                  slot={slot}
                  recipes={recipes}
                  onRecipeClick={setDetailRecipe}
                  onUpdateRecipe={handleUpdateRecipe}
                  onRemoveRecipe={handleRemoveRecipe}
                  onAddRecipe={handleAddRecipe}
                />
              ))}

              <button className="btn btn-primary btn-full"
                      style={{ marginBottom: 16 }}
                      onClick={logAll}>
                Log all meals for today →
              </button>
            </>
          )}
        </>
      )}

      {detailRecipe && (
        <RecipeModal name={detailRecipe} onClose={() => setDetailRecipe(null)} />
      )}
    </div>
  );
}
