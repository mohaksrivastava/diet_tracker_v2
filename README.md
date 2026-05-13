---
title: Call Bhaiya
emoji: 🔥
colorFrom: green
colorTo: green
sdk: streamlit
sdk_version: 1.45.0
app_file: app.py
python_version: "3.12"
pinned: false
---

# Call Bhaiya — Diet Tracker

Personalised multi-user meal planning and logging app for managing daily nutrition.

**Live app:** [call-bhaiya.netlify.app](https://call-bhaiya.netlify.app)

---

## Current Architecture

```
Netlify (React/Vite)                HF Space: diet_tracker_api         Supabase
  call-bhaiya.netlify.app  ──HTTPS──►  mohaksrivastava2912-             ──► PostgreSQL
  localStorage JWT                      diet-tracker-api.hf.space
                                        (FastAPI, Docker SDK)

Local Windows Machine
  schedulers/ → agents/ → Ollama → writes nudges + recipe fills → Supabase
```

The app originally ran as a Streamlit single-file app (`app.py`) on HF Spaces. It has been fully migrated to a **FastAPI backend + React/Vite frontend** for proper mobile layout and performance. The old Streamlit app remains deployed as a fallback.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, deployed on Netlify |
| Backend API | FastAPI (Python), Docker on HF Spaces |
| Database | Supabase PostgreSQL |
| Auth | JWT Bearer tokens (python-jose), bcrypt passwords |
| Optimiser | Pure NumPy slot-based vectorised meal optimizer |
| AI — Recipe Fill | Ollama (local, 02:00 cron) |
| AI — Diet Nudges | Ollama (local, 04:00 cron) |
| Cron | Windows Task Scheduler + Python scripts |
| Legacy UI | Streamlit (still live at old HF Space) |

---

## Repository Layout

```
diet_tracker_v2/
├── app.py                  ← Legacy Streamlit app (still live, do not touch)
├── requirements.txt        ← Streamlit deps (legacy)
├── netlify.toml            ← Netlify build config (base=frontend, publish=dist)
├── db/                     ← Shared DB query modules
│   ├── connection.py
│   ├── logs.py
│   ├── nudges.py
│   ├── nutrition_targets.py
│   ├── recipes.py
│   └── users.py
├── optimizer/
│   └── meal_optimizer.py   ← NumPy slot-based meal optimizer (v4)
├── agents/
│   ├── recipe_fill_agent.py
│   └── nudge_agent.py
├── schedulers/
│   ├── fill_recipes.py
│   └── generate_nudges.py
├── data/
│   └── seed_recipes.py
└── frontend/               ← React/Vite app (deployed to Netlify)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx         ← Auth state, tab bar routing, error boundary
        ├── api.js          ← All fetch() calls + JWT token handling
        ├── style.css       ← Design system (DM Sans, green palette)
        └── pages/
            ├── Login.jsx
            ├── Home.jsx    ← Dashboard: today's macros, 7-day bar chart, streak
            ├── Plan.jsx    ← Generate meal plans, edit portions, log all
            ├── Log.jsx     ← Quick-log a single meal
            ├── Diary.jsx   ← Browse/edit/delete logs by date
            ├── Nudges.jsx  ← AI nudges, mark as read
            └── Settings.jsx
```

The FastAPI backend lives in a separate repo (`diet_tracker_api`) deployed to Hugging Face Spaces.

---

## Features

### Home Dashboard
- Today's calorie count vs daily target with remaining kcal
- Macro progress bars — Protein / Carbs / Fat
- **7-day performance bar chart** (pure SVG, no library) with dotted target line
- Streak counter and 7-day average kcal
- Latest AI nudge preview

### Meal Plan Generator
- NumPy slot-based optimizer selects optimal recipe combinations
- **Calorie slider** (1000–3500 kcal) to override daily target per session
- Meals/day selector (2–5 meals)
- Food preference filter (Vegan / Vegetarian / Dairy / Egg / Non-veg)
- **Cuisine filter** (Any, North Indian, South Indian, Continental, etc.)
- Up to 3 ranked plan options shown as tabs
- **Portion steppers** (±0.25×) per recipe with live macro recalculation
- **Add / remove recipes** from any slot inline
- Click any recipe name → **cooking instructions modal** (ingredients + steps)
- Gap filler recipes (★) automatically added to close macro deficits
- "Log all meals for today" — one tap logs the entire plan to the diary

### Food Diary
- Browse logs by date with a calendar picker
- Edit calories/macros inline, delete individual entries
- Add custom meals for any date

### AI Nudges
- Overnight-generated personalised diet feedback via Ollama LLM
- Unread badge on tab bar
- Mark individual nudges as read

### Settings
- Update daily calorie target, meals/day, food preference
- Fine-tune nutrition targets (macro grams + optimizer penalty weights)
- Change password
- Request custom recipes (status: pending / filled / rejected)

---

## Optimizer — How It Works

`optimizer/meal_optimizer.py` (v4) uses a three-phase approach:

**Phase 1 — Slot candidates:** For each meal slot (lunch, dinner, breakfast, snack), generates all valid recipe combinations within ±30% of the slot's calorie target. Enforces anchor rules: lunch/dinner must include an `anchor_protein` + `anchor_starch` pair, or a single `complete_meal`.

**Phase 2 — Global search:** Vectorised NumPy meshgrid enumerates all slot combinations. Scores each by macro penalty + cuisine coherence + portion deviation + anchor pair bonus. Applies hard feasibility constraints with 4 relaxation levels (strict → soft_only). Returns top 3 diverse plans.

**Phase 3 — Gap filler:** If a protein or carb/fat deficit remains after Phase 2, inserts a `gap_filler` recipe (e.g., protein shake, fruit) into the last slot.

**Protein-first scoring:** The penalty function uses a high `k_protein_under = 3000` coefficient and a softened over-protein penalty (`kp/8`) to strongly favour meeting protein targets before fat/carbs. The gap filler also prioritises protein deficit first.

---

## API Endpoints

All auth-protected endpoints require `Authorization: Bearer <token>`.

```
POST  /auth/login           {username, password} → {token, user}
GET   /recipes              → all recipes list
GET   /recipes/{name}/detail
GET   /recipes/custom       auth → user's custom recipe requests
POST  /recipes/custom       auth {name}
POST  /optimizer/run        auth {num_meals, food_pref, target_cal,
                                  nutrition_target, cuisine_filter?}
GET   /logs?date_str=       auth → day's meal logs
GET   /logs/week            auth → 7-day summary
GET   /logs/streak          auth → {streak: int}
POST  /logs                 auth {log_date, recipe_name, meal_type, ...}
PUT   /logs/{id}            auth
DELETE /logs/{id}           auth
GET   /nudges               auth → AI nudge list
PUT   /nudges/{id}/seen     auth
GET   /settings             auth → {user, nutrition_target}
PUT   /settings/profile     auth
PUT   /settings/targets     auth
PUT   /settings/password    auth
GET   /health
```

---

## Environment Variables

### HF Space (`diet_tracker_api`) — Secrets tab:
| Variable | Description |
|---|---|
| `SUPABASE_HOST` | Supabase Session Pooler hostname |
| `SUPABASE_USER` | `postgres.{project_ref}` |
| `SUPABASE_PASS` | Database password |
| `JWT_SECRET` | Long random string for signing JWTs |

### Netlify (`call-bhaiya`) — Environment variables:
| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://mohaksrivastava2912-diet-tracker-api.hf.space` |

### Local `.env` (for legacy Streamlit and cron jobs):
```
SUPABASE_HOST=...
SUPABASE_USER=...
SUPABASE_PASS=...
```

---

## Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set API URL for local dev
echo "VITE_API_URL=https://mohaksrivastava2912-diet-tracker-api.hf.space" > .env.local

# Start dev server
npm run dev
# → http://localhost:5173

# Production build
npm run build
```

Netlify auto-deploys from the `master` branch of this repo whenever changes are pushed to the `github` remote. `VITE_API_URL` is baked into the JS bundle at build time by Vite.

---

## Database Schema

Key tables (do not modify schema):

| Table | Purpose |
|---|---|
| `users` | id, name, password_hash (bcrypt), daily_cal, num_meals, food_pref |
| `recipes` | name, category, meal_type, food_type, calories, protein, carbohydrate, fat, portion_min/typical/max, role, cuisine |
| `custom_recipes` | user requests (pending / filled / rejected) |
| `meal_logs` | user_id, log_date (DATE), recipe_name, meal_type, macros, logged_at (TIMESTAMPTZ) |
| `nudges` | user_id, nudge_text, generated_on, days_analyzed, seen |
| `nutrition_targets` | per-user macro targets + optimizer penalty weights |

**Two-timestamp design in `meal_logs`:**
- `log_date DATE` — the date the meal was *eaten* (user-controlled; used in all queries)
- `logged_at TIMESTAMPTZ` — when the row was inserted (system-controlled; ordering only)

Always filter/group by `log_date`, never `logged_at`.

---

## Seeding the Database

```bash
# Activate venv
venv\Scripts\activate

# Seed recipes (safe to re-run; uses ON CONFLICT UPDATE)
python data/seed_recipes.py
```

---

## Cron Jobs (Windows Task Scheduler)

Both jobs run on the local Windows machine. The machine must be on at the scheduled times.

| Job | Script | Time |
|---|---|---|
| Recipe fill | `schedulers/fill_recipes.py` | 02:00 |
| Nudge generation | `schedulers/generate_nudges.py` | 04:00 |

Both agents use Ollama locally (`qwen2.5:7b` by default). To run manually:
```bash
ollama serve
python schedulers/generate_nudges.py
```

Logs are written to `logs/` in the project root.

---

## Git Remotes

```
origin  → https://huggingface.co/spaces/mohak-srivastava/diet-tracker  (legacy Streamlit)
github  → https://github.com/mohaksrivastava/diet_tracker_v2           (Netlify source)
```

Push frontend/backend changes to GitHub (triggers Netlify deploy):
```bash
git push github master
```

The FastAPI backend (`diet_tracker_api`) is a separate repo:
```
https://huggingface.co/spaces/mohaksrivastava2912/diet_tracker_api
```

---

## Design System

```css
--green-deep:  #1D4A2F   /* primary buttons, headings */
--green-mid:   #2D6A4F   /* hover states */
--green-light: #52B788   /* accents, chart bars */
--linen:       #F0EFE9   /* page background */
--linen-dark:  #E8E6DE   /* card borders */
--breakfast:   #FF6B35
--lunch:       #43A047
--snack:       #E91E8C
--dinner:      #3D5AF1
```

Fonts: DM Sans (body) + DM Serif Display (headings) via Google Fonts.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Plan page spinner on load | HF Space is cold-starting — wait up to 15s; form appears with defaults |
| "Failed to generate plan" | Check HF Space at `/docs`; verify all 4 secrets are set |
| Login loops back to login page | Clear localStorage: DevTools → Application → Local Storage → Clear |
| Blank white screen | An error boundary message should appear; if not, check browser console |
| `No eligible recipes` | Check `food_pref` filter; ensure recipes table has correct `food_type` values |
| Nudge not showing | Check `logs/generate_nudges_*.log`; verify Ollama was running at 04:00 |
| Recipes dropdown empty in Plan | HF Space cold start — wait a few seconds and the list will populate |
| `could not connect to server` | Check Supabase secrets in HF Space settings |
