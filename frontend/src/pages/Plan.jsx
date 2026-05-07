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

function SlotCard({ slot, slotType }) {
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
          <div key={i} className="recipe-row">
            <span className="recipe-name">
              {r.name}{r.portion && r.portion !== 1 ? ` (${r.portion}×)` : ""}
            </span>
            <span className="recipe-macros">
              {Math.round(r.calories_shown || r.calories * (r.portion||1))} kcal ·
              P:{Math.round((r.protein_shown || r.protein * (r.portion||1)))}g
            </span>
          </div>
        ))}
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
  const [loading,   setLoading]   = useState(false);
  const [initLoading, setInitLoading] = useState(true);
  const [error,     setError]     = useState("");
  const [logSuccess, setLogSuccess] = useState(false);

  // Controls
  const [numMeals, setNumMeals] = useState(user.num_meals || 3);
  const [foodPref, setFoodPref] = useState(user.food_pref || "veg");

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
      });
      setPlans(result.plans || []);
      setActivePlan(0);
    } catch(e) {
      setError(e?.detail || "Failed to generate plan.");
    } finally {
      setLoading(false);
    }
  }

  async function logAll() {
    if (!plans[activePlan]) return;
    const plan = plans[activePlan];
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

  const plan = plans[activePlan];
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
                <SlotCard key={slotType} slotType={slotType} slot={slot} />
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
