# scripts/build_recipe_specs_v2.py
# Generates data/recipe_specs_v2.json with exactly 150 NEW strict single-dish
# recipes that do NOT duplicate existing DB names (exact or fuzzy).

import json
import os
import sys
import difflib
import random
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

random.seed(42)

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "recipe_specs_v2.json")
EXISTING_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "existing_recipes.json")

# ── Load existing names ────────────────────────────────────────────────────────
existing_names = []
if os.path.exists(EXISTING_JSON):
    with open(EXISTING_JSON, "r", encoding="utf-8") as f:
        existing_names = [item["name"].lower().strip() for item in json.load(f)]

print(f"Loaded {len(existing_names)} existing names from DB")

# ── Fuzzy duplicate check ──────────────────────────────────────────────────────
SIM_LIMIT = 0.80

def is_duplicate(new_name: str, already_selected: list[str]) -> tuple[bool, str]:
    new_lower = new_name.lower().strip()
    all_names = existing_names + [a.lower().strip() for a in already_selected]
    for ex in all_names:
        if new_lower == ex:
            return True, ex
        ratio = difflib.SequenceMatcher(None, new_lower, ex).ratio()
        if ratio >= SIM_LIMIT:
            return True, ex
    return False, ""

# ── Target distributions ───────────────────────────────────────────────────────
TARGET_CUISINE = {"indian": 70, "chinese": 15, "continental": 20, "middle_eastern": 10, "japanese": 10, "global": 10}
TARGET_FOOD = {"vegan": 30, "veg": 45, "dairy": 15, "egg": 20, "non-veg": 40}
TARGET_ROLE = {"complete_meal": 40, "anchor_protein": 30, "anchor_starch": 25, "anchor_veg": 20, "side": 30, "beverage": 5}
TARGET_DIFF = {"Easy": 80, "Medium": 50, "Hard": 20}

