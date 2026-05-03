# agents/recipe_fill_agent.py
#
# Fetches pending custom recipes, checks uniqueness via fuzzy matching,
# sends unique ones to Ollama for nutritional fill, pushes results back to DB.
#
# Called by: schedulers/fill_recipes.py (Windows Task Scheduler, ~02:00)
# Model:     qwen2.5:7b or llama3.1:8b (whichever you have in Ollama)

import json
import logging
import difflib
from datetime import datetime

import ollama

from db.connection import get_connection
from db.recipes import (get_pending_custom_recipes, get_recipe_names,
                         fill_custom_recipe, reject_custom_recipe)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RECIPE-FILL] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

MODEL     = "qwen2.5:7b"   # Change to whatever model you have pulled
SIM_LIMIT = 0.85           # Similarity threshold above which we consider it a duplicate

VALID_FOOD_TYPES  = {"vegan","veg","dairy","egg","non-veg"}
VALID_FOOD_GROUPS = {
    "grain_breakfast","roti","rice","dal","paneer","veg_curry",
    "egg","chicken","fish","south_indian","chaat","kabab","toast",
    "pasta","drink","soup","dairy","fruit","seed","nut","veg_raw","other"
}
VALID_DIFFICULTY  = {"Easy","Medium","Hard"}


def _is_duplicate(new_name: str, existing_names: list[str]) -> tuple[bool, str]:
    """
    Returns (is_duplicate, closest_match).
    Uses SequenceMatcher for case-insensitive fuzzy comparison.
    """
    new_lower = new_name.lower().strip()
    for ex in existing_names:
        ratio = difflib.SequenceMatcher(None, new_lower, ex.lower().strip()).ratio()
        if ratio >= SIM_LIMIT:
            return True, ex
    return False, ""


def _build_prompt(name: str) -> str:
    return f"""You are a nutrition expert specialising in Indian cuisine.

Provide accurate nutritional information for the Indian dish: "{name}"

Return ONLY a valid JSON object in this exact structure — no explanation, no markdown:
{{
  "serving_note": "e.g. 1 bowl (~200g)",
  "meal_type": "e.g. Lunch; Dinner",
  "food_type": "one of: vegan | veg | dairy | egg | non-veg",
  "food_group": "one of: grain_breakfast | roti | rice | dal | paneer | veg_curry | egg | chicken | fish | south_indian | chaat | kabab | toast | pasta | drink | soup | dairy | fruit | seed | nut | veg_raw | other",
  "difficulty": "one of: Easy | Medium | Hard",
  "cook_time_mins": 20,
  "calories": 268.0,
  "protein": 14.0,
  "carbohydrate": 36.0,
  "fat": 8.0,
  "ingredients": "Ingredient 1 quantity|Ingredient 2 quantity|...",
  "steps": "Step 1 description|Step 2 description|..."
}}

Rules:
- All nutritional values are per standard serving (as described in serving_note)
- If this is NOT a real, recognisable Indian dish, return: {{"rejected": true, "reason": "explain why"}}
- Pipe character | separates list items in ingredients and steps fields
- Be precise: use typical Indian home-cooking serving sizes
"""


def _validate_and_clean(data: dict) -> dict | None:
    """Validate the model's JSON response and normalise fields."""
    if data.get("rejected"):
        return None

    required = ["calories","protein","carbohydrate","fat","meal_type","food_type"]
    for field in required:
        if field not in data or data[field] is None:
            log.warning(f"Missing required field: {field}")
            return None

    # Normalise enums
    data["food_type"] = data.get("food_type","veg").lower().strip()
    if data["food_type"] not in VALID_FOOD_TYPES:
        data["food_type"] = "veg"

    data["food_group"] = data.get("food_group","other").lower().strip().replace(" ","_")
    if data["food_group"] not in VALID_FOOD_GROUPS:
        data["food_group"] = "other"

    data["difficulty"] = data.get("difficulty","Medium").strip().title()
    if data["difficulty"] not in VALID_DIFFICULTY:
        data["difficulty"] = "Medium"

    # Coerce numerics
    for field in ["calories","protein","carbohydrate","fat"]:
        try:
            data[field] = float(data[field])
        except (TypeError, ValueError):
            log.warning(f"Invalid numeric value for {field}: {data[field]}")
            return None

    # Sanity bounds for Indian food (very loose)
    if not (20 <= data["calories"] <= 1200):
        log.warning(f"Calorie value out of sane range: {data['calories']}")
        return None

    data["cook_time_mins"] = int(data.get("cook_time_mins") or 20)
    return data


def run_recipe_fill():
    log.info("=" * 60)
    log.info("Recipe Fill Agent starting")
    conn = get_connection()

    pending  = get_pending_custom_recipes(conn)
    existing = get_recipe_names(conn)

    log.info(f"Pending recipes: {len(pending)} | Existing in DB: {len(existing)}")

    filled = rejected = skipped = 0

    for recipe in pending:
        rid  = recipe["id"]
        name = recipe["name"]
        log.info(f"Processing [{rid}]: '{name}'")

        # ── Uniqueness check ─────────────────────────────────────────────────
        is_dup, match = _is_duplicate(name, existing)
        if is_dup:
            reason = f"Too similar to existing recipe: '{match}'"
            log.info(f"  → REJECTED (duplicate): {reason}")
            reject_custom_recipe(conn, rid, reason)
            rejected += 1
            continue

        # ── Ollama call ──────────────────────────────────────────────────────
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": _build_prompt(name)}],
                options={"temperature": 0.1, "num_predict": 800}
            )
            raw_text = response["message"]["content"].strip()

            # Strip any accidental markdown fences
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

        except json.JSONDecodeError as e:
            log.error(f"  → JSON parse error: {e} | Raw: {raw_text[:200]}")
            skipped += 1
            continue
        except Exception as e:
            log.error(f"  → Ollama error: {e}")
            skipped += 1
            continue

        # ── Rejection signal from model ──────────────────────────────────────
        if data.get("rejected"):
            reason = data.get("reason", "Not a recognised Indian dish")
            log.info(f"  → REJECTED (AI): {reason}")
            reject_custom_recipe(conn, rid, reason)
            rejected += 1
            continue

        # ── Validate ─────────────────────────────────────────────────────────
        cleaned = _validate_and_clean(data)
        if not cleaned:
            log.warning(f"  → SKIPPED (validation failed)")
            skipped += 1
            continue

        # ── Write to DB ──────────────────────────────────────────────────────
        fill_custom_recipe(conn, rid, cleaned)
        existing.append(name)   # prevent duplicates within this batch
        filled += 1
        log.info(f"  → FILLED: {cleaned['calories']} kcal | "
                 f"P:{cleaned['protein']}g C:{cleaned['carbohydrate']}g F:{cleaned['fat']}g")

    conn.close()
    log.info(f"Done — Filled: {filled} | Rejected: {rejected} | Skipped: {skipped}")
    log.info("=" * 60)
    return {"filled": filled, "rejected": rejected, "skipped": skipped}


if __name__ == "__main__":
    run_recipe_fill()
