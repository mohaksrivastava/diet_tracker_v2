# scripts/build_recipe_specs.py
# Generates data/recipe_specs.json with exactly 150 recipes distributed across
# meal types, food types, cuisines, and roles.

import json
import os
import sys
import random
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

random.seed(42)

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "recipe_specs.json")

# ── Distribution targets ───────────────────────────────────────────────────────
MEAL_TARGET = {"Breakfast": 30, "Lunch": 40, "Dinner": 40, "Snack": 25}
FOOD_TARGET = {"vegan": 30, "veg": 45, "dairy": 15, "egg": 20, "non-veg": 40}
CUISINE_TARGET = {
    "indian": 70, "chinese": 15, "continental": 20,
    "middle_eastern": 10, "japanese": 10, "global": 10,
}
ROLE_TARGET = {
    "complete_meal": 40, "anchor_protein": 30, "anchor_starch": 25,
    "anchor_veg": 20, "side": 30, "beverage": 5,
}
DIFF_TARGET = {"Easy": 80, "Medium": 50, "Hard": 20}

# ── Carefully curated pool of exactly 150 recipes ──────────────────────────────
# Format: (name, meal_type, food_type, role, food_group, difficulty, cuisine)

POOL = [
    # ═══════════════════════════════════════════════════════════════════════════
    # INDIAN (70 recipes)
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Indian Breakfast (15) ──
    ("Poha with Sprouts", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Rava Upma", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Besan Chilla", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Masala Omelette", "Breakfast", "egg", "complete_meal", "egg", "Easy", "indian"),
    ("Aloo Paratha", "Breakfast", "veg", "complete_meal", "roti", "Medium", "indian"),
    ("Paneer Paratha", "Breakfast", "dairy", "complete_meal", "roti", "Medium", "indian"),
    ("Methi Thepla", "Breakfast", "veg", "complete_meal", "roti", "Easy", "indian"),
    ("Idli with Sambar", "Breakfast", "vegan", "complete_meal", "south_indian", "Medium", "indian"),
    ("Masala Dosa", "Breakfast", "vegan", "complete_meal", "south_indian", "Medium", "indian"),
    ("Uttapam", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Sabudana Khichdi", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Egg Bhurji", "Breakfast", "egg", "complete_meal", "egg", "Easy", "indian"),
    ("Moong Dal Cheela", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Chole Bhature", "Breakfast; Lunch", "veg", "complete_meal", "chaat", "Hard", "indian"),
    ("Bread Pakora", "Breakfast; Snack", "veg", "complete_meal", "toast", "Medium", "indian"),

    # ── Indian Lunch/Dinner Protein Anchors (16) ──
    ("Rajma Masala", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Medium", "indian"),
    ("Chana Masala", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Medium", "indian"),
    ("Dal Makhani", "Lunch; Dinner", "dairy", "anchor_protein", "dal", "Medium", "indian"),
    ("Yellow Dal Tadka", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Easy", "indian"),
    ("Sambar", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Medium", "indian"),
    ("Paneer Butter Masala", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Kadai Paneer", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Palak Paneer", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Chicken Curry", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),
    ("Butter Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),
    ("Chicken Tikka Masala", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),
    ("Rogan Josh", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Hard", "indian"),
    ("Mutton Curry", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "indian"),
    ("Fish Curry", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Medium", "indian"),
    ("Egg Curry", "Lunch; Dinner", "egg", "anchor_protein", "egg", "Easy", "indian"),
    ("Tandoori Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),

    # ── Indian Lunch/Dinner Veg Anchors (8) ──
    ("Bhindi Masala", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Aloo Gobi", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Baingan Bharta", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Dum Aloo", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Mix Veg Sabzi", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Aloo Methi", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Lauki Chana Dal", "Lunch; Dinner", "vegan", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Bharwa Baingan", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Hard", "indian"),

    # ── Indian Starches (8) ──
    ("Jeera Rice", "Lunch; Dinner", "vegan", "anchor_starch", "rice", "Easy", "indian"),
    ("Vegetable Pulao", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Medium", "indian"),
    ("Lemon Rice", "Lunch; Dinner", "vegan", "anchor_starch", "rice", "Easy", "indian"),
    ("Biryani (Veg)", "Lunch; Dinner", "veg", "complete_meal", "rice", "Hard", "indian"),
    ("Chicken Biryani", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Hard", "indian"),
    ("Tawa Roti", "Lunch; Dinner", "vegan", "anchor_starch", "roti", "Easy", "indian"),
    ("Butter Naan", "Lunch; Dinner", "dairy", "anchor_starch", "roti", "Medium", "indian"),
    ("Missi Roti", "Lunch; Dinner", "veg", "anchor_starch", "roti", "Easy", "indian"),

    # ── Indian Sides (7) ──
    ("Raita (Cucumber)", "Lunch; Dinner", "dairy", "side", "dairy", "Easy", "indian"),
    ("Papad", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Kachumber Salad", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Mint Chutney", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Onion Salad", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Pickle (Mango)", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Boondi Raita", "Lunch; Dinner", "dairy", "side", "dairy", "Easy", "indian"),

    # ── Indian Snacks (8) ──
    ("Samosa", "Snack", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Aloo Tikki", "Snack", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Pani Puri", "Snack", "vegan", "complete_meal", "chaat", "Medium", "indian"),
    ("Bhel Puri", "Snack", "vegan", "complete_meal", "chaat", "Easy", "indian"),
    ("Dahi Vada", "Snack", "dairy", "complete_meal", "chaat", "Medium", "indian"),
    ("Pav Bhaji", "Snack; Dinner", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Paneer Tikka", "Snack", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Chicken Tikka", "Snack", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),

    # ── Indian Beverages (4) ──
    ("Masala Chai", "Snack; Breakfast", "dairy", "beverage", "drink", "Easy", "indian"),
    ("Sweet Lassi", "Snack", "dairy", "beverage", "drink", "Easy", "indian"),
    ("Nimbu Pani", "Snack", "vegan", "beverage", "drink", "Easy", "indian"),
    ("Aam Panna", "Snack", "vegan", "beverage", "drink", "Easy", "indian"),

    # ── Indian Soups (4) ──
    ("Tomato Soup (Indian)", "Snack; Dinner", "vegan", "side", "soup", "Easy", "indian"),
    ("Mulligatawny Soup", "Snack; Dinner", "non-veg", "side", "soup", "Medium", "indian"),
    ("Rasam", "Snack; Dinner", "vegan", "side", "soup", "Easy", "indian"),
    ("Sweet Corn Soup", "Snack; Dinner", "vegan", "side", "soup", "Easy", "indian"),

    # ═══════════════════════════════════════════════════════════════════════════
    # CHINESE (15 recipes)
    # ═══════════════════════════════════════════════════════════════════════════
    ("Vegetable Hakka Noodles", "Lunch; Dinner", "vegan", "complete_meal", "pasta", "Medium", "chinese"),
    ("Schezwan Noodles", "Lunch; Dinner", "vegan", "complete_meal", "pasta", "Medium", "chinese"),
    ("Chicken Hakka Noodles", "Lunch; Dinner", "non-veg", "complete_meal", "pasta", "Medium", "chinese"),
    ("Veg Manchurian Gravy", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "chinese"),
    ("Gobi Manchurian Dry", "Snack", "veg", "side", "veg_curry", "Medium", "chinese"),
    ("Chilli Paneer", "Snack; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "chinese"),
    ("Chilli Chicken", "Snack; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Chicken Manchurian", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Veg Fried Rice", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Easy", "chinese"),
    ("Egg Fried Rice", "Lunch; Dinner", "egg", "anchor_starch", "rice", "Easy", "chinese"),
    ("Chicken Fried Rice", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Easy", "chinese"),
    ("Schezwan Fried Rice", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Medium", "chinese"),
    ("Veg Spring Rolls", "Snack", "veg", "side", "veg_raw", "Medium", "chinese"),
    ("Chicken Spring Rolls", "Snack", "non-veg", "side", "chicken", "Medium", "chinese"),
    ("Hot and Sour Soup", "Snack; Dinner", "veg", "side", "soup", "Easy", "chinese"),

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTINENTAL (20 recipes)
    # ═══════════════════════════════════════════════════════════════════════════
    ("Creamy Tomato Basil Soup", "Snack; Dinner", "veg", "side", "soup", "Easy", "continental"),
    ("Minestrone Soup", "Lunch; Dinner", "vegan", "complete_meal", "soup", "Medium", "continental"),
    ("Vegetable Stew", "Lunch; Dinner", "vegan", "complete_meal", "veg_curry", "Easy", "continental"),
    ("Chicken Stew", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Medium", "continental"),
    ("Grilled Vegetable Salad", "Lunch; Dinner", "vegan", "anchor_veg", "veg_raw", "Easy", "continental"),
    ("Caesar Salad (Veg)", "Lunch; Dinner", "veg", "anchor_veg", "veg_raw", "Easy", "continental"),
    ("Caesar Salad (Chicken)", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Easy", "continental"),
    ("Pasta Arrabbiata", "Lunch; Dinner", "vegan", "complete_meal", "pasta", "Easy", "continental"),
    ("Pasta Alfredo (Veg)", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Easy", "continental"),
    ("Pasta Alfredo (Chicken)", "Lunch; Dinner", "non-veg", "complete_meal", "pasta", "Medium", "continental"),
    ("Penne Pesto", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Easy", "continental"),
    ("Spaghetti Aglio e Olio", "Lunch; Dinner", "vegan", "complete_meal", "pasta", "Easy", "continental"),
    ("Veg Grilled Sandwich", "Snack; Breakfast", "veg", "complete_meal", "toast", "Easy", "continental"),
    ("Chicken Grilled Sandwich", "Snack; Breakfast", "non-veg", "complete_meal", "toast", "Easy", "continental"),
    ("Egg Salad Sandwich", "Snack; Breakfast", "egg", "complete_meal", "toast", "Easy", "continental"),
    ("French Toast", "Breakfast", "egg", "complete_meal", "toast", "Easy", "continental"),
    ("Scrambled Eggs on Toast", "Breakfast", "egg", "complete_meal", "toast", "Easy", "continental"),
    ("Herb Omelette", "Breakfast", "egg", "complete_meal", "egg", "Easy", "continental"),
    ("Shakshuka", "Breakfast; Dinner", "egg", "complete_meal", "egg", "Medium", "continental"),
    ("Spanish Omelette", "Breakfast; Dinner", "egg", "complete_meal", "egg", "Easy", "continental"),

    # ═══════════════════════════════════════════════════════════════════════════
    # MIDDLE EASTERN (10 recipes)
    # ═══════════════════════════════════════════════════════════════════════════
    ("Hummus with Pita", "Snack; Lunch", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Falafel Wrap", "Snack; Lunch", "vegan", "complete_meal", "veg_curry", "Medium", "middle_eastern"),
    ("Baba Ganoush", "Snack; Lunch", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Tabbouleh Salad", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Shawarma (Chicken)", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Medium", "middle_eastern"),
    ("Shawarma (Paneer)", "Lunch; Dinner", "dairy", "complete_meal", "paneer", "Medium", "middle_eastern"),
    ("Chicken Kebab Plate", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "middle_eastern"),
    ("Lentil Soup (Shorba)", "Snack; Dinner", "vegan", "side", "soup", "Easy", "middle_eastern"),
    ("Fattoush Salad", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Grilled Halloumi Salad", "Lunch; Dinner", "dairy", "side", "veg_raw", "Easy", "middle_eastern"),

    # ═══════════════════════════════════════════════════════════════════════════
    # JAPANESE (10 recipes)
    # ═══════════════════════════════════════════════════════════════════════════
    ("Miso Soup with Tofu", "Snack; Dinner", "vegan", "side", "soup", "Easy", "japanese"),
    ("Edamame", "Snack", "vegan", "side", "veg_raw", "Easy", "japanese"),
    ("Vegetable Sushi Rolls", "Snack; Lunch", "vegan", "side", "veg_raw", "Medium", "japanese"),
    ("Salmon Sushi Rolls", "Snack; Lunch", "non-veg", "anchor_protein", "fish", "Medium", "japanese"),
    ("Chicken Teriyaki Bowl", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Medium", "japanese"),
    ("Tofu Teriyaki Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_curry", "Medium", "japanese"),
    ("Miso Glazed Eggplant", "Lunch; Dinner", "vegan", "anchor_veg", "veg_curry", "Medium", "japanese"),
    ("Vegetable Tempura", "Snack; Dinner", "veg", "side", "veg_raw", "Medium", "japanese"),
    ("Prawn Tempura", "Snack; Dinner", "non-veg", "side", "fish", "Medium", "japanese"),
    ("Ramen (Veg)", "Lunch; Dinner", "vegan", "complete_meal", "soup", "Hard", "japanese"),

    # ═══════════════════════════════════════════════════════════════════════════
    # GLOBAL (10 recipes)
    # ═══════════════════════════════════════════════════════════════════════════
    ("Quinoa Buddha Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_raw", "Easy", "global"),
    ("Greek Yogurt Parfait", "Breakfast; Snack", "dairy", "complete_meal", "dairy", "Easy", "global"),
    ("Overnight Oats", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "global"),
    ("Avocado Toast", "Breakfast", "vegan", "complete_meal", "toast", "Easy", "global"),
    ("Smoothie Bowl (Berry)", "Breakfast; Snack", "vegan", "beverage", "fruit", "Easy", "global"),
    ("Protein Pancakes", "Breakfast", "egg", "complete_meal", "grain_breakfast", "Medium", "global"),
    ("Banana Oat Pancakes", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "global"),
    ("Shakshuka (Veg)", "Breakfast; Dinner", "veg", "complete_meal", "egg", "Medium", "global"),
    ("Minestrone (Veg)", "Lunch; Dinner", "vegan", "complete_meal", "soup", "Medium", "global"),
    ("Grilled Chicken Breast", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Easy", "global"),

    # Extra Indian ────────────────────────────────────────────────────────────────
    ("Keema Matar", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "indian"),
    ("Chicken Saag", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),
    ("Fish Amritsari", "Snack", "non-veg", "anchor_protein", "fish", "Medium", "indian"),
    ("Egg Roll", "Snack", "egg", "complete_meal", "egg", "Medium", "indian"),
    ("Stuffed Paratha (Aloo)", "Breakfast", "veg", "complete_meal", "roti", "Medium", "indian"),
    ("Dhokla", "Breakfast; Snack", "veg", "side", "grain_breakfast", "Medium", "indian"),
    ("Khandvi", "Breakfast; Snack", "veg", "side", "grain_breakfast", "Medium", "indian"),
    ("Tomato Rasam", "Snack; Dinner", "vegan", "side", "soup", "Easy", "indian"),

    # Extra Chinese ───────────────────────────────────────────────────────────────
    ("Kung Pao Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Mapo Tofu", "Lunch; Dinner", "veg", "anchor_protein", "veg_curry", "Medium", "chinese"),

    # Extra Continental ───────────────────────────────────────────────────────────
    ("Grilled Salmon", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Easy", "continental"),
    ("Beef Stew", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "continental"),

    # Extra Japanese ──────────────────────────────────────────────────────────────
    ("Gyoza (Veg)", "Snack; Dinner", "veg", "side", "veg_raw", "Medium", "japanese"),
    ("Chicken Katsu", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Medium", "japanese"),

    # Extra Middle Eastern ────────────────────────────────────────────────────────
    ("Lamb Kofta", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "middle_eastern"),
]

# ── Validate pool size ───────────────────────────────────────────────────────────
assert len(POOL) == 150, f"Pool must be exactly 150, got {len(POOL)}"

# Build JSON
specs = []
for name, meal_type, food_type, role, food_group, difficulty, cuisine in POOL:
    specs.append({
        "name": name,
        "meal_type": meal_type,
        "food_type": food_type,
        "role": role,
        "food_group": food_group,
        "difficulty": difficulty,
        "cuisine": cuisine,
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(specs, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(specs)} recipe specs to {OUTPUT}")

# Print distribution stats
mt = Counter()
for s in specs:
    for m in s["meal_type"].split(";"):
        mt[m.strip()] += 1
print("Meal types:", dict(mt))
print("Food types:", Counter(s["food_type"] for s in specs))
print("Cuisines:", Counter(s["cuisine"] for s in specs))
print("Roles:", Counter(s["role"] for s in specs))
print("Difficulty:", Counter(s["difficulty"] for s in specs))
