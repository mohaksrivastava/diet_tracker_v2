-- ============================================================
-- migration_v2_optimizer.sql
-- Run ONCE in Supabase SQL Editor after the initial setup_db.sql
-- All changes are ADDITIVE — existing app keeps working during migration
-- ============================================================

-- ── 1. New columns on recipes ─────────────────────────────────────────────────
ALTER TABLE recipes
  ADD COLUMN IF NOT EXISTS portion_min     REAL DEFAULT 0.5,
  ADD COLUMN IF NOT EXISTS portion_max     REAL DEFAULT 1.5,
  ADD COLUMN IF NOT EXISTS portion_typical REAL DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS role            TEXT DEFAULT 'side',
  ADD COLUMN IF NOT EXISTS cuisine         TEXT DEFAULT 'unknown';

-- Constrain valid values (permissive defaults keep all existing rows valid)
ALTER TABLE recipes
  DROP CONSTRAINT IF EXISTS role_valid,
  ADD  CONSTRAINT role_valid CHECK (role IN (
    'anchor_protein', 'anchor_starch', 'anchor_veg',
    'complete_meal', 'side', 'beverage'
  ));

ALTER TABLE recipes
  DROP CONSTRAINT IF EXISTS cuisine_valid,
  ADD  CONSTRAINT cuisine_valid CHECK (cuisine IN (
    'north_indian', 'south_indian', 'indo_chinese',
    'east_asian', 'continental', 'mediterranean',
    'mexican', 'unknown'
  ));

-- ── 2. Same columns on custom_recipes (AI fill will populate them) ────────────
ALTER TABLE custom_recipes
  ADD COLUMN IF NOT EXISTS portion_min     REAL DEFAULT 0.5,
  ADD COLUMN IF NOT EXISTS portion_max     REAL DEFAULT 1.5,
  ADD COLUMN IF NOT EXISTS portion_typical REAL DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS role            TEXT DEFAULT 'side',
  ADD COLUMN IF NOT EXISTS cuisine         TEXT DEFAULT 'unknown';

-- ── 3. Per-user nutrition targets ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nutrition_targets (
  user_id           INTEGER  PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  -- Daily gram targets
  cal_target        INTEGER  NOT NULL,
  protein_g         REAL     NOT NULL,
  fat_g             REAL     NOT NULL,
  carb_g            REAL     NOT NULL,
  fiber_g           REAL     NOT NULL DEFAULT 30,
  -- Soft band: zero penalty inside this range (fraction of target)
  cal_soft_pct      REAL     DEFAULT 0.08,
  protein_soft_lo   REAL     DEFAULT 0.05,
  fat_soft_hi       REAL     DEFAULT 0.10,
  carb_soft_pct     REAL     DEFAULT 0.15,
  fiber_soft_lo     REAL     DEFAULT 0.10,
  -- Hard limit: outside this the candidate is rejected
  cal_hard_pct      REAL     DEFAULT 0.20,
  protein_hard_lo   REAL     DEFAULT 0.20,
  fat_hard_hi       REAL     DEFAULT 0.25,
  fat_hard_lo       REAL     DEFAULT 0.30,
  carb_hard_pct     REAL     DEFAULT 0.35,
  fiber_hard_lo     REAL     DEFAULT 0.30,
  -- Penalty weights (tune these to change optimizer behaviour)
  k_cal             INTEGER  DEFAULT 1000,
  k_protein_under   INTEGER  DEFAULT 2000,
  k_fat_over        INTEGER  DEFAULT 1500,
  k_carb            INTEGER  DEFAULT 400,
  k_fiber_under     INTEGER  DEFAULT 800,
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── 4. Seed default targets for all existing users ────────────────────────────
-- 40 % protein · 40 % carb · 20 % fat
INSERT INTO nutrition_targets
  (user_id, cal_target, protein_g, fat_g, carb_g, fiber_g)
SELECT
  id,
  daily_cal,
  ROUND((daily_cal * 0.40 / 4.0)::numeric, 1),
  ROUND((daily_cal * 0.20 / 9.0)::numeric, 1),
  ROUND((daily_cal * 0.40 / 4.0)::numeric, 1),
  30
FROM users
ON CONFLICT (user_id) DO NOTHING;

-- ── 5. Pairing graph (Phase 7 — table created now, populated later) ───────────
CREATE TABLE IF NOT EXISTS recipe_pairings (
  recipe_a_id  INTEGER  REFERENCES recipes(id) ON DELETE CASCADE,
  recipe_b_id  INTEGER  REFERENCES recipes(id) ON DELETE CASCADE,
  affinity     REAL     NOT NULL,
  source       TEXT     NOT NULL CHECK (source IN ('curated', 'co_log', 'cuisine_cluster')),
  updated_at   TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY  (recipe_a_id, recipe_b_id),
  CHECK        (recipe_a_id < recipe_b_id)
);
CREATE INDEX IF NOT EXISTS idx_pairings_a ON recipe_pairings(recipe_a_id);
CREATE INDEX IF NOT EXISTS idx_pairings_b ON recipe_pairings(recipe_b_id);

-- ── 6. Optimizer run log (for production tuning — Phase 9) ───────────────────
CREATE TABLE IF NOT EXISTS optimizer_log (
  id                SERIAL      PRIMARY KEY,
  user_id           INTEGER     REFERENCES users(id) ON DELETE CASCADE,
  ran_at            TIMESTAMPTZ DEFAULT NOW(),
  k_meals           INTEGER,
  num_candidates    INTEGER,
  num_feasible      INTEGER,
  relaxation_level  TEXT,
  runtime_ms        INTEGER,
  food_pref         TEXT
);

-- ── 7. Verify ─────────────────────────────────────────────────────────────────
SELECT
  (SELECT COUNT(*) FROM nutrition_targets)  AS nutrition_targets_rows,
  (SELECT COUNT(*) FROM recipes
   WHERE role IS NOT NULL)                  AS recipes_with_role,
  (SELECT COUNT(*) FROM recipe_pairings)    AS pairing_rows;
