# db/nutrition_targets.py
# Per-user nutrition targets: load, save, and derive defaults.
# Macro split: 30% protein · 50% carbs · 20% fat (as % of total kcal)

from db.connection import execute


# ── Defaults ──────────────────────────────────────────────────────────────────

def get_default_target(daily_cal: int) -> dict:
    """
    Derive sensible macro targets from a daily calorie goal.
    Split: 30% protein · 50% carb · 20% fat
    Returns a complete target dict usable by the optimizer without a DB call.
    """
    return {
        "cal_target":      daily_cal,
        "protein_g":       round(daily_cal * 0.30 / 4, 1),
        "fat_g":           round(daily_cal * 0.20 / 9, 1),
        "carb_g":          round(daily_cal * 0.50 / 4, 1),
        "fiber_g":         30.0,
        # Soft bands (zero penalty inside)
        "cal_soft_pct":    0.08,
        "protein_soft_lo": 0.05,
        "fat_soft_hi":     0.10,
        "carb_soft_pct":   0.15,
        "fiber_soft_lo":   0.10,
        # Hard limits (candidates rejected outside)
        "cal_hard_pct":    0.20,
        "protein_hard_lo": 0.10,
        "protein_hard_hi": 0.10,
        "fat_hard_hi":     0.25,
        "fat_hard_lo":     0.30,
        "carb_hard_pct":   0.35,
        "fiber_hard_lo":   0.30,
        # Penalty weights
        "k_cal":           1000,
        "k_protein_under": 2000,
        "k_fat_over":      1500,
        "k_carb":          400,
        "k_fiber_under":   800,
    }


def get_macro_split() -> dict:
    """Return the canonical macro split percentages for display and recomputation."""
    return {"protein_pct": 0.30, "carb_pct": 0.50, "fat_pct": 0.20}


# ── History blending ──────────────────────────────────────────────────────────

def blend_macro_targets(nt: dict, history_df, n_history: int) -> dict:
    """
    Adjust fat and carb targets based on historical intake (up to 7 days).

    Uses cumulative gap formula:
        blended = daily_target * (N+1) - sum(eaten over N days)

    Clamped to 50%-150% of daily target to prevent extreme values.
    Protein is NEVER blended — it stays strict per-day.

    Returns a modified copy of nt with adjusted fat_g and carb_g.
    """
    if n_history == 0 or history_df is None or history_df.empty:
        return dict(nt)

    out = dict(nt)
    daily_fat  = float(nt["fat_g"])
    daily_carb = float(nt["carb_g"])

    hist_fat  = float(history_df["total_fat"].sum())
    hist_carb = float(history_df["total_carb"].sum())

    # Cumulative gap: what today needs to bring the (N+1)-day total on target
    blended_fat  = daily_fat  * (n_history + 1) - hist_fat
    blended_carb = daily_carb * (n_history + 1) - hist_carb

    # Clamp to 50%-150% of daily target
    out["fat_g"]  = round(max(daily_fat  * 0.50, min(blended_fat,  daily_fat  * 1.50)), 1)
    out["carb_g"] = round(max(daily_carb * 0.50, min(blended_carb, daily_carb * 1.50)), 1)

    return out


# ── DB helpers ────────────────────────────────────────────────────────────────

def load_nutrition_target(conn, user_id: int) -> dict | None:
    """
    Load a user's targets from the nutrition_targets table.
    Returns None if the row doesn't exist yet.
    """
    row = execute(conn,
        "SELECT * FROM nutrition_targets WHERE user_id = %s LIMIT 1",
        (user_id,), fetch="one")
    return dict(row) if row else None


def load_or_default_target(conn, user_id: int, daily_cal: int) -> dict:
    """
    Load from DB; fall back to derived defaults so the optimizer always
    gets a valid target dict even before the migration has run.
    """
    target = load_nutrition_target(conn, user_id)
    if target is None:
        return get_default_target(daily_cal)
    # Backfill protein_hard_hi for legacy rows that lack it
    if "protein_hard_hi" not in target or target.get("protein_hard_hi") is None:
        target["protein_hard_hi"] = 0.10
    return target


