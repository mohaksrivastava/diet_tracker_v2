# scripts/generate_recipes.py
# LLM-assisted bulk recipe generation for the 150-recipe expansion.
# Requires: Ollama running locally with the model specified below.
#
# Usage:
#   python scripts/generate_recipes.py
#
# Reads:  data/recipe_specs.json
# Writes: data/recipes_generated.csv  +  data/recipe_details_generated.csv
# Logs:   logs/generate_recipes_YYYYMM.log

import json
import logging
import os
import sys
import time
from datetime import datetime

import pandas as pd

# Ensure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama

# ── Configuration ──────────────────────────────────────────────────────────────
MODEL = "qwen2.5:7b"
BATCH_SIZE = 5          # recipes per LLM call (multi-turn is faster)
TEMPERATURE = 0.15
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, f"generate_recipes_{datetime.now().strftime('%Y%m')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GEN] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SPECS_PATH = os.path.join(DATA_DIR, "recipe_specs.json")
OUT_RECIPES_PATH = os.path.join(DATA_DIR, "recipes_generated.csv")
OUT_DETAILS_PATH = os.path.join(DATA_DIR, "recipe_details_generated.csv")
INGREDIENT_LIST_PATH = os.path.join(DATA_DIR, "ingredient_master_list.md")

VALID_FOOD_TYPES = {"vegan", "veg", "dairy", "egg", "non-veg"}
VALID_DIFFICULTY = {"Easy", "Medium", "Hard"}
VALID_ROLES = {"anchor_protein", "anchor_starch", "anchor_veg",
               "complete_meal", "side", "beverage"}
VALID_CUISINES = {
    "north_indian", "south_indian", "indo_chinese", "east_asian",
    "continental", "mediterranean", "mexican", "unknown",
    "indian", "chinese", "middle_eastern", "japanese", "global",
}


