"""
Shared fixtures for the optimizer test suite.

Recipe calories are deliberately calibrated so that plausible combinations
fit every slot window (±30%) across K=2..5 and cal targets 1200–2500.
"""

import pytest
import pandas as pd
from db.nutrition_targets import get_default_target


# ─── Recipe factory ───────────────────────────────────────────────────────────

def _r(name, meal_type, food_type, food_group, calories, protein, carb, fat,
       role="side", cuisine="north_indian",
       portion_min=0.5, portion_typical=1.0, portion_max=2.5):
    return {
        "name":             name,
        "category":         "recipe",
        "meal_type":        meal_type,
        "food_type":        food_type,
        "food_group":       food_group,
        "calories":         float(calories),
        "protein":          float(protein),
        "carbohydrate":     float(carb),
        "fat":              float(fat),
        "role":             role,
        "cuisine":          cuisine,
        "portion_min":      portion_min,
        "portion_typical":  portion_typical,
        "portion_max":      portion_max,
        "difficulty":       "Easy",
        "cook_time_mins":   20,
    }


# Calorie notes per slot (1800 kcal reference, SLOT_WINDOW = ±30%):
#   K=2: lunch/dinner target=900, window [630, 1170]
#   K=3: lunch/dinner target=630, window [441, 819]; breakfast=540 [378, 702]
#   K=4: lunch/dinner target=550, window [385, 715]; breakfast=400 [280, 520]; snack=300 [210, 390]
#   K=5: lunch/dinner target=470, window [329, 611]; breakfast=320 [224, 416]; snack=270 [189, 351]

FIXTURE_RECIPES = [
    # ── Lunch / Dinner — anchor proteins ──────────────────────────────────────
    # Vegan anchor proteins: combine with anchor starch to reach slot targets
    _r("Dal Fry",          "Lunch|Dinner", "vegan",   "lentils",        350, 18, 45,  8, "anchor_protein"),
    _r("Rajma",            "Lunch|Dinner", "vegan",   "kidney_beans",   320, 16, 48,  6, "anchor_protein"),
    _r("Chana Masala",     "Lunch|Dinner", "vegan",   "chickpeas",      290, 14, 44,  7, "anchor_protein"),
    # Non-veg anchor proteins
    _r("Chicken Curry",    "Lunch|Dinner", "non-veg", "poultry",        380, 32, 12, 18, "anchor_protein"),
    _r("Fish Curry",       "Lunch|Dinner", "non-veg", "seafood",        310, 28, 10, 14, "anchor_protein", "south_indian"),
    # Dairy / egg
    _r("Paneer Makhani",   "Lunch|Dinner", "dairy",   "dairy_protein",  340, 16, 18, 22, "anchor_protein"),
    _r("Egg Curry",        "Lunch|Dinner", "egg",     "egg_protein",    300, 14, 12, 18, "anchor_protein"),
    _r("Tandoori Chicken", "Lunch|Dinner", "non-veg", "grilled_poultry", 250, 30,  8, 10, "anchor_protein"),
    _r("Soy Chunks Curry", "Lunch|Dinner", "vegan",   "soy",            220, 28, 12,  8, "anchor_protein"),

    # ── Lunch / Dinner — anchor starches (all vegan) ──────────────────────────
    # Same food_group ("rice") intentionally prevents Steamed Rice + Jeera Rice
    # from co-existing in the same slot (duplicate food_group rule).
    _r("Steamed Rice",     "Lunch|Dinner", "vegan",   "rice",           350,  6, 78,  1, "anchor_starch", "south_indian"),
    _r("Roti",             "Lunch|Dinner", "vegan",   "roti",           300,  9, 60,  5, "anchor_starch", "north_indian", 0.5, 1.0, 2.0),
    _r("Jeera Rice",       "Lunch|Dinner", "vegan",   "rice",           360,  6, 72,  5, "anchor_starch"),

    # ── Lunch / Dinner — complete meals ───────────────────────────────────────
    # Single-recipe slots for lunch/dinner require role == "complete_meal".
    # Calories around 480–580 kcal → at 1x fit K=3 window [441, 819].
    # At 1.75x (1015 kcal) fit K=2 window [630, 1170] too.
    _r("Dal Khichdi",      "Lunch|Dinner", "vegan",   "mixed_grain",    480, 18, 80,  8, "complete_meal"),
    _r("Veg Biryani",      "Lunch|Dinner", "veg",     "mixed_grain",    520, 12, 90, 12, "complete_meal"),
    _r("Chicken Biryani",  "Lunch|Dinner", "non-veg", "mixed_grain",    580, 35, 85, 14, "complete_meal"),
    _r("Palak Tofu",       "Lunch|Dinner", "vegan",   "tofu",           420, 22, 28, 24, "complete_meal"),

    # ── Lunch / Dinner — sides ────────────────────────────────────────────────
    _r("Mixed Vegetable",  "Lunch|Dinner", "vegan",   "vegetable",      160,  4, 22,  6, "side"),
    _r("Raita",            "Lunch|Dinner", "dairy",   "dairy_product",  100,  5, 10,  4, "side"),

    # ── Breakfast ─────────────────────────────────────────────────────────────
    # Breakfast is min_n=1, max_n=3, no anchor requirement.
    # Single-item at 1x: Oats (280), Poha (260), Idli (300), PB Toast (320),
    # Paratha (380). Fit K=4 breakfast window [280, 520] and K=5 [224, 416].
    # At 1.75x they fit K=3 window [378, 702] and K=2 (slot target=0 for K=2).
    _r("Oats Upma",        "Breakfast",    "vegan",   "oats",           280,  8, 48,  6, "complete_meal", "south_indian"),
    _r("Poha",             "Breakfast",    "vegan",   "flattened_rice", 260,  6, 46,  5, "complete_meal", "north_indian"),
    _r("Idli Sambar",      "Breakfast",    "vegan",   "fermented_grain",300, 10, 52,  5, "complete_meal", "south_indian"),
    _r("Egg Omelette",     "Breakfast",    "egg",     "egg_dish",       220, 14,  4, 16, "complete_meal", "continental"),
    _r("PB Toast",         "Breakfast",    "vegan",   "bread",          320, 12, 38, 14, "complete_meal", "continental"),
    _r("Paratha",          "Breakfast",    "dairy",   "wheat_bread",    380,  9, 58, 14, "complete_meal"),
    _r("Moong Dal Chilla", "Breakfast",    "vegan",   "lentil_crepe",   200, 14, 24,  6, "complete_meal"),
    _r("Egg Bhurji",       "Breakfast",    "egg",     "scrambled_egg",  180, 16,  4, 12, "complete_meal"),
    _r("Banana Smoothie",  "Breakfast",    "vegan",   "fruit_drink",    200,  4, 42,  2, "side", "unknown"),

    # ── Snacks ────────────────────────────────────────────────────────────────
    # Snack targets at 1800 kcal: K=4→300 [210, 390], K=5→270 [189, 351].
    # At 2.5x: Mixed Nuts=450 (too high), so 1.75x=315 fits K=4. ✓
    # Yogurt at 2.5x=250 fits both windows. ✓
    _r("Mixed Nuts",       "Snack",        "vegan",   "nuts",           180,  5,  8, 15, "side", "unknown"),
    _r("Fruit Bowl",       "Snack",        "vegan",   "fresh_fruit",    120,  2, 28,  1, "side", "unknown"),
    _r("Roasted Chickpeas","Snack",        "vegan",   "roasted_legumes",150,  8, 22,  3, "side", "unknown"),
    _r("Yogurt",           "Snack",        "dairy",   "dairy_product",  100,  8, 12,  2, "side", "unknown"),
    _r("Sprouts Salad",    "Snack",        "vegan",   "sprouts",        110,  8, 18,  2, "side", "unknown"),

    # ── Gap fillers (role="gap_filler") ───────────────────────────────────────
    # Phase 3 adds these only when a macro deficit ≥ 5 g persists after Phase 2.
    _r("Protein Shake",    "Snack",        "dairy",   "supplement",     150, 25,  8,  2, "gap_filler", "unknown"),
    _r("Boiled Chicken",   "Snack",        "non-veg", "lean_poultry",   165, 31,  0,  4, "gap_filler", "unknown"),
    _r("Chia Seeds",       "Snack",        "vegan",   "seeds",          100,  5, 12,  5, "gap_filler", "unknown"),
]


