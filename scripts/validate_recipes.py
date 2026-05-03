# scripts/validate_recipes.py
# Validate generated recipes before merging into the main CSVs.
#
# Usage:
#   python scripts/validate_recipes.py data/recipes_generated.csv data/recipe_details_generated.csv

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

VALID_FOOD_TYPES = {"vegan", "veg", "dairy", "egg", "non-veg"}
VALID_DIFFICULTY = {"Easy", "Medium", "Hard"}
VALID_ROLES = {"anchor_protein", "anchor_starch", "anchor_veg",
               "complete_meal", "side", "beverage"}
VALID_CUISINES = {
    "north_indian", "south_indian", "indo_chinese", "east_asian",
    "continental", "mediterranean", "mexican", "unknown",
    "indian", "chinese", "middle_eastern", "japanese", "global",
}
VALID_MEAL_TYPES = {"Breakfast", "Lunch", "Dinner", "Snack"}


def word_count(text: str) -> int:
    return len(str(text).split()) if text else 0


def validate(recipes_path: str, details_path: str):
    errors = []
    warnings = []

    recipes = pd.read_csv(recipes_path)
    details = pd.read_csv(details_path)

    # Load existing base recipes for uniqueness check
    base_recipes_path = os.path.join(os.path.dirname(recipes_path), "recipes.csv")
    existing_names = set()
    if os.path.exists(base_recipes_path):
        existing = pd.read_csv(base_recipes_path)
        existing_names = set(existing["name"].str.lower().str.strip())

    # Cross-join by name
    merged = pd.merge(recipes, details, on="name", how="outer", indicator=True)
    for _, row in merged.iterrows():
        if row["_merge"] != "both":
            errors.append(f"'{row.get('name', '???')}' missing in {'details' if '_merge' in str(row) else 'recipes'}")

    merged = pd.merge(recipes, details, on="name", how="inner")

    for idx, r in merged.iterrows():
        name = str(r["name"])
        prefix = f"Row {idx+1} ('{name}')"

        # 1. Uniqueness
        if name.lower().strip() in existing_names:
            errors.append(f"{prefix}: Name duplicates existing base recipe")

        # 2. Required fields
        for field in ["name", "category", "meal_type", "food_type", "difficulty",
                      "calories", "protein", "carbohydrate", "fat", "role", "cuisine",
                      "description", "tags", "source", "ingredients", "steps"]:
            if pd.isna(r.get(field)) or str(r.get(field)).strip() == "":
                errors.append(f"{prefix}: Missing or empty field '{field}'")

        # 3. Enum checks
        ft = str(r.get("food_type", "")).lower().strip()
        if ft not in VALID_FOOD_TYPES:
            errors.append(f"{prefix}: Invalid food_type '{ft}'")

        diff = str(r.get("difficulty", "")).strip().title()
        if diff not in VALID_DIFFICULTY:
            errors.append(f"{prefix}: Invalid difficulty '{diff}'")

        role = str(r.get("role", "")).lower().strip()
        if role not in VALID_ROLES:
            errors.append(f"{prefix}: Invalid role '{role}'")

        cuisine = str(r.get("cuisine", "")).lower().strip().replace(" ", "_")
        if cuisine not in VALID_CUISINES:
            errors.append(f"{prefix}: Invalid cuisine '{cuisine}'")

        # 4. Meal type check
        meal_types = [m.strip().title() for m in str(r.get("meal_type", "")).split(";")]
        for mt in meal_types:
            if mt and mt not in VALID_MEAL_TYPES:
                errors.append(f"{prefix}: Invalid meal_type component '{mt}'")
        if not meal_types or all(m == "" for m in meal_types):
            errors.append(f"{prefix}: No valid meal_type")

        # 5. Macro math
        try:
            cal = float(r["calories"])
            p = float(r["protein"])
            c = float(r["carbohydrate"])
            f = float(r["fat"])
        except (TypeError, ValueError):
            errors.append(f"{prefix}: Non-numeric macros")
            continue

        if not (20 <= cal <= 1200):
            errors.append(f"{prefix}: Calories {cal} out of range 20–1200")

        est_cal = p * 4 + c * 4 + f * 9
        if abs(cal - est_cal) / max(cal, 1) > 0.15:
            errors.append(f"{prefix}: Macro math off — stated {cal:.0f} kcal, estimated {est_cal:.0f} kcal (P={p}, C={c}, F={f})")

        # 6. Portion bounds
        try:
            pmin = float(r.get("portion_min", 0.5))
            ptyp = float(r.get("portion_typical", 1.0))
            pmax = float(r.get("portion_max", 1.5))
            if not (0.1 <= pmin <= ptyp <= pmax <= 3.0):
                warnings.append(f"{prefix}: Portion bounds look odd ({pmin}/{ptyp}/{pmax})")
        except (TypeError, ValueError):
            warnings.append(f"{prefix}: Non-numeric portion bounds")

        # 7. Word counts
        desc_wc = word_count(r.get("description"))
        if desc_wc > 180:
            warnings.append(f"{prefix}: Description is {desc_wc} words (target <150)")
        elif desc_wc < 10:
            warnings.append(f"{prefix}: Description is only {desc_wc} words")

        steps_wc = word_count(r.get("steps"))
        if steps_wc > 300:
            warnings.append(f"{prefix}: Steps are {steps_wc} words (target <250)")

        # 8. Tags count
        tags = [t.strip() for t in str(r.get("tags", "")).split(";") if t.strip()]
        if len(tags) != 5:
            warnings.append(f"{prefix}: Found {len(tags)} tags instead of 5")
        for t in tags:
            if len(t.split()) > 5:
                warnings.append(f"{prefix}: Tag '{t}' exceeds 5 words")

        # 9. Ingredient format
        ingredients = str(r.get("ingredients", ""))
        if "|" not in ingredients:
            warnings.append(f"{prefix}: Ingredients not pipe-delimited")
        for ing in ingredients.split("|"):
            ing = ing.strip()
            if not ing:
                continue
            # Must end with g or ml
            if not (ing.lower().endswith("g") or ing.lower().endswith("ml")):
                warnings.append(f"{prefix}: Ingredient '{ing}' missing g/ml unit")
            elif "to taste" in ing.lower():
                warnings.append(f"{prefix}: Ingredient '{ing}' uses subjective quantity")

        # 10. Source URL
        source = str(r.get("source", ""))
        if not source.startswith("http"):
            warnings.append(f"{prefix}: Source '{source}' doesn't look like a URL")

    # Summary
    print("=" * 60)
    print(f"VALIDATION RESULTS for {len(merged)} recipes")
    print("=" * 60)
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        print("\n--- ERRORS ---")
        for e in errors[:30]:
            print(f"  ✗ {e}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more errors")
    if warnings:
        print("\n--- WARNINGS ---")
        for w in warnings[:30]:
            print(f"  [WARN] {w}")
        if len(warnings) > 30:
            print(f"  ... and {len(warnings) - 30} more warnings")
    print("=" * 60)

    if errors:
        sys.exit(1)
    print("Validation passed (no errors)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/validate_recipes.py <recipes.csv> <details.csv>")
        sys.exit(1)
    validate(sys.argv[1], sys.argv[2])
