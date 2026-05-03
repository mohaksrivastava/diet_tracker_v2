# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> For deeper architecture detail, see `AGENTS.md`.

**App name:** Call Bhaiya (formerly "Indian Diet Tracker"). The app supports recipes from any cuisine — avoid "Indian-only" language in UI copy or AI prompts.

---

## Running the App

```bash
# Activate venv (Windows)
venv\Scripts\activate

# Run locally
streamlit run app.py
# → http://localhost:8501

# Re-seed recipes after CSV changes
python data/seed_recipes.py

# Run AI agents manually (requires local Ollama running: `ollama serve`)
python agents/recipe_fill_agent.py
python agents/nudge_agent.py
```

There is no build step, no linter configured. Tests live in `tests/` — run with `python -m pytest`.

---

## Architecture

Single-file Streamlit app (`app.py`) backed by Supabase PostgreSQL. All UI pages are Python functions dispatched from a sidebar radio widget in `main()`. State lives in `st.session_state`; the DB connection is `@st.cache_resource`; recipes are `@st.cache_data(ttl=300)`.

**Request flow for meal planning:**
1. User triggers "Generate Plans" → `app.py` calls `run_optimizer()` from `optimizer/meal_optimizer.py`
2. Optimizer returns up to 3 ranked plans stored in `st.session_state.plans`
3. User customises via `_customize_panel()` (inline portion/add/remove with `st.rerun()`)
4. "Log All" writes rows to `meal_logs` via `db/logs.py:log_meal()`

**Two-timestamp design in `meal_logs`:**
- `log_date DATE` — the date the meal was *eaten* (user-controlled; used in all queries and grouping)
- `logged_at TIMESTAMPTZ DEFAULT NOW()` — when the row was inserted (system-controlled; used only for ordering within a day)

Always query/group by `log_date`, never `logged_at`.

**Offline AI jobs** (require local Ollama on the Windows machine, not on HF Spaces):
- `schedulers/fill_recipes.py` → `agents/recipe_fill_agent.py` at 02:00
- `schedulers/generate_nudges.py` → `agents/nudge_agent.py` at 04:00

---

## Database Access Pattern

All DB calls go through `db/connection.py:execute()`. Never use f-strings for SQL values.

```python
from db.connection import execute

rows = execute(conn, "SELECT ... WHERE user_id = %s", (user_id,), fetch="all")
row  = execute(conn, "SELECT ... WHERE id = %s",      (id,),      fetch="one")
execute(conn, "INSERT INTO ...", (val1, val2))  # auto-commits
```

Add new tables to `setup_db.sql` and new query modules under `db/`.

---

## Adding a New UI Page

1. Write `def new_page():` in `app.py`
2. Add its label to the `st.radio(...)` list in `main()`
3. Add label → function to the dispatch dict in `main()`

---

## Key Constants and Enums

```python
# app.py
PORTIONS   = {"0.5×": 0.5, "1×": 1.0, "1.5×": 1.5, "2×": 2.0}
SLOT_LABELS = {"lunch": "Lunch", "dinner": "Dinner", "breakfast": "Breakfast", "snack": "Snack"}

# DB-enforced enums
food_pref  : vegan | veg | dairy | egg | non-veg
category   : recipe | ingredient
difficulty : Easy | Medium | Hard
```

---

## Code Style

- 4-space indent, ~100 char soft line limit
- Single quotes for short strings, double quotes for UI text
- Section headers use `# ── Name ──` and `# ═══` box-drawing characters — maintain when adding new sections
- Import order: stdlib → third-party → local (`db.*`, `optimizer.*`, `agents.*`)

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `SUPABASE_HOST` | Supabase Session Pooler host |
| `SUPABASE_USER` | `postgres.your_project_ref` |
| `SUPABASE_PASS` | Database password |

Loaded from `.env` locally via `python-dotenv`; set as Secrets in HF Space for production.