# ─── DataFrame fixtures ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def all_recipes_df():
    return pd.DataFrame(FIXTURE_RECIPES)


@pytest.fixture(scope="module")
def vegan_only_df():
    """Only vegan recipes — used to test strict food preference filtering."""
    df = pd.DataFrame(FIXTURE_RECIPES)
    return df[df["food_type"] == "vegan"].copy().reset_index(drop=True)


@pytest.fixture(scope="module")
def nonveg_only_df():
    """Only non-veg recipes — vegan/veg users should get no results from this pool."""
    df = pd.DataFrame(FIXTURE_RECIPES)
    return df[df["food_type"] == "non-veg"].copy().reset_index(drop=True)


@pytest.fixture(scope="module")
def no_gap_filler_df():
    """Recipe pool with gap filler recipes removed — Phase 3 should be inert."""
    df = pd.DataFrame(FIXTURE_RECIPES)
    return df[df["role"] != "gap_filler"].copy().reset_index(drop=True)


@pytest.fixture(scope="module")
def no_role_column_df():
    """DataFrame without a 'role' column — optimizer should fill in 'side' default."""
    df = pd.DataFrame(FIXTURE_RECIPES).drop(columns=["role"])
    return df


# ─── Nutrition target fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="module")
def target_1200():
    return get_default_target(1200)

@pytest.fixture(scope="module")
def target_1500():
    return get_default_target(1500)

@pytest.fixture(scope="module")
def target_1800():
    return get_default_target(1800)

@pytest.fixture(scope="module")
def target_2000():
    return get_default_target(2000)

@pytest.fixture(scope="module")
def target_2500():
    return get_default_target(2500)