# ── Curated realistic recipe pool ──────────────────────────────────────────────
RAW_POOL = [
    # INDIAN BREAKFAST (25) ─────────────────────────────────────────────────────
    ("Rava Idli", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Ragi Idli", "Breakfast", "vegan", "complete_meal", "south_indian", "Easy", "indian"),
    ("Set Dosa", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Neer Dosa", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Ragi Dosa", "Breakfast", "vegan", "complete_meal", "south_indian", "Easy", "indian"),
    ("Wheat Dosa", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Onion Uttapam", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Tomato Uttapam", "Breakfast", "veg", "complete_meal", "south_indian", "Easy", "indian"),
    ("Adai", "Breakfast", "vegan", "complete_meal", "south_indian", "Medium", "indian"),
    ("Kuzhi Paniyaram", "Breakfast", "veg", "complete_meal", "south_indian", "Medium", "indian"),
    ("Puttu", "Breakfast", "vegan", "complete_meal", "south_indian", "Easy", "indian"),
    ("Appam", "Breakfast", "vegan", "complete_meal", "south_indian", "Medium", "indian"),
    ("Nei Appam", "Breakfast", "veg", "complete_meal", "south_indian", "Medium", "indian"),
    ("Mysore Bonda", "Breakfast", "veg", "complete_meal", "south_indian", "Medium", "indian"),
    ("Maddur Vada", "Breakfast", "veg", "complete_meal", "south_indian", "Medium", "indian"),
    ("Thalipeeth", "Breakfast", "veg", "complete_meal", "grain_breakfast", "Medium", "indian"),
    ("Sabudana Vada", "Breakfast", "veg", "complete_meal", "grain_breakfast", "Medium", "indian"),
    ("Moong Dal Khichdi", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Rava Kesari", "Breakfast", "veg", "side", "grain_breakfast", "Easy", "indian"),
    ("Avalakki", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Kanda Poha", "Breakfast", "vegan", "complete_meal", "grain_breakfast", "Easy", "indian"),
    ("Khaman Dhokla", "Breakfast; Snack", "veg", "side", "grain_breakfast", "Medium", "indian"),
    ("Methi Muthia", "Breakfast; Snack", "veg", "side", "grain_breakfast", "Medium", "indian"),
    ("Gobi Paratha", "Breakfast", "veg", "complete_meal", "roti", "Medium", "indian"),
    ("Mixed Dal Paratha", "Breakfast", "veg", "complete_meal", "roti", "Medium", "indian"),
    ("Sattu Paratha", "Breakfast", "vegan", "complete_meal", "roti", "Medium", "indian"),

    # EGG (20) ────────────────────────────────────────────────────────────────────
    ("Egg Bhurji", "Breakfast", "egg", "complete_meal", "egg", "Easy", "indian"),
    ("Egg Korma", "Breakfast", "egg", "complete_meal", "egg", "Medium", "indian"),
    ("Egg Sandwich", "Breakfast", "egg", "complete_meal", "toast", "Easy", "indian"),
    ("Egg Paratha", "Breakfast", "egg", "complete_meal", "roti", "Medium", "indian"),
    ("Egg Roll", "Breakfast", "egg", "complete_meal", "roti", "Medium", "indian"),
    ("Egg Biryani", "Breakfast", "egg", "complete_meal", "rice", "Medium", "indian"),
    ("Egg Pulao", "Breakfast", "egg", "complete_meal", "rice", "Easy", "indian"),
    ("Egg Keema", "Breakfast", "egg", "complete_meal", "egg", "Easy", "indian"),
    ("Egg Cutlet", "Breakfast", "egg", "complete_meal", "veg_curry", "Easy", "indian"),
    ("Egg Patty", "Breakfast", "egg", "complete_meal", "chaat", "Easy", "indian"),
    ("Egg Vada", "Breakfast", "egg", "complete_meal", "south_indian", "Medium", "indian"),
    ("Egg Spring Roll", "Breakfast", "egg", "complete_meal", "chaat", "Medium", "indian"),
    ("Egg Frankie", "Breakfast", "egg", "complete_meal", "chaat", "Easy", "indian"),
    ("Egg Samosa", "Breakfast", "egg", "complete_meal", "chaat", "Medium", "indian"),
    ("Egg Kofta", "Breakfast", "egg", "complete_meal", "veg_curry", "Easy", "indian"),
    ("Egg Toast", "Breakfast", "egg", "complete_meal", "toast", "Easy", "indian"),
    ("Egg Bhurji Roll", "Breakfast", "egg", "complete_meal", "roti", "Easy", "indian"),
    ("Scrambled Eggs", "Breakfast", "egg", "complete_meal", "egg", "Easy", "continental"),
    ("Boiled Eggs", "Breakfast", "egg", "complete_meal", "egg", "Easy", "global"),
    ("Omelette", "Breakfast", "egg", "complete_meal", "egg", "Easy", "continental"),

    # INDIAN LUNCH/DINNER PROTEIN (20) ────────────────────────────────────────────
    ("Amritsari Chole", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Medium", "indian"),
    ("Kala Chana", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Easy", "indian"),
    ("Green Moong Dal", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Easy", "indian"),
    ("Dal Panchmel", "Lunch; Dinner", "vegan", "anchor_protein", "dal", "Medium", "indian"),
    ("Dal Bukhara", "Lunch; Dinner", "dairy", "anchor_protein", "dal", "Medium", "indian"),
    ("Dhansak", "Lunch; Dinner", "non-veg", "anchor_protein", "dal", "Hard", "indian"),
    ("Paneer Lababdar", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Paneer Pasanda", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Hard", "indian"),
    ("Paneer Korma", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Paneer Jalfrezi", "Lunch; Dinner", "dairy", "anchor_protein", "paneer", "Medium", "indian"),
    ("Chicken Korma", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),
    ("Chicken Vindaloo", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Hard", "indian"),
    ("Chicken Kolhapuri", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Hard", "indian"),
    ("Laal Maas", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Hard", "indian"),
    ("Fish Moilee", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Medium", "indian"),
    ("Meen Curry", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Medium", "indian"),
    ("Prawn Balchao", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Hard", "indian"),
    ("Prawn Malai Curry", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Medium", "indian"),
    ("Keema Matar", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "indian"),
    ("Kadai Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "indian"),

    # INDIAN VEG (15) ─────────────────────────────────────────────────────────────
    ("Aloo Matar", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Aloo Palak", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Jeera Aloo", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Dahi Aloo", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Gobi Matar", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Phool Gobi", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Bhindi Do Pyaza", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Karela Masala", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Bharwa Karela", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Hard", "indian"),
    ("Lauki Kofta", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Navratan Korma", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Hard", "indian"),
    ("Veg Kolhapuri", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Hard", "indian"),
    ("Dum Aloo", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Medium", "indian"),
    ("Kashmiri Aloo", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),
    ("Aloo Posto", "Lunch; Dinner", "veg", "anchor_veg", "veg_curry", "Easy", "indian"),

    # INDIAN STARCHES (12) ────────────────────────────────────────────────────────
    ("Ghee Rice", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Easy", "indian"),
    ("Curd Rice", "Lunch; Dinner", "dairy", "anchor_starch", "rice", "Easy", "indian"),
    ("Methi Rice", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Easy", "indian"),
    ("Peas Pulao", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Easy", "indian"),
    ("Mint Pulao", "Lunch; Dinner", "veg", "anchor_starch", "rice", "Easy", "indian"),
    ("Hydrabadi Biryani", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Hard", "indian"),
    ("Lucknowi Biryani", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Hard", "indian"),
    ("Roomali Roti", "Lunch; Dinner", "vegan", "anchor_starch", "roti", "Easy", "indian"),
    ("Kulcha", "Lunch; Dinner", "veg", "anchor_starch", "roti", "Medium", "indian"),
    ("Makki Di Roti", "Lunch; Dinner", "vegan", "anchor_starch", "roti", "Easy", "indian"),
    ("Bajra Roti", "Lunch; Dinner", "vegan", "anchor_starch", "roti", "Easy", "indian"),
    ("Jowar Roti", "Lunch; Dinner", "vegan", "anchor_starch", "roti", "Easy", "indian"),

    # INDIAN SIDES (8) ────────────────────────────────────────────────────────────
    ("Pudina Chutney", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Coconut Chutney", "Lunch; Dinner", "vegan", "side", "veg_raw", "Easy", "indian"),
    ("Gajar Ka Halwa", "Lunch; Dinner", "dairy", "side", "veg_raw", "Medium", "indian"),
    ("Moong Dal Halwa", "Lunch; Dinner", "dairy", "side", "veg_raw", "Hard", "indian"),
    ("Gulab Jamun", "Lunch; Dinner", "dairy", "side", "veg_raw", "Medium", "indian"),
    ("Rasmalai", "Lunch; Dinner", "dairy", "side", "veg_raw", "Medium", "indian"),
    ("Kulfi", "Lunch; Dinner", "dairy", "side", "veg_raw", "Easy", "indian"),
    ("Falooda", "Lunch; Dinner", "dairy", "side", "veg_raw", "Medium", "indian"),

    # INDIAN SNACKS (8) ───────────────────────────────────────────────────────────
    ("Kachori", "Snack", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Dahi Puri", "Snack", "veg", "complete_meal", "chaat", "Easy", "indian"),
    ("Ragda Pattice", "Snack", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Dahi Bhalla", "Snack", "dairy", "complete_meal", "chaat", "Medium", "indian"),
    ("Misal Pav", "Snack", "veg", "complete_meal", "chaat", "Medium", "indian"),
    ("Shami Kebab", "Snack", "non-veg", "anchor_protein", "kabab", "Medium", "indian"),
    ("Galouti Kebab", "Snack", "non-veg", "anchor_protein", "kabab", "Hard", "indian"),
    ("Soya Chaap", "Snack", "vegan", "complete_meal", "veg_curry", "Medium", "indian"),

    # INDIAN BEVERAGES (5) ────────────────────────────────────────────────────────
    ("Masala Chai", "Snack; Breakfast", "dairy", "beverage", "drink", "Easy", "indian"),
    ("Sweet Lassi", "Snack", "dairy", "beverage", "drink", "Easy", "indian"),
    ("Aam Panna", "Snack", "vegan", "beverage", "drink", "Easy", "indian"),
    ("Jaljeera", "Snack", "vegan", "beverage", "drink", "Easy", "indian"),
    ("Badam Milk", "Snack; Breakfast", "dairy", "beverage", "drink", "Easy", "indian"),

    # CHINESE (15) ────────────────────────────────────────────────────────────────
    ("Kung Pao Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Mapo Tofu", "Lunch; Dinner", "veg", "anchor_protein", "veg_curry", "Medium", "chinese"),
    ("Sweet and Sour Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Lemon Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Medium", "chinese"),
    ("Garlic Chicken", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Easy", "chinese"),
    ("Chilli Garlic Noodles", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Easy", "chinese"),
    ("Hakka Noodles", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Medium", "chinese"),
    ("Triple Schezwan Rice", "Lunch; Dinner", "veg", "complete_meal", "rice", "Medium", "chinese"),
    ("Manchow Soup", "Snack; Dinner", "veg", "side", "soup", "Easy", "chinese"),
    ("Wonton Soup", "Snack; Dinner", "non-veg", "side", "soup", "Medium", "chinese"),
    ("Sweet and Sour Pork", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "chinese"),
    ("Peking Duck", "Lunch; Dinner", "non-veg", "anchor_protein", "chicken", "Hard", "chinese"),
    ("Char Siu", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Hard", "chinese"),
    ("Congee", "Breakfast", "veg", "complete_meal", "grain_breakfast", "Easy", "chinese"),
    ("Dim Sum", "Snack", "veg", "side", "veg_raw", "Medium", "chinese"),

    # CONTINENTAL (20) ────────────────────────────────────────────────────────────
    ("Grilled Salmon", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Easy", "continental"),
    ("Beef Stew", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "continental"),
    ("Lamb Chops", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "continental"),
    ("Pork Ribs", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Hard", "continental"),
    ("Cream of Mushroom Soup", "Snack; Dinner", "veg", "side", "soup", "Easy", "continental"),
    ("Pumpkin Soup", "Snack; Dinner", "veg", "side", "soup", "Easy", "continental"),
    ("French Onion Soup", "Snack; Dinner", "veg", "side", "soup", "Medium", "continental"),
    ("Ratatouille", "Lunch; Dinner", "vegan", "anchor_veg", "veg_curry", "Medium", "continental"),
    ("Nicoise Salad", "Lunch; Dinner", "non-veg", "complete_meal", "veg_raw", "Easy", "continental"),
    ("Quiche Lorraine", "Lunch; Dinner", "egg", "complete_meal", "egg", "Hard", "continental"),
    ("Beef Bourguignon", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "continental"),
    ("Coq au Vin", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Hard", "continental"),
    ("Shepherds Pie", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Medium", "continental"),
    ("Fish and Chips", "Lunch; Dinner", "non-veg", "complete_meal", "fish", "Medium", "continental"),
    ("Bangers and Mash", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Easy", "continental"),
    ("Chicken Cordon Bleu", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Hard", "continental"),
    ("Wiener Schnitzel", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Medium", "continental"),
    ("Beef Wellington", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "continental"),
    ("Steak Diane", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "continental"),
    ("Osso Buco", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "continental"),

    # MIDDLE EASTERN (10) ─────────────────────────────────────────────────────────
    ("Lamb Kofta", "Lunch; Dinner", "non-veg", "anchor_protein", "kabab", "Medium", "middle_eastern"),
    ("Mutabbal", "Snack; Lunch", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Muhammara", "Snack; Lunch", "vegan", "side", "veg_raw", "Easy", "middle_eastern"),
    ("Dolma", "Lunch; Dinner", "vegan", "anchor_veg", "veg_curry", "Medium", "middle_eastern"),
    ("Kibbeh", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Hard", "middle_eastern"),
    ("Mujaddara", "Lunch; Dinner", "vegan", "complete_meal", "rice", "Easy", "middle_eastern"),
    ("Mansaf", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Hard", "middle_eastern"),
    ("Maqluba", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Hard", "middle_eastern"),
    ("Knafeh", "Snack", "dairy", "side", "veg_raw", "Hard", "middle_eastern"),
    ("Baklava", "Snack", "veg", "side", "veg_raw", "Hard", "middle_eastern"),

    # JAPANESE (10) ───────────────────────────────────────────────────────────────
    ("Gyoza", "Snack; Dinner", "veg", "side", "veg_raw", "Medium", "japanese"),
    ("Chicken Katsu", "Lunch; Dinner", "non-veg", "complete_meal", "chicken", "Medium", "japanese"),
    ("Yakitori", "Snack", "non-veg", "anchor_protein", "chicken", "Medium", "japanese"),
    ("Unagi Don", "Lunch; Dinner", "non-veg", "complete_meal", "fish", "Medium", "japanese"),
    ("Onigiri", "Snack; Lunch", "vegan", "side", "veg_raw", "Easy", "japanese"),
    ("Miso Glazed Salmon", "Lunch; Dinner", "non-veg", "anchor_protein", "fish", "Medium", "japanese"),
    ("Tonkatsu", "Lunch; Dinner", "non-veg", "complete_meal", "kabab", "Medium", "japanese"),
    ("Yakisoba", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Medium", "japanese"),
    ("Soba Noodles", "Lunch; Dinner", "vegan", "complete_meal", "pasta", "Easy", "japanese"),
    ("Udon Noodles", "Lunch; Dinner", "veg", "complete_meal", "pasta", "Easy", "japanese"),

    # GLOBAL (10) ──────────────────────────────────────────────────────────────────
    ("Acai Bowl", "Breakfast; Snack", "vegan", "beverage", "fruit", "Easy", "global"),
    ("Turkey Sandwich", "Snack; Breakfast", "non-veg", "complete_meal", "toast", "Easy", "global"),
    ("Tuna Salad", "Lunch; Dinner", "non-veg", "complete_meal", "veg_raw", "Easy", "global"),
    ("Cobb Salad", "Lunch; Dinner", "non-veg", "complete_meal", "veg_raw", "Easy", "global"),
    ("Falafel Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_raw", "Easy", "global"),
    ("Hummus Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_raw", "Easy", "global"),
    ("Buddha Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_raw", "Easy", "global"),
    ("Poke Bowl", "Lunch; Dinner", "non-veg", "complete_meal", "fish", "Easy", "global"),
    ("Grain Bowl", "Lunch; Dinner", "vegan", "complete_meal", "veg_raw", "Easy", "global"),
    ("Burrito Bowl", "Lunch; Dinner", "non-veg", "complete_meal", "rice", "Easy", "global"),
]

# ── Filter duplicates ────────────────────────────────────────────────────────────
selected = []
rejected = []
for name, meal_type, food_type, role, food_group, difficulty, cuisine in RAW_POOL:
    dup, match = is_duplicate(name, [s[0] for s in selected])
    if dup:
        rejected.append((name, match))
        continue
    selected.append((name, meal_type, food_type, role, food_group, difficulty, cuisine))

print(f"Selected: {len(selected)} | Rejected (duplicate): {len(rejected)}")
if rejected:
    print("\nRejected duplicates:")
    for name, match in rejected[:20]:
        print(f"  - {name} (matched: {match})")
    if len(rejected) > 20:
        print(f"  ... and {len(rejected) - 20} more")

# If we have more than 150, trim by prioritizing diversity
if len(selected) > 150:
    print(f"\nTrimming from {len(selected)} to 150...")
    # Shuffle to avoid bias
    random.shuffle(selected)
    # Greedy selection to hit cuisine targets
    cuisine_counts = Counter()
    food_counts = Counter()
    role_counts = Counter()
    diff_counts = Counter()
    final_selected = []
    remaining = list(selected)
    
    for _ in range(150):
        best_idx = None
        best_score = -9999
        for idx, (name, meal_type, food_type, role, food_group, difficulty, cuisine) in enumerate(remaining):
            score = 0
            # Prefer cuisines that are under target
            score += max(0, TARGET_CUISINE.get(cuisine, 0) - cuisine_counts[cuisine]) * 10
            score += max(0, TARGET_FOOD.get(food_type, 0) - food_counts[food_type]) * 5
            score += max(0, TARGET_ROLE.get(role, 0) - role_counts[role]) * 3
            score += max(0, TARGET_DIFF.get(difficulty, 0) - diff_counts[difficulty]) * 1
            if score > best_score:
                best_score = score
                best_idx = idx
        
        if best_idx is not None:
            recipe = remaining.pop(best_idx)
            final_selected.append(recipe)
            cuisine_counts[recipe[6]] += 1
            food_counts[recipe[2]] += 1
            role_counts[recipe[3]] += 1
            diff_counts[recipe[5]] += 1
    
    selected = final_selected

# ── Build JSON ───────────────────────────────────────────────────────────────────
specs = []
for name, meal_type, food_type, role, food_group, difficulty, cuisine in selected:
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

print(f"\nWrote {len(specs)} recipe specs to {OUTPUT}")

# Print distribution stats
mt = Counter()
for s in specs:
    for m in s["meal_type"].split(";"):
        mt[m.strip()] += 1
print("\nMeal types:", dict(mt))
print("Food types:", Counter(s["food_type"] for s in specs))
print("Cuisines:", Counter(s["cuisine"] for s in specs))
print("Roles:", Counter(s["role"] for s in specs))
print("Difficulty:", Counter(s["difficulty"] for s in specs))
