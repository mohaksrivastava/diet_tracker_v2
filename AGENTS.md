# AGENTS.md — Indian Diet Tracker v2

> This file is for AI coding agents. It describes the project architecture, conventions, and runtime behaviour as actually implemented. If you change any of these areas, update this file.

---

## 1. Project Overview

Indian Diet Tracker is a personalised, multi-user meal-planning and food-logging web app focused on Indian cuisine. Users log in, generate optimised daily meal plans, log what they ate, and receive AI-generated diet nudges based on their recent history.

The app is a single Python/Streamlit monolith. It is deployed on **Hugging Face Spaces** (free CPU tier). Two AI features run **offline on a local Windows machine** via Windows Task Scheduler:

1. **Recipe Fill Agent** (~02:00 daily) — Uses a local Ollama LLM to fill nutritional details for user-submitted custom recipes.
2. **Nudge Agent** (~04:00 daily) — Uses a local Ollama LLM to generate personalised diet recommendations based on the last ≤5 days of meal logs.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| UI / App server | Streamlit (Python) |
| Hosting | Hugging Face Spaces |
| Database | Supabase PostgreSQL |
| DB driver | `psycopg2-binary` |
| Auth | `bcrypt` (password hash stored in DB) |
| Optimiser | Pure NumPy (slot-based, vectorised) |
| AI (local) | Ollama (`qwen2.5:7b` by default) |
| Task scheduling | Windows Task Scheduler |
| Environment | Python 3.x venv |

No build step (no `pyproject.toml`, `setup.py`, or `package.json`). Dependencies are listed flat in `requirements.txt`.

---

## 3. Repository Layout

```
diet_tracker_v2/
├── app.py                      # Streamlit entry point — all UI pages
├── requirements.txt            # Flat dependency list
├── .env                        # SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASS
├── setup_db.sql                # One-time schema for Supabase
├── seed_recipes.py             # One-time seed script (users + recipes CSVs)
│
├── db/                         # Database access layer
│   ├── connection.py           # psycopg2 connection + thin execute() helper
│   ├── users.py                # Auth (bcrypt) + user CRUD
│   ├── recipes.py              # Read/write recipes (base + custom)
│   ├── logs.py                 # Meal logging + history queries
│   └── nudges.py               # Diet recommendation storage
│
├── optimizer/
│   └── meal_optimizer.py       # NumPy slot-based plan optimiser
│
├── agents/                     # AI agents (require local Ollama)
│   ├── recipe_fill_agent.py    # Fills pending custom recipes via LLM
│   └── nudge_agent.py          # Generates personalised diet nudges via LLM
│
├── schedulers/                 # Windows Task Scheduler entry points
│   ├── fill_recipes.py         # 02:00 runner — calls recipe_fill_agent
│   └── generate_nudges.py      # 04:00 runner — calls nudge_agent
│
└── data/                       # Seed CSVs
    ├── recipes.csv             # Base recipe nutritional data
    ├── recipe_details.csv      # Ingredients & steps (pipe-delimited)
    └── seed_recipes.py         # Script that pushes CSVs into Supabase
```

**No test suite exists** in this project.

---

## 4. Build and Run Commands

### Local development

```bash
# 1. Create and activate venv
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — fill SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASS

# 4. Seed the database (one-time)
python data/seed_recipes.py

# 5. Run locally
streamlit run app.py
# → http://localhost:8501
```

### Running AI agents manually (requires local Ollama)

```bash
# Recipe fill
python agents/recipe_fill_agent.py

# Nudge generation
python agents/nudge_agent.py
```

### Deploy to Hugging Face Spaces

The Space uses the Streamlit SDK. Push the repo to the HF Space Git remote. The Space rebuilds automatically. Secrets (`SUPABASE_HOST`, `SUPABASE_USER`, `SUPABASE_PASS`) must be set in the Space Settings → Secrets tab.

`data/recipes.csv` and `data/recipe_details.csv` do **not** need to be in the HF repo — all runtime data comes from Supabase.

---

## 5. Environment Variables

Stored in `.env` (local) or HF Space Secrets (production):

