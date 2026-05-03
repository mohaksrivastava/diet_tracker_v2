"""
Unit tests for db/nutrition_targets.py

These functions are pure (no DB connection required) and used by both
the optimizer and the settings page. A bug here cascades to every plan.
"""

import pytest
from db.nutrition_targets import (
    get_default_target,
    get_macro_split,
    recompute_grams_from_cal,
)


class TestGetDefaultTarget:
    """get_default_target() derives macro gram targets from a calorie goal."""

    @pytest.mark.parametrize("cal", [1200, 1500, 1800, 2000, 2500])
    def test_macro_split_is_30_50_20(self, cal):
        t = get_default_target(cal)
        assert abs(t["protein_g"] * 4 / cal - 0.30) < 0.01, "Protein not 30% of calories"
        assert abs(t["carb_g"]    * 4 / cal - 0.50) < 0.01, "Carbs not 50% of calories"
        assert abs(t["fat_g"]     * 9 / cal - 0.20) < 0.01, "Fat not 20% of calories"

    @pytest.mark.parametrize("cal", [1200, 1500, 1800, 2000, 2500])
    def test_macro_grams_sum_close_to_calories(self, cal):
        t = get_default_target(cal)
        macro_cal = t["protein_g"] * 4 + t["carb_g"] * 4 + t["fat_g"] * 9
        assert abs(macro_cal - cal) < 5, (
            f"{cal} kcal: macro calories sum to {macro_cal:.1f}"
        )

    def test_cal_target_stored_correctly(self):
        t = get_default_target(1800)
        assert t["cal_target"] == 1800

    def test_has_all_required_optimizer_keys(self):
        required = {
            "cal_target", "protein_g", "fat_g", "carb_g", "fiber_g",
            "cal_soft_pct", "protein_soft_lo", "fat_soft_hi", "carb_soft_pct",
            "cal_hard_pct", "protein_hard_lo", "fat_hard_hi", "fat_hard_lo",
            "carb_hard_pct",
            "k_cal", "k_protein_under", "k_fat_over", "k_carb",
        }
        t = get_default_target(1800)
        missing = required - set(t.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_hard_bands_wider_than_soft_bands(self):
        t = get_default_target(1800)
        assert t["cal_hard_pct"]     > t["cal_soft_pct"]
        assert t["protein_hard_lo"]  > t["protein_soft_lo"]
        assert t["fat_hard_hi"]      > t["fat_soft_hi"]
        assert t["carb_hard_pct"]    > t["carb_soft_pct"]

    def test_protein_grams_scale_with_calories(self):
        t1200 = get_default_target(1200)
        t2500 = get_default_target(2500)
        # More calories → more protein grams
        assert t2500["protein_g"] > t1200["protein_g"]
        # Ratio should reflect calorie ratio
        ratio = t2500["protein_g"] / t1200["protein_g"]
        assert abs(ratio - 2500 / 1200) < 0.05


class TestGetMacroSplit:

    def test_split_sums_to_one(self):
        s = get_macro_split()
        total = s["protein_pct"] + s["carb_pct"] + s["fat_pct"]
        assert abs(total - 1.0) < 0.01

    def test_canonical_values(self):
        s = get_macro_split()
        assert s["protein_pct"] == pytest.approx(0.30)
        assert s["carb_pct"]    == pytest.approx(0.50)
        assert s["fat_pct"]     == pytest.approx(0.20)


class TestRecomputeGramsFromCal:
    """
    When a user changes their calorie target in Settings, macro grams must
    be recalculated to preserve the stored macro split percentage.
    """

    def test_preserves_custom_split(self):
        # User has a 40/40/20 custom split at 1800 kcal
        nt = {
            "cal_target": 1800,
            "protein_g":  180.0,   # 40%
            "fat_g":       40.0,   # 20%
            "carb_g":     180.0,   # 40%
        }
        updated = recompute_grams_from_cal(nt, 2000)
        assert updated["cal_target"] == 2000
        # Split percentages should be preserved (within rounding)
        assert abs(updated["protein_g"] * 4 / 2000 - 0.40) < 0.02
        assert abs(updated["fat_g"]     * 9 / 2000 - 0.20) < 0.02
        assert abs(updated["carb_g"]    * 4 / 2000 - 0.40) < 0.02

    def test_fallback_on_unreasonable_split(self):
        # Stored split is nonsensical (protein > 100%)
        nt = {
            "cal_target": 1800,
            "protein_g":  600.0,   # 133% — impossible
            "fat_g":        5.0,
            "carb_g":      10.0,
        }
        updated = recompute_grams_from_cal(nt, 1800)
        # Falls back to canonical 30/50/20
        assert abs(updated["protein_g"] * 4 / 1800 - 0.30) < 0.02
        assert abs(updated["fat_g"]     * 9 / 1800 - 0.20) < 0.02
        assert abs(updated["carb_g"]    * 4 / 1800 - 0.50) < 0.02

    def test_output_contains_new_cal_target(self):
        nt = get_default_target(1800)
        updated = recompute_grams_from_cal(nt, 2200)
        assert updated["cal_target"] == 2200

    def test_non_cal_keys_are_preserved(self):
        nt = get_default_target(1800)
        updated = recompute_grams_from_cal(nt, 2000)
        # Penalty weights and bands should pass through unchanged
        for key in ("k_cal", "k_protein_under", "cal_hard_pct"):
            assert key in updated

    @pytest.mark.parametrize("new_cal", [1200, 1500, 1800, 2000, 2500])
    def test_grams_are_positive(self, new_cal):
        nt = get_default_target(1800)
        updated = recompute_grams_from_cal(nt, new_cal)
        assert updated["protein_g"] > 0
        assert updated["fat_g"]     > 0
        assert updated["carb_g"]    > 0

    def test_increasing_calories_increases_all_macros(self):
        nt_low  = recompute_grams_from_cal(get_default_target(1800), 1200)
        nt_high = recompute_grams_from_cal(get_default_target(1800), 2500)
        assert nt_high["protein_g"] > nt_low["protein_g"]
        assert nt_high["carb_g"]    > nt_low["carb_g"]
        assert nt_high["fat_g"]     > nt_low["fat_g"]
