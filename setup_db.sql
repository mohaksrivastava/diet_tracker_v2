-- ============================================================
-- Diet Tracker v2 – Complete Database Schema
-- Run ONCE in the Supabase SQL Editor (New Query → paste → Run)
-- ============================================================

-- ── 1. Users ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id            SERIAL      PRIMARY KEY,
  name          TEXT        UNIQUE NOT NULL,
  password_hash TEXT        NOT NULL,
  daily_cal     INTEGER     NOT NULL DEFAULT 1800,
  num_meals     INTEGER     NOT NULL DEFAULT 3,
  food_pref     TEXT        NOT NULL DEFAULT 'veg'
    CHECK (food_pref IN ('vegan','veg','dairy','egg','non-veg'))
);

-- ── 2. Recipes (migrated from CSV via seed_recipes.py) ────────
CREATE TABLE IF NOT EXISTS recipes (
  id             SERIAL  PRIMARY KEY,
  name           TEXT    UNIQUE NOT NULL,
  category       TEXT    NOT NULL DEFAULT 'recipe'
    CHECK (category IN ('recipe','ingredient')),
  meal_type      TEXT,
  food_type      TEXT    CHECK (food_type IN ('vegan','veg','dairy','egg','non-veg')),
  food_group     TEXT,
  difficulty     TEXT    CHECK (difficulty IN ('Easy','Medium','Hard')),
  cook_time_mins INTEGER NOT NULL DEFAULT 0,
  calories       REAL,
  protein        REAL,
  carbohydrate   REAL,
  fat            REAL
);

CREATE TABLE IF NOT EXISTS recipe_details (
  id           SERIAL  PRIMARY KEY,
  recipe_id    INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
  serving_note TEXT,
  ingredients  TEXT,   -- pipe-delimited list
  steps        TEXT    -- pipe-delimited steps
);

-- ── 3. Custom recipes (user-submitted, AI-filled overnight) ───
CREATE TABLE IF NOT EXISTS custom_recipes (
  id             SERIAL      PRIMARY KEY,
  added_by       INTEGER     REFERENCES users(id) ON DELETE SET NULL,
  name           TEXT        NOT NULL,
  status         TEXT        NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','filled','rejected')),
  reject_reason  TEXT,
  category       TEXT        DEFAULT 'recipe',
  meal_type      TEXT,
  food_type      TEXT,
  food_group     TEXT,
  difficulty     TEXT,
  cook_time_mins INTEGER,
  calories       REAL,
  protein        REAL,
  carbohydrate   REAL,
  fat            REAL,
  serving_note   TEXT,
  ingredients    TEXT,
  steps          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  filled_at      TIMESTAMPTZ
);

-- ── 4. Meal logs ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS meal_logs (
  id           SERIAL      PRIMARY KEY,
  user_id      INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  log_date     DATE        NOT NULL DEFAULT CURRENT_DATE,
  recipe_name  TEXT        NOT NULL,
  meal_type    TEXT,
  calories     INTEGER,
  protein_g    REAL,
  carb_g       REAL,
  fat_g        REAL,
  logged_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_user_date ON meal_logs (user_id, log_date);

-- ── 5. Nudges (AI diet recommendations, shown on next login) ──
CREATE TABLE IF NOT EXISTS nudges (
  id             SERIAL      PRIMARY KEY,
  user_id        INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  generated_on   DATE        NOT NULL DEFAULT CURRENT_DATE,
  days_analyzed  INTEGER,
  adjusted_cal   REAL,
  adjusted_prot  REAL,
  adjusted_carb  REAL,
  adjusted_fat   REAL,
  nudge_text     TEXT        NOT NULL,
  seen           BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nudges_user ON nudges (user_id, seen);

-- ── 6. Migration: protein_hard_hi ────────────────────────────
ALTER TABLE nutrition_targets
  ADD COLUMN IF NOT EXISTS protein_hard_hi REAL DEFAULT 0.10;

UPDATE nutrition_targets
  SET protein_hard_lo = 0.10
  WHERE protein_hard_lo = 0.20;

-- ── 7. Verify ─────────────────────────────────────────────────
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
