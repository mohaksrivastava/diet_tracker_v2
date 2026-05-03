-- ============================================================
-- migration_v3_recipes_expansion.sql
-- Add description, tags, source; expand cuisine enum.
-- Run ONCE in Supabase SQL Editor after migration_v2_optimizer.sql
-- ============================================================

-- ── 1. Expand cuisine enum on recipes ─────────────────────────────────────────
ALTER TABLE recipes
  DROP CONSTRAINT IF EXISTS cuisine_valid,
  ADD  CONSTRAINT cuisine_valid CHECK (cuisine IN (
    -- legacy values (keep for backward compatibility)
    'north_indian', 'south_indian', 'indo_chinese', 'east_asian',
    'continental', 'mediterranean', 'mexican', 'unknown',
    -- new user-requested values
    'indian', 'chinese', 'middle_eastern', 'japanese', 'global'
  ));

-- ── 2. Add new columns to recipes ─────────────────────────────────────────────
ALTER TABLE recipes
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS tags      TEXT,
  ADD COLUMN IF NOT EXISTS source    TEXT;

-- ── 3. Same columns on custom_recipes (AI fill will populate them) ────────────
ALTER TABLE custom_recipes
  DROP CONSTRAINT IF EXISTS cuisine_valid_custom,
  ADD  CONSTRAINT cuisine_valid_custom CHECK (cuisine IN (
    'north_indian', 'south_indian', 'indo_chinese', 'east_asian',
    'continental', 'mediterranean', 'mexican', 'unknown',
    'indian', 'chinese', 'middle_eastern', 'japanese', 'global'
  ));

ALTER TABLE custom_recipes
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS tags      TEXT,
  ADD COLUMN IF NOT EXISTS source    TEXT;

-- ── 4. Verify ─────────────────────────────────────────────────────────────────
SELECT
  (SELECT COUNT(*) FROM recipes) AS recipe_rows,
  (SELECT COUNT(*) FROM custom_recipes) AS custom_rows,
  (SELECT COUNT(*) FROM information_schema.columns
   WHERE table_name = 'recipes' AND column_name IN ('description','tags','source')) AS new_cols_present;