def _load_ingredient_list() -> str:
    if not os.path.exists(INGREDIENT_LIST_PATH):
        return ""
    with open(INGREDIENT_LIST_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _build_prompt(specs: list[dict], ingredient_list: str) -> str:
    """Build a single prompt for a batch of recipe specs."""
    specs_block = "\n".join(
        f"{i+1}. Name: {s['name']} | Meal: {s['meal_type']} | Type: {s['food_type']} | Cuisine: {s['cuisine']} | Role: {s.get('role','side')} | Group: {s.get('food_group','other')}"
        for i, s in enumerate(specs)
    )

    return f"""You are an expert Indian gastronomist, nutritionist, and chef.

Generate detailed recipes for the following dishes. Each dish is for ONE person (single serving).

STANDARD INGREDIENT NAMES (use these EXACT strings):
{ingredient_list[:3000]}

RECIPE SPECIFICATIONS:
{specs_block}

For EACH recipe, return a JSON object with these exact keys:
{{
  "name": "exact recipe name",
  "meal_type": "Breakfast; Lunch" or "Dinner" etc.,
  "food_type": "one of: vegan | veg | dairy | egg | non-veg",
  "food_group": "e.g. veg_curry, rice, chicken, grain_breakfast, soup, etc.",
  "difficulty": "Easy | Medium | Hard",
  "cook_time_mins": integer (upper-bound minutes),
  "calories": numeric (kcal per serving),
  "protein": numeric (grams),
  "carbohydrate": numeric (grams),
  "fat": numeric (grams),
  "portion_min": 0.5,
  "portion_typical": 1.0,
  "portion_max": 1.5,
  "role": "one of: anchor_protein | anchor_starch | anchor_veg | complete_meal | side | beverage",
  "cuisine": "must match the spec",
  "description": "formal gastronomic description under 150 words",
  "tags": "tag1; tag2; tag3; tag4; tag5",
  "source": "a plausible working URL or https://en.wikipedia.org/wiki/DishName",
  "serving_note": "e.g. 1 bowl (~250g)",
  "ingredients": "Ingredient name 50g|Ingredient name 100ml|... (pipe-delimited, only g or ml)",
  "steps": "Step 1|Step 2|... (pipe-delimited, formal tone, under 250 words total)"
}}

Rules:
- Output MUST be a single JSON array containing exactly {len(specs)} objects, in the SAME order as the specs.
- No markdown fences, no explanations — raw JSON array only.
- Ingredients must use exact names from the standard list above.
- Nutritional values must be realistic for a single serving.
- Calories must approximately equal protein*4 + carbohydrate*4 + fat*9 (within 15%).
- Description: formal, informative, no flowery adjectives, under 150 words.
- Steps: formal, short, crisp, easy for a beginner, under 250 words total.
- Tags: exactly 5 short phrases separated by semicolons.
"""


def _call_ollama(prompt: str) -> list[dict]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": TEMPERATURE, "num_predict": 3000},
            )
            raw_text = response["message"]["content"].strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()
            data = json.loads(raw_text)
            if isinstance(data, dict) and "recipes" in data:
                return data["recipes"]
            if isinstance(data, list):
                return data
            log.warning("Unexpected JSON shape, retrying...")
        except Exception as e:
            log.warning(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
    return []


def _validate_row(row: dict, spec: dict) -> tuple[bool, str]:
    """Basic validation. Returns (ok, reason)."""
    required = ["name", "calories", "protein", "carbohydrate", "fat",
                "meal_type", "food_type", "difficulty", "role", "cuisine",
                "description", "tags", "source", "ingredients", "steps"]
    for field in required:
        if field not in row or row[field] is None:
            return False, f"missing {field}"

    row["food_type"] = str(row.get("food_type", "veg")).lower().strip()
    if row["food_type"] not in VALID_FOOD_TYPES:
        return False, f"bad food_type: {row['food_type']}"

    row["difficulty"] = str(row.get("difficulty", "Easy")).strip().title()
    if row["difficulty"] not in VALID_DIFFICULTY:
        return False, f"bad difficulty: {row['difficulty']}"

    row["role"] = str(row.get("role", "side")).lower().strip()
    if row["role"] not in VALID_ROLES:
        return False, f"bad role: {row['role']}"

    row["cuisine"] = str(row.get("cuisine", "unknown")).lower().strip().replace(" ", "_")
    if row["cuisine"] not in VALID_CUISINES:
        return False, f"bad cuisine: {row['cuisine']}"

    try:
        cal = float(row["calories"])
        p = float(row["protein"])
        c = float(row["carbohydrate"])
        f = float(row["fat"])
    except (TypeError, ValueError):
        return False, "non-numeric macros"

    if not (20 <= cal <= 1200):
        return False, f"calories out of range: {cal}"

    est_cal = p * 4 + c * 4 + f * 9
    if abs(cal - est_cal) / max(cal, 1) > 0.20:
        return False, f"macro math off: est={est_cal:.0f} vs stated={cal:.0f}"

    # Check that name matches spec (loose)
    if spec["name"].lower() not in row["name"].lower():
        return False, f"name mismatch: spec={spec['name']} got={row['name']}"

    return True, ""


def main():
    log.info("=" * 60)
    log.info("Recipe Generation Agent starting")

    if not os.path.exists(SPECS_PATH):
        log.error(f"Specs file not found: {SPECS_PATH}")
        sys.exit(1)

    with open(SPECS_PATH, "r", encoding="utf-8") as f:
        all_specs = json.load(f)

    log.info(f"Loaded {len(all_specs)} recipe specs")

    ingredient_list = _load_ingredient_list()

    # Resume support
    existing_recipes = []
    existing_details = []
    if os.path.exists(OUT_RECIPES_PATH):
        existing_recipes = pd.read_csv(OUT_RECIPES_PATH).to_dict("records")
        log.info(f"Resuming — found {len(existing_recipes)} existing generated recipes")
    if os.path.exists(OUT_DETAILS_PATH):
        existing_details = pd.read_csv(OUT_DETAILS_PATH).to_dict("records")

    done_names = {r["name"] for r in existing_recipes}
    recipes_out = list(existing_recipes)
    details_out = list(existing_details)

    pending = [s for s in all_specs if s["name"] not in done_names]
    log.info(f"Pending: {len(pending)}")

    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i:i + BATCH_SIZE]
        batch_names = [b["name"] for b in batch]
        log.info(f"Batch {i//BATCH_SIZE + 1}/{(len(pending)+BATCH_SIZE-1)//BATCH_SIZE}: {batch_names}")

        prompt = _build_prompt(batch, ingredient_list)
        results = _call_ollama(prompt)

        if len(results) != len(batch):
            log.warning(f"  → Expected {len(batch)} results, got {len(results)}. Saving partial.")

        for spec, result in zip(batch, results):
            ok, reason = _validate_row(result, spec)
            if not ok:
                log.warning(f"  ✗ {spec['name']} — {reason}")
                continue

            # Build recipes row
            recipes_out.append({
                "name": result["name"],
                "category": "recipe",
                "meal_type": result["meal_type"],
                "food_type": result["food_type"],
                "food_group": result.get("food_group", spec.get("food_group", "other")),
                "difficulty": result["difficulty"],
                "cook_time_mins": int(result.get("cook_time_mins", 20)),
                "calories": float(result["calories"]),
                "protein": float(result["protein"]),
                "carbohydrate": float(result["carbohydrate"]),
                "fat": float(result["fat"]),
                "portion_min": float(result.get("portion_min", 0.5)),
                "portion_typical": float(result.get("portion_typical", 1.0)),
                "portion_max": float(result.get("portion_max", 1.5)),
                "role": result["role"],
                "cuisine": result["cuisine"],
                "description": result["description"],
                "tags": result["tags"],
                "source": result["source"],
            })

            # Build details row
            details_out.append({
                "name": result["name"],
                "serving_note": result.get("serving_note", ""),
                "ingredients": result["ingredients"],
                "steps": result["steps"],
            })

            log.info(f"  ✓ {result['name']}")

        # Checkpoint after every batch
        pd.DataFrame(recipes_out).to_csv(OUT_RECIPES_PATH, index=False, encoding="utf-8")
        pd.DataFrame(details_out).to_csv(OUT_DETAILS_PATH, index=False, encoding="utf-8")
        time.sleep(1)

    log.info(f"Done — total generated: {len(recipes_out)}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
