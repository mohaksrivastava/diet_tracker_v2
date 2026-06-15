-- ── Fiber tracking migration ─────────────────────────────────────────────────
-- Idempotent: safe to re-run on any environment.
-- Run in Supabase SQL Editor after setup_db.sql.

ALTER TABLE recipes
  ADD COLUMN IF NOT EXISTS fiber REAL;

ALTER TABLE custom_recipes
  ADD COLUMN IF NOT EXISTS fiber REAL;

ALTER TABLE meal_logs
  ADD COLUMN IF NOT EXISTS fiber_g REAL;

ALTER TABLE nutrition_targets
  ADD COLUMN IF NOT EXISTS fiber_g       REAL DEFAULT 30.0;
ALTER TABLE nutrition_targets
  ADD COLUMN IF NOT EXISTS fiber_soft_lo REAL DEFAULT 0.10;
ALTER TABLE nutrition_targets
  ADD COLUMN IF NOT EXISTS fiber_hard_lo REAL DEFAULT 0.30;
ALTER TABLE nutrition_targets
  ADD COLUMN IF NOT EXISTS k_fiber_under REAL DEFAULT 800;

-- Backfill NULL fiber_g in nutrition_targets rows that pre-date this migration
UPDATE nutrition_targets
  SET fiber_g       = 30.0,
      fiber_soft_lo = 0.10,
      fiber_hard_lo = 0.30,
      k_fiber_under = 800
  WHERE fiber_g IS NULL;