| Variable | Purpose |
|----------|---------|
| `SUPABASE_HOST` | Supabase Session Pooler host |
| `SUPABASE_USER` | `postgres.your_project_ref` |
| `SUPABASE_PASS` | Database password |

`db/connection.py` loads these via `python-dotenv` and opens a psycopg2 connection with `sslmode="require"` and `RealDictCursor`.

---

## 6. Database Schema (Supabase)

Run `setup_db.sql` once in the Supabase SQL Editor.

| Table | Purpose |
|-------|---------|
| `users` | Credentials, calorie target, meals/day, food preference |
| `recipes` | Base recipe catalogue (migrated from CSV) |
| `recipe_details` | Ingredients & steps (pipe-delimited text), linked to `recipes` |
| `custom_recipes` | User-submitted recipes; status = `pending` → `filled` / `rejected` |
| `meal_logs` | Per-user per-day food log |
| `nudges` | AI-generated recommendations with `seen` flag |

Key constraints:
- `food_pref` ∈ `{vegan, veg, dairy, egg, non-veg}`
- `category` ∈ `{recipe, ingredient}`
- `difficulty` ∈ `{Easy, Medium, Hard}`
- `food_group` values are free but the optimiser and agents recognise a specific set (see `agents/recipe_fill_agent.py` and `optimizer/meal_optimizer.py`).

---

## 7. Code Style and Conventions

### Formatting
- 4-space indentation.
- Maximum line length ~100 characters (soft limit).
- Single quotes for short strings, double quotes for UI text and docstrings.

### Naming
- `lower_snake_case` for functions, variables, filenames.
- Modules are nouns (`users.py`, `meal_optimizer.py`).
- Agent entry functions are `run_<thing>()`.

### Section headers
Files use box-drawing characters for visual sections:
```python
# ── Section name ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
```
Maintain this style when adding new major sections.

### Imports
- Standard library first.
- Third-party next (`pandas`, `numpy`, `streamlit`, `ollama`).
- Local project modules last, grouped by layer (`db.*`, `optimizer.*`, `agents.*`).

### Database access pattern
Use the thin helper in `db/connection.py`:
```python
from db.connection import execute

# fetch one row
row = execute(conn, "SELECT ...", (param,), fetch="one")

# fetch many
rows = execute(conn, "SELECT ...", fetch="all")

# write (auto-commits)
execute(conn, "INSERT ...", (param,))
```
Always pass parameters as a tuple; never use f-strings for SQL values.

---

## 8. Key Modules — What You Need to Know

### `app.py` — UI
- Single-file Streamlit app with page dispatch via sidebar radio.
- Pages: Login → Get a Plan / Log a Meal / My Logs / Add Custom Recipe / Notifications / Settings.
- Uses `@st.cache_resource` for the DB connection and `@st.cache_data(ttl=300)` for recipes.
- Session state keys: `logged_in`, `user_id`, `username`, `user_data`, `plans`, `customize_state`.

### `optimizer/meal_optimizer.py` — Plan Generation
- Port of an original R algorithm.
- Generates up to 3 diverse meal plans given `K` meals/day, calorie target, and food preference.
- Scoring: `2·cal_pct² + (C%−40)² + (P%−40)² + (F%−20)² + extra_penalties`.
- Constraints: no duplicate food groups within a slot; non-staple recipes unique across slots; diversity filter so top 3 plans differ in ≥2 slots.
- **Important**: it operates on a pandas DataFrame of recipes. It expects columns `name`, `category`, `meal_type`, `food_type`, `food_group`, `difficulty`, `cook_time_mins`, `calories`, `protein`, `carbohydrate`, `fat`.

### `agents/recipe_fill_agent.py` — Custom Recipe AI Fill
- Queries `custom_recipes` with `status = 'pending'`.
- Fuzzy-deduplicates against existing recipe names (`difflib.SequenceMatcher`, threshold `0.85`).
- Calls Ollama with a strict JSON prompt.
- Validates response, normalises enums, clamps calories to `20–1200`, then writes back via `db.recipes.fill_custom_recipe()`.
- Model constant: `MODEL = "qwen2.5:7b"`.

