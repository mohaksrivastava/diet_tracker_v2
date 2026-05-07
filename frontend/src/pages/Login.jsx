import { useState } from "react";
import { login, setToken, setStoredUser } from "../api.js";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username.trim(), password);
      setToken(data.token);
      setStoredUser(data.user);
      onLogin(data.user);
    } catch (err) {
      setError(err?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-logo">🥗 Call Bhaiya</div>
      <p className="login-tagline">Your personal diet tracker</p>

      <div className="login-card">
        <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 22,
                     color: "var(--green-deep)", marginBottom: 20 }}>
          Sign in
        </h2>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              className="form-input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Your name"
              required
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              required
              autoComplete="current-password"
            />
          </div>

          <button className="btn btn-primary btn-full" type="submit"
                  disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
