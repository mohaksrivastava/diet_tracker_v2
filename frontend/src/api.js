const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() { return localStorage.getItem("token"); }
export function setToken(t) { localStorage.setItem("token", t); }
export function clearToken() { localStorage.removeItem("token"); }
export function getStoredUser() {
  try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
}
export function setStoredUser(u) { localStorage.setItem("user", JSON.stringify(u)); }

async function req(path, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (res.status === 401) {
    // Always throw — let the caller decide what to do. Clear stale auth data.
    clearToken();
    localStorage.removeItem("user");
    const err = await res.json().catch(() => ({ detail: "Invalid credentials" }));
    throw err;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const login = (u, p) =>
  req("/auth/login", { method: "POST", body: JSON.stringify({ username: u, password: p }) });

export const getRecipes = () => req("/recipes");
export const getRecipeDetail = (name) => req(`/recipes/${encodeURIComponent(name)}/detail`);
export const addCustomRecipe = (name) =>
  req("/recipes/custom", { method: "POST", body: JSON.stringify({ name }) });
export const getCustomRecipes = () => req("/recipes/custom");

export const runOptimizer = (body) =>
  req("/optimizer/run", { method: "POST", body: JSON.stringify(body) });

export const getLogs = (dateStr) => req(`/logs?date_str=${dateStr}`);
export const getWeekLogs = () => req("/logs/week");
export const getStreak = () => req("/logs/streak");
export const addLog = (body) =>
  req("/logs", { method: "POST", body: JSON.stringify(body) });
export const updateLog = (id, body) =>
  req(`/logs/${id}`, { method: "PUT", body: JSON.stringify(body) });
export const deleteLog = (id) => req(`/logs/${id}`, { method: "DELETE" });

export const getNudges = () => req("/nudges");
export const markNudgeSeen = (id) => req(`/nudges/${id}/seen`, { method: "PUT" });

export const getSettings = () => req("/settings");
export const saveProfile = (body) =>
  req("/settings/profile", { method: "PUT", body: JSON.stringify(body) });
export const saveTargets = (body) =>
  req("/settings/targets", { method: "PUT", body: JSON.stringify(body) });
export const changePassword = (pw) =>
  req("/settings/password", { method: "PUT", body: JSON.stringify({ new_password: pw }) });
