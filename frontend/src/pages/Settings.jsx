import { useState, useEffect } from "react";
import {
  getSettings, saveProfile, saveTargets, changePassword,
  addCustomRecipe, getCustomRecipes, setStoredUser,
} from "../api.js";

const FOOD_PREFS = [
  { val: "vegan",   label: "Vegan" },
  { val: "veg",     label: "Vegetarian" },
  { val: "dairy",   label: "Dairy incl." },
  { val: "egg",     label: "Egg incl." },
  { val: "non-veg", label: "Non-veg" },
];

export default function Settings({ user, setUser, onLogout }) {
  const [settings,  setSettings]  = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [saving,    setSaving]    = useState("");
  const [msg,       setMsg]       = useState({ type: "", text: "" });

  // Profile fields
  const [dailyCal,  setDailyCal]  = useState(user.daily_cal || 1800);
  const [numMeals,  setNumMeals]  = useState(user.num_meals || 3);
  const [foodPref,  setFoodPref]  = useState(user.food_pref || "veg");

  // Password
  const [newPw,     setNewPw]     = useState("");
  const [confirmPw, setConfirmPw] = useState("");

  // Custom recipes
  const [customName,    setCustomName]    = useState("");
  const [customRecipes, setCustomRecipes] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const [s, cr] = await Promise.all([getSettings(), getCustomRecipes()]);
        setSettings(s);
        setCustomRecipes(cr || []);
        if (s?.user) {
          setDailyCal(s.user.daily_cal);
          setNumMeals(s.user.num_meals);
          setFoodPref(s.user.food_pref);
        }
      } catch(e) { console.error(e); }
      finally { setLoading(false); }
    }
    load();
  }, []);

  function notify(type, text) {
    setMsg({ type, text });
    setTimeout(() => setMsg({ type: "", text: "" }), 3000);
  }

  async function handleProfile(e) {
    e.preventDefault();
    setSaving("profile");
    try {
      await saveProfile({ daily_cal: Number(dailyCal),
                          num_meals: Number(numMeals), food_pref: foodPref });
      const updated = { ...user, daily_cal: Number(dailyCal),
                        num_meals: Number(numMeals), food_pref: foodPref };
      setStoredUser(updated);
      setUser(updated);
      notify("success", "Profile saved.");
    } catch(e) { notify("error", e?.detail || "Save failed"); }
    finally { setSaving(""); }
  }

  async function handlePassword(e) {
    e.preventDefault();
    if (newPw !== confirmPw) { notify("error", "Passwords don't match."); return; }
    if (newPw.length < 6)    { notify("error", "Password must be ≥ 6 characters."); return; }
    setSaving("password");
    try {
      await changePassword(newPw);
      setNewPw(""); setConfirmPw("");
      notify("success", "Password updated.");
    } catch(e) { notify("error", e?.detail || "Failed"); }
    finally { setSaving(""); }
  }

  async function handleAddCustom(e) {
    e.preventDefault();
    if (!customName.trim()) return;
    setSaving("custom");
    try {
      await addCustomRecipe(customName.trim());
      setCustomName("");
      const updated = await getCustomRecipes();
      setCustomRecipes(updated || []);
      notify("success", "Request submitted. It will be filled overnight.");
    } catch(e) { notify("error", e?.detail || "Failed"); }
    finally { setSaving(""); }
  }

  if (loading) return <div className="page loading-center"><span className="spinner" /></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <button className="btn btn-secondary"
                style={{ padding: "8px 14px", fontSize: 13 }}
                onClick={onLogout}>
          Log out
        </button>
      </div>

      {msg.text && (
        <div className={`alert alert-${msg.type === "success" ? "success" : "error"}`}>
          {msg.text}
        </div>
      )}

      {/* Profile */}
      <div className="section-header">Profile</div>
      <div className="card">
        <form onSubmit={handleProfile}>
          <div className="form-group">
            <label className="form-label">Daily calorie goal</label>
            <input className="form-input" type="number" min="1000" max="5000" step="50"
                   value={dailyCal} onChange={e => setDailyCal(e.target.value)} />
          </div>

          <div className="form-group">
            <label className="form-label">Meals per day</label>
            <div style={{ display: "flex", gap: 6 }}>
              {[2,3,4,5].map(n => (
                <button key={n} type="button"
                        style={{
                          flex: 1, padding: "8px 0", borderRadius: 8,
                          border: numMeals === n
                            ? "2px solid var(--green-deep)"
                            : "1.5px solid var(--linen-dark)",
                          background: numMeals === n ? "var(--green-deep)" : "white",
                          color: numMeals === n ? "white" : "var(--text)",
                          fontWeight: 600, fontSize: 14, cursor: "pointer",
                        }}
                        onClick={() => setNumMeals(n)}>
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Food preference</label>
            <select className="form-select" value={foodPref}
                    onChange={e => setFoodPref(e.target.value)}>
              {FOOD_PREFS.map(f => (
                <option key={f.val} value={f.val}>{f.label}</option>
              ))}
            </select>
          </div>

          <button className="btn btn-primary btn-full" type="submit"
                  disabled={saving === "profile"}>
            {saving === "profile" ? <span className="spinner" /> : "Save profile"}
          </button>
        </form>
      </div>

      {/* Password */}
      <div className="section-header">Change Password</div>
      <div className="card">
        <form onSubmit={handlePassword}>
          <div className="form-group">
            <label className="form-label">New password</label>
            <input className="form-input" type="password" value={newPw}
                   onChange={e => setNewPw(e.target.value)} minLength={6} />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm password</label>
            <input className="form-input" type="password" value={confirmPw}
                   onChange={e => setConfirmPw(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-full" type="submit"
                  disabled={!newPw || saving === "password"}>
            {saving === "password" ? <span className="spinner" /> : "Update password"}
          </button>
        </form>
      </div>

      {/* Custom recipe requests */}
      <div className="section-header">Request a Recipe</div>
      <div className="card">
        <form onSubmit={handleAddCustom} style={{ display: "flex", gap: 8 }}>
          <input className="form-input" style={{ flex: 1 }}
                 placeholder="Recipe name (e.g. Oats Upma)"
                 value={customName} onChange={e => setCustomName(e.target.value)} />
          <button className="btn btn-primary" type="submit"
                  disabled={!customName.trim() || saving === "custom"}>
            {saving === "custom" ? <span className="spinner" /> : "Request"}
          </button>
        </form>

        {customRecipes.length > 0 && (
          <div style={{ marginTop: 14 }}>
            {customRecipes.map((r, i) => (
              <div key={i} style={{
                display: "flex", justifyContent: "space-between",
                alignItems: "center", padding: "6px 0",
                borderBottom: i < customRecipes.length - 1
                  ? "1px solid var(--linen-dark)" : "none",
              }}>
                <span style={{ fontSize: 14 }}>{r.name}</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: "2px 8px",
                  borderRadius: 99,
                  background: r.status === "filled" ? "#d1fae5"
                            : r.status === "rejected" ? "#fee2e2" : "#fef3c7",
                  color: r.status === "filled" ? "#065f46"
                       : r.status === "rejected" ? "#dc2626" : "#92400e",
                }}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
