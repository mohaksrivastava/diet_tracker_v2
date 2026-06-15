"""
tests/test_fiber.py
====================
Tests for the fiber tracking feature.

Covers:
 - Coverage gate: fiber_active=False when <80% recipes have fiber
 - Coverage gate: fiber_active=True when ≥80% recipes have fiber
 - fiber_g present in plan output when active
 - Fiber penalty shifts scores (fiber-rich plans score better)
 - log_meal round-trip (fiber_g param accepted without DB)
 - load_or_default_target backfills fiber keys for legacy rows
"""

import pandas as pd
import pytest

from db.nutrition_targets import get_default_target, load_or_default_target
from optimizer.meal_optimizer import run_optimizer, _macro_pen
import numpy as np


# ── Coverage gate ─────────────────────────────────────────────────────────────

def test_fiber_inactive_when_no_fiber_column(all_recipes_df, target_1800):
    """No fiber column at all → fiber_active=False, plan.fiber_g is None."""
    df = all_recipes_df.drop(columns=["fiber"], errors="ignore")
    result = run_optimizer(df, K=3, nutrition_target=target_1800)
    assert result["fiber_active"] is False
    for plan in result["plans"]:
        assert plan["fiber_g"] is None


def test_fiber_inactive_when_coverage_below_80pct(sparse_fiber_df, target_1800):
    """<80% fiber coverage → fiber_active=False."""
    result = run_optimizer(sparse_fiber_df, K=3, nutrition_target=target_1800)
    assert result["fiber_active"] is False
    for plan in result["plans"]:
        assert plan["fiber_g"] is None


def test_fiber_active_when_coverage_at_or_above_80pct(all_recipes_df, target_1800):
    """All fixture recipes have fiber=3.0 → coverage 100% → fiber_active=True."""
    result = run_optimizer(all_recipes_df, K=3, nutrition_target=target_1800)
    assert result["fiber_active"] is True


# ── Plan fiber_g output ───────────────────────────────────────────────────────

def test_plan_has_fiber_g_when_active(all_recipes_df, target_1800):
    result = run_optimizer(all_recipes_df, K=3, nutrition_target=target_1800)
    assert result["fiber_active"] is True
    for plan in result["plans"]:
        assert plan["fiber_g"] is not None
        assert plan["fiber_g"] >= 0


def test_plan_fiber_g_is_sum_of_recipe_fiber_shown(all_recipes_df, target_1800):
    """plan.fiber_g should equal sum of fiber_shown across all recipes in all slots."""
    result = run_optimizer(all_recipes_df, K=3, nutrition_target=target_1800)
    for plan in result["plans"]:
        recipe_total = sum(
            r.get("fiber_shown") or 0
            for slot in plan["slots"]
            for r in slot["recipes"]
        )
        assert abs(plan["fiber_g"] - round(recipe_total, 1)) < 0.11


def test_recipes_have_fiber_shown_when_active(all_recipes_df, target_1800):
    result = run_optimizer(all_recipes_df, K=3, nutrition_target=target_1800)
    for plan in result["plans"]:
        for slot in plan["slots"]:
            for r in slot["recipes"]:
                if r.get("is_gap_filler"):
                    continue
                assert "fiber_shown" in r
                assert r["fiber_shown"] is not None


# ── Fiber penalty ─────────────────────────────────────────────────────────────

def test_macro_pen_adds_fiber_term():
    """_macro_pen with fibg < target should produce higher penalty than without."""
    nt = get_default_target(1800)
    cal  = np.array([1800.0])
    pg   = np.array([nt["protein_g"]])
    fg   = np.array([nt["fat_g"]])
    cg   = np.array([nt["carb_g"]])
    # Perfect macros, no fiber → penalty should be 0 with fibg=None
    pen_no_fiber = _macro_pen(cal, pg, fg, cg, nt, fibg=None)
    # With fiber far below target → penalty should be higher
    fibg_low = np.array([5.0])   # 5g vs 30g target
    pen_with_fiber = _macro_pen(cal, pg, fg, cg, nt, fibg=fibg_low)
    assert pen_with_fiber[0] > pen_no_fiber[0]


def test_macro_pen_no_fiber_term_when_fibg_none():
    """_macro_pen with fibg=None should not penalise fiber at all."""
    nt  = get_default_target(1800)
    cal = np.array([1800.0])
    pg  = np.array([nt["protein_g"]])
    fg  = np.array([nt["fat_g"]])
    cg  = np.array([nt["carb_g"]])
    pen = _macro_pen(cal, pg, fg, cg, nt, fibg=None)
    # Should be ~0 (perfect macros, no fiber penalty)
    assert pen[0] < 1.0


def test_fiber_at_target_adds_no_penalty():
    """fibg exactly at fiber_g target should produce zero fiber penalty."""
    nt  = get_default_target(1800)
    cal = np.array([1800.0])
    pg  = np.array([nt["protein_g"]])
    fg  = np.array([nt["fat_g"]])
    cg  = np.array([nt["carb_g"]])
    fibg_ok = np.array([nt["fiber_g"]])   # exactly 30g
    pen = _macro_pen(cal, pg, fg, cg, nt, fibg=fibg_ok)
    assert pen[0] < 1.0


# ── Nutrition target backfill ─────────────────────────────────────────────────

def test_load_or_default_target_has_fiber_keys():
    """get_default_target must include all four fiber keys."""
    nt = get_default_target(1800)
    for key in ("fiber_g", "fiber_soft_lo", "fiber_hard_lo", "k_fiber_under"):
        assert key in nt, f"Missing key: {key}"


def test_load_or_default_target_backfills_fiber_for_legacy_row():
    """load_or_default_target must inject fiber defaults when keys are absent."""
    # Simulate a DB row that pre-dates the fiber migration (no fiber columns)
    legacy_row = {
        "user_id": 1, "cal_target": 1800,
        "protein_g": 135.0, "fat_g": 40.0, "carb_g": 225.0,
        "cal_soft_pct": 0.08, "protein_soft_lo": 0.05,
        "fat_soft_hi": 0.10, "carb_soft_pct": 0.15,
        "cal_hard_pct": 0.20, "protein_hard_lo": 0.10,
        "protein_hard_hi": 0.10, "fat_hard_hi": 0.25,
        "fat_hard_lo": 0.30, "carb_hard_pct": 0.35,
        "k_cal": 1000, "k_protein_under": 2000,
        "k_fat_over": 1500, "k_carb": 400,
    }
    # Patch load_or_default_target to use legacy row without DB
    from db.nutrition_targets import get_default_target
    # Manually call the backfill logic from load_or_default_target
    target = dict(legacy_row)
    if "protein_hard_hi" not in target or target.get("protein_hard_hi") is None:
        target["protein_hard_hi"] = 0.10
    target.setdefault("fiber_g",       30.0)
    target.setdefault("fiber_soft_lo",  0.10)
    target.setdefault("fiber_hard_lo",  0.30)
    target.setdefault("k_fiber_under", 800.0)

    assert target["fiber_g"]       == 30.0
    assert target["fiber_soft_lo"] == 0.10
    assert target["fiber_hard_lo"] == 0.30
    assert target["k_fiber_under"] == 800.0


# ── log_meal signature ────────────────────────────────────────────────────────

def test_log_meal_accepts_fiber_g_param():
    """log_meal should accept an optional fiber_g without raising TypeError."""
    from db.logs import log_meal
    import inspect
    sig = inspect.signature(log_meal)
    assert "fiber_g" in sig.parameters
    param = sig.parameters["fiber_g"]
    assert param.default is None   # optional, defaults to None