def recompute_grams_from_cal(nt: dict, new_cal: int) -> dict:
    """
    Given an existing target dict (which may have stored split %),
    recompute protein_g / fat_g / carb_g from the new calorie target.

    Recovers split % from stored grams; falls back to canonical 30/50/20
    if the stored split looks unreasonable.
    """
    stored_cal = float(nt.get("cal_target") or new_cal)
    if stored_cal > 0:
        prot_pct = float(nt.get("protein_g", 0)) * 4 / stored_cal
        fat_pct  = float(nt.get("fat_g",     0)) * 9 / stored_cal
        carb_pct = float(nt.get("carb_g",    0)) * 4 / stored_cal
    else:
        prot_pct = fat_pct = carb_pct = 0.0

    # Sanity check: if split is unreasonable, fall back to canonical
    if not (0.15 <= prot_pct <= 0.50 and
            0.05 <= fat_pct  <= 0.40 and
            0.25 <= carb_pct <= 0.70 and
            0.80 <= prot_pct + fat_pct + carb_pct <= 1.10):
        split = get_macro_split()
        prot_pct = split["protein_pct"]
        fat_pct  = split["fat_pct"]
        carb_pct = split["carb_pct"]

    out = dict(nt)
    out["cal_target"] = new_cal
    out["protein_g"]  = round(new_cal * prot_pct / 4, 1)
    out["fat_g"]      = round(new_cal * fat_pct  / 9, 1)
    out["carb_g"]     = round(new_cal * carb_pct / 4, 1)
    return out


def save_nutrition_target(conn, user_id: int, data: dict):
    """Upsert a user's nutrition targets."""
    execute(conn,
        """INSERT INTO nutrition_targets
             (user_id, cal_target, protein_g, fat_g, carb_g, fiber_g,
              cal_soft_pct, protein_soft_lo, fat_soft_hi, carb_soft_pct,
              fiber_soft_lo, cal_hard_pct, protein_hard_lo, protein_hard_hi,
              fat_hard_hi, fat_hard_lo, carb_hard_pct, fiber_hard_lo,
              k_cal, k_protein_under, k_fat_over, k_carb, k_fiber_under,
              updated_at)
           VALUES
             (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
              %s,%s,%s,%s,%s, NOW())
           ON CONFLICT (user_id) DO UPDATE SET
             cal_target       = EXCLUDED.cal_target,
             protein_g        = EXCLUDED.protein_g,
             fat_g            = EXCLUDED.fat_g,
             carb_g           = EXCLUDED.carb_g,
             fiber_g          = EXCLUDED.fiber_g,
             cal_soft_pct     = EXCLUDED.cal_soft_pct,
             protein_soft_lo  = EXCLUDED.protein_soft_lo,
             fat_soft_hi      = EXCLUDED.fat_soft_hi,
             carb_soft_pct    = EXCLUDED.carb_soft_pct,
             fiber_soft_lo    = EXCLUDED.fiber_soft_lo,
             cal_hard_pct     = EXCLUDED.cal_hard_pct,
             protein_hard_lo  = EXCLUDED.protein_hard_lo,
             protein_hard_hi  = EXCLUDED.protein_hard_hi,
             fat_hard_hi      = EXCLUDED.fat_hard_hi,
             fat_hard_lo      = EXCLUDED.fat_hard_lo,
             carb_hard_pct    = EXCLUDED.carb_hard_pct,
             fiber_hard_lo    = EXCLUDED.fiber_hard_lo,
             k_cal            = EXCLUDED.k_cal,
             k_protein_under  = EXCLUDED.k_protein_under,
             k_fat_over       = EXCLUDED.k_fat_over,
             k_carb           = EXCLUDED.k_carb,
             k_fiber_under    = EXCLUDED.k_fiber_under,
             updated_at       = NOW()""",
        (user_id,
         data["cal_target"], data["protein_g"], data["fat_g"],
         data["carb_g"],     data["fiber_g"],
         data["cal_soft_pct"],    data["protein_soft_lo"], data["fat_soft_hi"],
         data["carb_soft_pct"],   data["fiber_soft_lo"],
         data["cal_hard_pct"],    data["protein_hard_lo"],
         data.get("protein_hard_hi", 0.10),
         data["fat_hard_hi"],
         data["fat_hard_lo"],     data["carb_hard_pct"],   data["fiber_hard_lo"],
         data["k_cal"],           data["k_protein_under"], data["k_fat_over"],
         data["k_carb"],          data["k_fiber_under"]))
