# Indian Diet Tracker — Python/Streamlit

Personalised multi-user Indian meal planning and logging app.
Deployed free on Hugging Face Spaces. AI recipe fill + diet nudges run
overnight via Windows Task Scheduler on a local machine.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit (Python) |
| Hosting | Hugging Face Spaces (free, always-on) |
| Database | Supabase PostgreSQL |
| DB client | psycopg2 |
| Auth | bcrypt (password hash in DB) |
| Optimiser | Pure NumPy (slot-based, vectorised) |
| AI — Recipe Fill | Ollama (local, 02:00 cron) |
| AI — Diet Nudges | Ollama (local, 04:00 cron) |
| Cron | Windows Task Scheduler + .bat files |

---

## One-time Setup (do this in order)

### 1. Supabase — create the schema

1. Log in to [supabase.com](https://supabase.com) → open your project
2. SQL Editor → New Query → paste `setup/setup_db.sql` → Run
3. Note your **Session Pooler** host: Settings → Database → Session mode
   (`aws-0-XX.pooler.supabase.com`)
4. Note your **user**: `postgres.your_project_ref`
5. Note your **password**: Settings → Database → Database Password

### 2. Local Python environment

```bash
cd diet_tracker_py
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env — fill in SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASS
```

### 4. Seed the database

Edit `data/seed_recipes.py` → update the `USERS` list with real names
and passwords. Copy `recipes.csv` and `recipe_details.csv` from your
R project into the `data/` folder, then:

```bash
python data/seed_recipes.py
```

Expected output:
```
✓ Mohak
✓ User2
✓ User3
✓ 83 recipes inserted/updated
✓ Details inserted
```

### 5. Test locally

```bash
streamlit run app.py
```

Open http://localhost:8501 — log in with one of the seeded usernames
and passwords. Verify plan generation, logging, and settings work.

---

## Deploy to Hugging Face Spaces

### Step 1 — Create the Space

1. Go to [huggingface.co](https://huggingface.co) → New Space
2. Space SDK: **Streamlit**
3. Visibility: **Public** (required for free tier; protected by login)
4. Hardware: **CPU basic** (free)

### Step 2 — Push the code

```bash
# Install Git LFS if not already installed
git lfs install

# Clone the empty Space repo (replace with your Space URL)
git clone https://huggingface.co/spaces/your-username/diet-tracker

# Copy all project files into it
cp -r diet_tracker_py/. diet-tracker/

# Commit and push
cd diet-tracker
git add .
git commit -m "Initial deployment"
git push
```

### Step 3 — Set Secrets

In the Space settings → **Secrets** tab → add:

| Name | Value |
|------|-------|
| `SUPABASE_HOST` | your pooler hostname |
| `SUPABASE_USER` | `postgres.your_project_ref` |
| `SUPABASE_PASS` | your database password |

### Step 4 — Verify

The Space builds automatically after each push (takes ~2 minutes).
Visit your Space URL → log in → generate a plan → confirm it works.

**Note:** `data/recipes.csv` and `data/recipe_details.csv` do **not**
need to be in the HF repo — all data is read from Supabase at runtime.
You can add them to `.gitignore`.

---

## Windows Task Scheduler — Cron Jobs

Both cron jobs run on your local Dell Precision. The machine must be
on (not sleeping) at the scheduled times.

### Prevent sleep at night

Control Panel → Power Options → Change plan settings → set
"Put the computer to sleep" to **Never** (or use a scheduled task to
wake the PC before 02:00 using Wake Timer).

### Create the 02:00 Recipe Fill task

1. Open **Task Scheduler** → Create Basic Task
2. Name: `DietTracker — Fill Recipes`
3. Trigger: **Daily** at **02:00**
4. Action: **Start a program**
   - Program: `D:\path\to\diet_tracker_py\venv\Scripts\python.exe`
   - Arguments: `D:\path\to\diet_tracker_py\schedulers\fill_recipes.py`
   - Start in: `D:\path\to\diet_tracker_py`
5. Finish → open Properties → General tab → check
   **"Run whether user is logged on or not"**
6. Conditions tab → uncheck **"Start only if computer is on AC power"**
   if you're on a laptop

Or use the `.bat` file approach — edit the path in
`schedulers/fill_recipes.bat`, then set that as the program.

### Create the 04:00 Nudge task

Repeat the above with:
- Name: `DietTracker — Generate Nudges`
- Time: **04:00**
- Script: `schedulers/generate_nudges.py` (or `generate_nudges.bat`)

### Logs

Both scripts write to `logs/` in the project root:
```
logs/fill_recipes_202506.log
logs/generate_nudges_202506.log
```

---

## Ollama Setup

The AI agents use Ollama running locally on the Dell Precision.

```bash
# Download and install Ollama from https://ollama.com

# Pull the model (once):
ollama pull qwen2.5:7b

# Verify it works:
ollama run qwen2.5:7b "What are the macros in dal tadka?"
```

The agents default to `qwen2.5:7b`. To use a different model,
change the `MODEL` constant at the top of:
- `agents/recipe_fill_agent.py`
- `agents/nudge_agent.py`

Larger models (14b, 32b) give better results for the nudge agent
if your RTX 500 Ada has enough VRAM.

---

## Updating the App

After code changes:

```bash
cd diet-tracker        # your local HF Space clone
git add .
git commit -m "your change"
git push               # Space rebuilds automatically
```

After recipe data changes (new rows in recipes.csv):

```bash
python data/seed_recipes.py    # re-seeds; uses ON CONFLICT UPDATE
```

No DB schema changes needed for recipe additions.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `could not connect to server` | Check SUPABASE_* secrets in HF Space settings |
| `No recipes found for slot` | Run `seed_recipes.py`; check `recipes` table has rows |
| `ollama: connection refused` | Start Ollama: `ollama serve` |
| Plan page crashes on generate | Check `food_pref` column exists in `users` table |
| Nudge not showing | Check `logs/generate_nudges_*.log` for errors |
| HF Space won't build | Check `requirements.txt` for typos; check Space logs |
