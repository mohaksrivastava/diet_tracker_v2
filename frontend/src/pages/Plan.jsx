import { useState, useEffect } from "react";
import { getRecipes, getSettings, runOptimizer, addLog } from "../api.js";

const SLOT_COLORS = {
  breakfast: "var(--breakfast)",
  lunch:     "var(--lunch)",
  snack:     "var(--snack)",
  dinner:    "var(--dinner)",
};

const FOOD_PREFS = [
  { val: "vegan",   label: "Vegan" },
  { val: "veg",     label: "Vegetarian" },
  { val: "dairy",   label: "Dairy incl." },
  { val: "egg",     label: "Egg incl." },
  { val: "non-veg", label: "Non-veg" },
];

function SlotCard({ slot, slotType, recipes, onUpdateRecipe, onRemoveRecipe, onAddRecipe }) {
  const [addRecipeId, setAddRecipeId] = useState("");

  return (
    <div className="slot-card">
      <div className="slot-header" style={{ background: SLOT_COLORS[slotType] || "#888" }}>
        <span style={{ fontSize: 16 }}>
          {slotType === "breakfast" ? "🌅"
           : slotType === "lunch"   ? "☀️"
           : slotType === "dinner"  ? "🌙" : "🍎"}
        </span>
        {slotType.charAt(0).toUpperCase() + slotType.slice(1)} ·{" "}
        {Math.round(slot.total_cal)} kcal
      </div>
      <div className="slot-body">
        {slot.recipes?.map((r, i) => (
          <div key={i} className="recipe-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <span className="recipe-name">
                {r.name}
              </span>
              <span className="recipe-macros" style={{ display: 'block', fontSize: '0.85em', color: 'var(--text-muted)' }}>
                {Math.round(r.calories * (r.portion||1))} kcal ·
                P:{Math.round((r.protein * (r.portion||1)))}g
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button onClick={() => onUpdateRecipe(slotType, i, Math.max(0.25, (r.portion||1) - 0.25))}
                      style={{ padding: '2px 8px', borderRadius: '4px', border: '1px solid #ccc' }}>-</button>
              <span style={{ minWidth: '30px', textAlign: 'center' }}>{r.portion || 1}×</span>
              <button onClick={() => onUpdateRecipe(slotType, i, (r.portion||1) + 0.25)}
                      style={{ padding: '2px 8px', borderRadius: '4px', border: '1px solid #ccc' }}>+</button>
              <button onClick={() => onRemoveRecipe(slotType, i)}
                      style={{ padding: '2px 8px', borderRadius: '4px', border: '1px solid #ff4d4f', color: '#ff4d4f', marginLeft: '8px' }}>✕</button>
            </div>
          </div>
        ))}

        <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
          <select
            className="form-select"
            value={addRecipeId}
            onChange={(e) => setAddRecipeId(e.target.value)}
            style={{ flex: 1, padding: '4px 8px', fontSize: '0.9em' }}
          >
            <option value="">Add recipe...</option>
            {recipes?.map((r, i) => (
              <option key={i} value={r.name}>{r.name}</option>
            ))}
          </select>
          <button
            className="btn btn-secondary"
            style={{ padding: '4px 12px', fontSize: '0.9em' }}
            onClick={() => {
              if (addRecipeId) {
                onAddRecipe(slotType, addRecipeId);
                setAddRecipeId("");
              }
            }}
            disabled={!addRecipeId}
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

function MacroRow({ label, val, target, color }) {
  const pct  = target > 0 ? Math.min((val / target) * 100, 100) : 0;
  const diff = val - target;
  const sign = diff > 0 ? "+" : "";
  return (
    <div className="macro-bar-wrap" style={{ marginBottom: 8 }}>
      <div className="macro-bar-label">
        <span style={{ fontWeight: 600, fontSize: 12 }}>{label}</span>
        <span style={{ fontSize: 12, color: Math.abs(diff) > 5 ? "#dc2626" : "var(--text-muted)" }}>
          {Math.round(val)}g {sign}{Math.round(diff)}g
        </span>
      </div>
      <div className="macro-bar-track">
        <div className="macro-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function Plan({ user, setPage }) {
  const [settings,  setSettings]  = useState(null);
  const [recipes,   setRecipes]   = useState([]);
  const [plans,     setPlans]     = useState([]);
  const [activePlan, setActivePlan] = useState(0);
  const [activePlanData, setActivePlanData] = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [initLoading, setInitLoading] = useState(true);
  const [error,     setError]     = useState("");
  const [logSuccess, setLogSuccess] = useState(false);

  // Controls
  const [numMeals, setNumMeals] = useState(user.num_meals || 3);
  const [foodPref, setFoodPref] = useState(user.food_pref || "veg");
  const [cuisineFilter, setCuisineFilter] = useState("any");

  const cuisines = ["any", ...new Set(recipes.map(r => r.cuisine).filter(Boolean))];

  useEffect(() => {
    async function load() {
      try {
        const [s, r] = await Promise.all([getSettings(), getRecipes()]);
        setSettings(s);
        setRecipes((r || []).filter(rx => rx.category === "recipe"));
        if (s?.user) {
          setNumMeals(s.user.num_meals);
          setFoodPref(s.user.food_pref);
        }
      } catch(e) { console.error(e); }
      finally { setInitLoading(false); }
    }
    load();
  }, []);

  async function generate() {
    if (!settings) return;
    setLoading(true); setError(""); setPlans([]); setLogSuccess(false);

    const nt = settings.nutrition_target || {
      cal_target: settings.user.daily_cal,
      protein_g: Math.round(settings.user.daily_cal * 0.30 / 4),
      carb_g:    Math.round(settings.user.daily_cal * 0.50 / 4),
      fat_g:     Math.round(settings.user.daily_cal * 0.20 / 9),
      fiber_g: 30,
      cal_soft_pct: 0.08, protein_soft_lo: 0.05, fat_soft_hi: 0.10,
      carb_soft_pct: 0.15, fiber_soft_lo: 0.10,
      cal_hard_pct: 0.20, protein_hard_lo: 0.20, fat_hard_hi: 0.25,
      fat_hard_lo: 0.30, carb_hard_pct: 0.35, fiber_hard_lo: 0.30,
      k_cal: 1000, k_protein_under: 2000, k_fat_over: 1500,
      k_carb: 400, k_fiber_under: 800,
    };

    try {
      const result = await runOptimizer({
        num_meals: numMeals,
        food_pref: foodPref,
        target_cal: settings.user.daily_cal,
        nutrition_target: nt,
        cuisine_filter: cuisineFilter,
      });
      setPlans(result.plans || []);
      setActivePlan(0);
      setActivePlanData(result.plans?.[0] || null);
    } catch(e) {
      setError(e?.detail || "Failed to generate plan.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setActivePlanData(plans[activePlan] ? JSON.parse(JSON.stringify(plans[activePlan])) : null);
  }, [activePlan, plans]);

  function recalculateMacros(updatedPlan) {
    let totalCal = 0, totalProt = 0, totalCarb = 0, totalFat = 0;

    Object.values(updatedPlan.slots).forEach(slot => {
      let slotCal = 0, slotProt = 0, slotCarb = 0, slotFat = 0;
      (slot.recipes || []).forEach(r => {
        const portion = r.portion || 1;
        slotCal += r.calories * portion;
        slotProt += r.protein * portion;
        slotCarb += (r.carbohydrate || r.carb || 0) * portion;
        slotFat += r.fat * portion;
      });
      slot.total_cal = slotCal;
      totalCal += slotCal;
      totalProt += slotProt;
      totalCarb += slotCarb;
      totalFat += slotFat;
    });

    updatedPlan.total_cal = totalCal;
    updatedPlan.protein_g = totalProt;
    updatedPlan.carb_g = totalCarb;
    updatedPlan.fat_g = totalFat;
    return updatedPlan;
  }

  function handleUpdateRecipe(slotType, recipeIndex, newPortion) {
    if (!activePlanData) return;
    const newPlan = { ...activePlanData };
    newPlan.slots[slotType].recipes[recipeIndex].portion = newPortion;
    delete newPlan.slots[slotType].recipes[recipeIndex].calories_shown;
    delete newPlan.slots[slotType].recipes[recipeIndex].protein_shown;
    delete newPlan.slots[slotType].recipes[recipeIndex].carb_shown;
    delete newPlan.slots[slotType].recipes[recipeIndex].fat_shown;
    setActivePlanData(recalculateMacros(newPlan));
  }

  function handleRemoveRecipe(slotType, recipeIndex) {
    if (!activePlanData) return;
    const newPlan = { ...activePlanData };
    newPlan.slots[slotType].recipes.splice(recipeIndex, 1);
    setActivePlanData(recalculateMacros(newPlan));
  }

  function handleAddRecipe(slotType, recipeName) {
    if (!activePlanData) return;
    const recipeTemplate = recipes.find(r => r.name === recipeName);
    if (!recipeTemplate) return;

    const newPlan = { ...activePlanData };
    if (!newPlan.slots[slotType].recipes) {
      newPlan.slots[slotType].recipes = [];
    }

    newPlan.slots[slotType].recipes.push({
      ...recipeTemplate,
      portion: 1
    });

    setActivePlanData(recalculateMacros(newPlan));
  }

  async function logAll() {
    if (!activePlanData) return;
    const plan = activePlanData;
    const today = new Date().toISOString().slice(0, 10);
    const entries = [];

    for (const [slotType, slot] of Object.entries(plan.slots || {})) {
      for (const r of (slot.recipes || [])) {
        entries.push({
          log_date: today,
          recipe_name: r.name,
          meal_type: slotType,
          calories: Math.round(r.calories_shown || r.calories * (r.portion||1)),
          protein_g: Math.round((r.protein_shown || r.protein * (r.portion||1)) * 10) / 10,
          carb_g:    Math.round((r.carb_shown    || r.carbohydrate * (r.portion||1)) * 10) / 10,
          fat_g:     Math.round((r.fat_shown     || r.fat * (r.portion||1)) * 10) / 10,
        });
      }
    }

    try {
      await Promise.all(entries.map(e => addLog(e)));
      setLogSuccess(true);
      setTimeout(() => setPage("diary"), 1500);
    } catch(e) {
      setError(e?.detail || "Failed to log some entries.");
    }
  }

  if (initLoading) return <div className="page loading-center"><span className="spinner" /></div>;

  const plan = activePlanData;
  const nt   = settings?.nutrition_target;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Meal Plan</h1>
      </div>

      {/* Controls */}
      <div className="card">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10,
                      marginBottom: 12 }}>
          <div>
            <div className="form-label" style={{ marginBottom: 6 }}>Meals/day</div>
            <div style={{ display: "flex", gap: 4 }}>
              {[2,3,4,5].map(n => (
                <button key={n}
                        style={{
                          flex: 1, padding: "7px 0", borderRadius: 7,
                          border: numMeals === n
                            ? "2px solid var(--green-deep)"
                            : "1.5px solid var(--linen-dark)",
                          background: numMeals === n ? "var(--green-deep)" : "white",
                          color: numMeals === n ? "white" : "var(--text)",
                          fontWeight: 600, fontSize: 13, cursor: "pointer",
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
              {FOOD_PREFS.map(f => (
                <option key={f.val} value={f.val}>{f.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="form-label" style={{ marginBottom: 6 }}>Cuisine Filter</div>
          <select className="form-select" style={{ padding: "7px 10px" }}
                  value={cuisineFilter} onChange={e => setCuisineFilter(e.target.value)}>
            {cuisines.map(c => (
              <option key={c} value={c}>
                {c === "any" ? "Any Cuisine" : c.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>

        <button className="btn btn-primary btn-full" onClick={generate}
                disabled={loading || !settings}>
          {loading ? <><span className="spinner" style={{ marginRight: 8 }} /> Generating…</>
                   : "✨ Generate Plans"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {logSuccess && <div className="alert alert-success">All meals logged! Redirecting…</div>}

      {plans.length > 0 && (
        <>
          {/* Plan selector */}
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
              {/* Macro summary */}
              {nt && (
                <div className="card">
                  <div className="card-title">Macro breakdown</div>
                  <MacroRow label="Protein" val={plan.protein_g || 0}
                            target={nt.protein_g} color="var(--protein)" />
                  <MacroRow label="Carbs"   val={plan.carb_g    || 0}
                            target={nt.carb_g}    color="var(--carbs)" />
                  <MacroRow label="Fat"     val={plan.fat_g     || 0}
                            target={nt.fat_g}     color="var(--fat)" />
                  <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
                    Total: <strong>{Math.round(plan.total_cal || 0)}</strong> kcal
                    (target {nt.cal_target})
                  </div>
                </div>
              )}

              {/* Slot cards */}
              {Object.entries(plan.slots || {}).map(([slotType, slot]) => (
                <SlotCard
                  key={slotType}
                  slotType={slotType}
                  slot={slot}
                  recipes={recipes}
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
    </div>
  );
}
