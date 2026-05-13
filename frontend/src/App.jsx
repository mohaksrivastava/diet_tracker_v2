import { useState, useEffect, Component } from "react";
import "./style.css";
import { getStoredUser, clearToken, getToken } from "./api.js";
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";
import Plan from "./pages/Plan.jsx";
import Log from "./pages/Log.jsx";
import Diary from "./pages/Diary.jsx";
import Nudges from "./pages/Nudges.jsx";
import Settings from "./pages/Settings.jsx";

class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) {
      return (
        <div className="page" style={{ paddingTop: 40 }}>
          <div className="alert alert-error" style={{ marginBottom: 16 }}>
            Something went wrong: {this.state.error.message}
          </div>
          <button className="btn btn-secondary btn-full"
                  onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const TABS = [
  { id: "home",     label: "Home",   icon: "🏠" },
  { id: "plan",     label: "Plan",   icon: "🗓️" },
  { id: "log",      label: "",       icon: "+" },
  { id: "diary",    label: "Diary",  icon: "📖" },
  { id: "nudges",   label: "Nudges", icon: "🔔" },
  { id: "settings", label: "Me",     icon: "⚙️" },
];

function App() {
  const [user, setUser]             = useState(null);
  const [page, setPage]             = useState("home");
  const [nudgeCount, setNudgeCount] = useState(0);

  useEffect(() => {
    const stored = getStoredUser();
    const token  = getToken();
    // Only restore session if both user object and token exist
    if (stored && token) setUser(stored);
    else {
      // Clear any partial/stale state
      clearToken();
      localStorage.removeItem("user");
    }
  }, []);

  function handleLogin(userData) {
    setUser(userData);
    setPage("home");
  }

  function handleLogout() {
    clearToken();
    localStorage.removeItem("user");
    setUser(null);
    setPage("home");
  }

  if (!user) return <Login onLogin={handleLogin} />;

  const pages = { home: Home, plan: Plan, log: Log, diary: Diary,
                  nudges: Nudges, settings: Settings };
  const PageComponent = pages[page] || Home;

  return (
    <>
      <ErrorBoundary key={page}>
        <PageComponent
          user={user}
          setUser={setUser}
          setPage={setPage}
          onLogout={handleLogout}
          onNudgeCount={setNudgeCount}
        />
      </ErrorBoundary>

      <nav className="tab-bar">
        {TABS.map((tab) => {
          if (tab.id === "log") {
            return (
              <button key="log" className="fab" onClick={() => setPage("log")}
                      aria-label="Log a meal">
                +
              </button>
            );
          }
          return (
            <button
              key={tab.id}
              className={`tab-item ${page === tab.id ? "active" : ""}`}
              onClick={() => setPage(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span>
                {tab.label}
                {tab.id === "nudges" && nudgeCount > 0 ? ` (${nudgeCount})` : ""}
              </span>
            </button>
          );
        })}
      </nav>
    </>
  );
}

export default App;