### `agents/nudge_agent.py` — Diet Recommendation AI
- For each user with logged data:
  1. Fetches last ≤5 days of logs (days with zero entries are skipped).
  2. Computes rolling macro surplus/deficit and clamps adjustments to ±20% of baseline.
  3. Runs the optimiser with adjusted targets.
  4. Builds a rich prompt (history, deviations, adjusted targets, candidate plan, available recipe list) and calls Ollama.
  5. Stores the resulting text in `nudges`.
- Skips users who already have a nudge for today or who have no logged data at all.

---

## 9. Scheduler Architecture

The local machine (Windows) runs two scheduled tasks:

| Time | Script | Logs to |
|------|--------|---------|
| 02:00 | `schedulers/fill_recipes.py` | `logs/fill_recipes_YYYYMM.log` |
| 04:00 | `schedulers/generate_nudges.py` | `logs/generate_nudges_YYYYMM.log` |

Both scripts:
- Insert the project root into `sys.path` so imports resolve.
- Configure logging to both a month-stamped file in `logs/` and stdout.
- Call the agent’s `run_*()` function and log the result dict.

The machine must remain awake at night. If using a laptop, disable sleep in Power Options.

---

## 10. Security Considerations

- **Passwords**: Hashed with `bcrypt` (salted). Never store plaintext.
- **Database**: SSL required (`sslmode="require"`). Credentials live only in `.env` / HF Secrets.
- **SQL injection**: Mitigated by `psycopg2` parameterised queries. Do **not** use f-string interpolation for SQL values.
- **Custom recipe names**: Sanitised with `.strip()` before insertion, but not HTML-escaped. Streamlit handles HTML escaping in most widgets; the app does use `unsafe_allow_html=True` for styled cards and badges.
- **Ollama**: Runs locally; no external API keys are stored in the repo.
- **Deployment**: HF free tier requires Public visibility, but login protects user data. Do not commit `.env`.

---

## 11. Common Tasks for Agents

### Adding a new DB table
1. Add `CREATE TABLE IF NOT EXISTS` block to `setup_db.sql`.
2. Create a new module under `db/` (e.g., `db/new_thing.py`) following the `execute()` pattern.
3. Import and use it from `app.py` or the relevant agent.

### Adding a new UI page
1. Write a `new_page()` function in `app.py`.
2. Add the label to the sidebar `st.radio(...)` list in `main()`.
3. Add the label→function mapping in the `dispatch` dict.

### Changing the LLM model
Edit the `MODEL` constant at the top of:
- `agents/recipe_fill_agent.py`
- `agents/nudge_agent.py`

The model must be pulled in Ollama locally (`ollama pull <model>`).

### Updating base recipes
1. Edit `data/recipes.csv` and/or `data/recipe_details.csv`.
2. Run `python data/seed_recipes.py`.
   - It uses `ON CONFLICT (name) DO UPDATE`, so existing rows are overwritten.

### Seeding new users
Edit the `USERS` list in `data/seed_recipes.py` and re-run the script.

---

## 12. Troubleshooting Quick Reference

| Symptom | Likely Cause |
|---------|--------------|
| `could not connect to server` | Wrong `SUPABASE_*` env vars; or IP not allowed in Supabase |
| `No recipes found for slot` | `recipes` table empty → run `seed_recipes.py`; or food preference too restrictive |
| Plan page crashes on generate | `food_pref` column missing from `users` table → re-run `setup_db.sql` |
| `ollama: connection refused` | Ollama not running locally → `ollama serve` |
| Nudge not appearing | Check `logs/generate_nudges_*.log`; user may have no logged data |
| HF Space build fails | Check `requirements.txt` for typos; inspect Space build logs |

---

## 13. Important Notes

- **No tests exist.** If you add tests, create a `tests/` directory and document the runner command here.
- **Do not run `git commit` / `git push` unless explicitly asked.**
- **Data files are pipe-delimited** inside cells: `ingredients` and `steps` in `recipe_details.csv` use `|` as a separator.
- **The optimizer is CPU-intensive** for large recipe catalogues because it builds a full meshgrid of slot candidates. Keep `M_CANDS` modest or restrict candidate pools if performance degrades.
- **British English spelling** is used in user-facing copy (e.g. "optimising", "fibre"). Code and comments use American English spellings interchangeably; consistency is not strictly enforced.
