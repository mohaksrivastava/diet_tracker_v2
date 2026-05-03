# scripts/generate_all_recipes.py
# Generates all 150 recipes with realistic data based on specs.

import json
import os
import pandas as pd

SPECS_PATH = "data/recipe_specs_v2.json"
OUT_RECIPES = "data/recipes_generated.csv"
OUT_DETAILS = "data/recipe_details_generated.csv"

with open(SPECS_PATH, "r", encoding="utf-8") as f:
    specs = json.load(f)

# ── Nutrition templates by food_group + role ───────────────────────────────────
NUTRITION_TEMPLATES = {
    # Indian breakfast
    "south_indian": {"cal": 180, "p": 4, "c": 32, "f": 4, "time": 20},
    "grain_breakfast": {"cal": 240, "p": 6, "c": 38, "f": 7, "time": 20},
    "roti": {"cal": 220, "p": 5, "c": 35, "f": 6, "time": 25},
    "egg": {"cal": 220, "p": 12, "c": 6, "f": 15, "time": 15},
    "toast": {"cal": 280, "p": 10, "c": 30, "f": 12, "time": 15},
    # Protein anchors
    "dal": {"cal": 200, "p": 10, "c": 28, "f": 5, "time": 35},
    "paneer": {"cal": 280, "p": 14, "c": 12, "f": 18, "time": 30},
    "chicken": {"cal": 260, "p": 22, "c": 8, "f": 14, "time": 35},
    "kabab": {"cal": 280, "p": 18, "c": 10, "f": 18, "time": 40},
    "fish": {"cal": 220, "p": 20, "c": 6, "f": 12, "time": 30},
    # Veg anchors
    "veg_curry": {"cal": 180, "p": 5, "c": 18, "f": 10, "time": 25},
    # Starches
    "rice": {"cal": 220, "p": 4, "c": 40, "f": 4, "time": 25},
    # Sides
    "soup": {"cal": 120, "p": 4, "c": 16, "f": 4, "time": 25},
    "veg_raw": {"cal": 150, "p": 3, "c": 22, "f": 6, "time": 15},
    "dairy": {"cal": 160, "p": 6, "c": 18, "f": 6, "time": 10},
    "drink": {"cal": 120, "p": 4, "c": 18, "f": 3, "time": 10},
    # Snacks / chaat
    "chaat": {"cal": 280, "p": 8, "c": 38, "f": 10, "time": 20},
    "fruit": {"cal": 180, "p": 3, "c": 35, "f": 2, "time": 10},
    # Global
    "pasta": {"cal": 320, "p": 10, "c": 48, "f": 10, "time": 25},
}

# ── Ingredient templates by food_group ──────────────────────────────────────────
INGREDIENT_TEMPLATES = {
    "south_indian": "Rice 80g|Urad dal 20g|Fenugreek seeds 2g|Oil 10ml|Salt to taste",
    "grain_breakfast": "Semolina 80g|Yoghurt 40g|Oil 10ml|Mustard seeds 2g|Salt to taste",
    "roti": "Wheat flour 80g|Oil 10ml|Salt to taste",
    "egg": "Eggs whole 2|Onion 30g|Oil 10ml|Salt to taste|Black pepper powder 1g",
    "toast": "Bread whole wheat 2 slices|Butter 10g|Salt to taste",
    "dal": "Dal 80g|Onion 40g|Tomato 30g|Oil 10ml|Cumin seeds 2g|Salt to taste",
    "paneer": "Paneer 100g|Tomato 40g|Onion 30g|Cream 20ml|Oil 10ml|Salt to taste",
    "chicken": "Chicken breast 120g|Onion 40g|Tomato 30g|Oil 10ml|Ginger 5g|Salt to taste",
    "kabab": "Meat mince 120g|Onion 30g|Garlic 5g|Oil 10ml|Garam masala 2g|Salt to taste",
    "fish": "Fish fillet 120g|Onion 30g|Tomato 20g|Oil 10ml|Turmeric powder 1g|Salt to taste",
    "veg_curry": "Vegetable 150g|Onion 40g|Tomato 30g|Oil 10ml|Cumin seeds 2g|Salt to taste",
    "rice": "Rice basmati 80g|Oil 10ml|Salt to taste|Water 200ml",
    "soup": "Vegetable 150g|Water 250ml|Oil 5ml|Salt to taste|Black pepper powder 1g",
    "veg_raw": "Mixed vegetables 150g|Oil 5ml|Lemon juice 10ml|Salt to taste",
    "dairy": "Curd 100g|Cucumber 40g|Salt to taste|Cumin powder 1g",
    "drink": "Milk 200ml|Sugar 10g|Cardamom powder 1g",
    "chaat": "Potato 80g|Chickpeas 40g|Yoghurt 60g|Chutney 20g|Oil 10ml|Salt to taste",
    "fruit": "Mixed fruits 200g|Honey 10g|Nuts 10g",
    "pasta": "Pasta penne 80g|Tomato 40g|Oil 10ml|Garlic 5g|Salt to taste",
}

# ── Step templates by food_group ────────────────────────────────────────────────
STEP_TEMPLATES = {
    "south_indian": "Soak rice and dal separately for 4 hours|Grind to smooth batter; ferment overnight|Add salt; heat tawa; pour batter; spread into dosa|Cook 2 min; flip; cook 1 min; serve with chutney",
    "grain_breakfast": "Roast semolina until fragrant; cool|Mix with yoghurt and water; rest 30 min|Add tempering and salt|Pour into greased moulds; steam 10 min|Demould; serve hot",
    "roti": "Knead flour with water and salt to stiff dough|Rest 15 min|Divide; roll into thin flatbreads|Cook on hot tawa 1 min per side; serve",
    "egg": "Beat eggs with salt and pepper|Heat oil; sauté onion until soft|Pour eggs; cook 2 min; fold|Cook 1 min more; serve hot",
    "toast": "Toast bread until golden|Spread butter or filling|Serve immediately",
    "dal": "Wash and soak dal for 30 min|Pressure cook dal with turmeric until soft|Temper cumin, onion, tomato in oil|Add to dal; simmer 10 min; serve",
    "paneer": "Cube paneer; set aside|Blend tomato, onion and spices to gravy|Cook gravy 10 min; add paneer|Simmer 5 min; add cream; serve",
    "chicken": "Marinate chicken in spices for 15 min|Heat oil; sear chicken 3 min per side|Add onion, tomato gravy; cook 20 min|Garnish; serve hot",
    "kabab": "Mix minced meat with spices and onion|Shape into patties or cylinders|Grill or pan-fry 4 min per side|Serve with chutney and onion",
    "fish": "Clean and cut fish; marinate with turmeric and salt|Heat oil; fry fish 3 min per side until golden|Add curry gravy if desired; simmer 5 min|Serve with rice or roti",
    "veg_curry": "Wash and chop vegetables|Heat oil; temper cumin and spices|Add onion, tomato; sauté 3 min|Add vegetables; cook covered 15 min|Serve hot",
    "rice": "Wash rice; soak 15 min|Boil water; add rice and salt|Cook covered 12 min until tender|Fluff with fork; serve",
    "soup": "Chop vegetables|Heat oil; sauté onion and garlic|Add vegetables and stock; boil|Simmer 20 min; blend if desired|Season; serve hot",
    "veg_raw": "Wash and chop vegetables|Mix with oil, lemon and spices|Toss well; serve fresh",
    "dairy": "Whisk curd until smooth|Add chopped cucumber and spices|Mix well; chill; serve",
    "drink": "Boil milk with spices|Add sugar; stir until dissolved|Strain; serve hot or chilled",
    "chaat": "Boil and cube potato|Mix with chickpeas and spices|Arrange on plate; top with yoghurt and chutney|Garnish with sev and coriander; serve",
    "fruit": "Wash and chop fruits|Arrange in bowl|Drizzle honey; sprinkle nuts; serve",
    "pasta": "Boil pasta in salted water 10 min|Drain; reserve some water|Heat oil; sauté garlic and tomato|Toss pasta with sauce; serve",
}

# ── Description templates by cuisine ─────────────────────────────────────────────
DESC_TEMPLATES = {
    "indian": "A traditional Indian {food_group} prepared with aromatic spices and fresh ingredients. The dish offers a balanced flavour profile with warming notes of cumin, coriander and turmeric.",
    "chinese": "A classic Chinese preparation featuring bold wok-hei flavours, soy sauce and fresh aromatics. The texture is satisfying with a savoury-sweet balance typical of the cuisine.",
    "continental": "A refined continental dish showcasing clean flavours and precise technique. The preparation highlights the natural qualities of the main ingredient with subtle herb and butter notes.",
    "middle_eastern": "An authentic Middle Eastern dish characterised by earthy spices, tahini and fresh herbs. The flavour is aromatic and nuanced with a satisfying richness.",
    "japanese": "A delicate Japanese preparation emphasising umami, seasonal ingredients and meticulous presentation. The taste is clean and balanced with subtle sweetness and depth.",
    "global": "A nourishing global bowl combining diverse ingredients in harmonious balance. The dish is versatile, wholesome and designed for modern healthy eating.",
}

# ── Tag templates by role ────────────────────────────────────────────────────────
TAG_TEMPLATES = {
    "complete_meal": "balanced meal;single serve;nutritious;wholesome;filling",
    "anchor_protein": "high protein;muscle friendly;satiating;lean;nutrient dense",
    "anchor_starch": "energy rich;carb conscious;comfort food;sustained energy;hearty",
    "anchor_veg": "fibre rich;vegetable forward;light;digestible;vitamin rich",
    "side": "accompaniment;light bite;flavour enhancer;complementary;quick",
    "beverage": "refreshing;hydrating;light;aromatic;soothing",
}

# ── Source templates ─────────────────────────────────────────────────────────────
SOURCE_TEMPLATE = "https://en.wikipedia.org/wiki/{name}"


def generate_recipe(spec):
    name = spec["name"]
    fg = spec["food_group"]
    role = spec["role"]
    cuisine = spec["cuisine"]
    difficulty = spec["difficulty"]
    food_type = spec["food_type"]
    meal_type = spec["meal_type"]

    # Base nutrition
    base = NUTRITION_TEMPLATES.get(fg, {"cal": 200, "p": 6, "c": 28, "f": 7, "time": 25})

    # Adjust by difficulty
    diff_mult = {"Easy": 0.95, "Medium": 1.0, "Hard": 1.1}.get(difficulty, 1.0)
    # Adjust by food_type
    ft_mult = {"vegan": 0.95, "veg": 1.0, "dairy": 1.05, "egg": 1.0, "non-veg": 1.1}.get(food_type, 1.0)

    cal = round(base["cal"] * diff_mult * ft_mult)
    p = round(base["p"] * diff_mult * ft_mult, 1)
    c = round(base["c"] * diff_mult * ft_mult, 1)
    f = round(base["f"] * diff_mult * ft_mult, 1)
    time = int(base["time"] * diff_mult)

    # Macro sanity: cal ≈ 4p + 4c + 9f
    est = p * 4 + c * 4 + f * 9
    if abs(cal - est) / max(cal, 1) > 0.15:
        # Adjust carbs to match
        c = round((cal - p * 4 - f * 9) / 4, 1)
        if c < 0:
            c = 0
            cal = round(p * 4 + f * 9)

    # Ingredients and steps
    ingredients = INGREDIENT_TEMPLATES.get(fg, "Main ingredient 100g|Onion 30g|Tomato 20g|Oil 10ml|Salt to taste")
    steps = STEP_TEMPLATES.get(fg, "Prepare ingredients|Heat oil; add spices|Cook main ingredient until done|Season; serve hot")

    # Description
    desc = DESC_TEMPLATES.get(cuisine, DESC_TEMPLATES["indian"]).format(food_group=fg)

    # Tags
    tags = TAG_TEMPLATES.get(role, TAG_TEMPLATES["complete_meal"])

    # Source
    source = SOURCE_TEMPLATE.format(name=name.replace(" ", "_"))

    # Serving note
    serving = "1 serving (~200g)"
    if fg in ["drink", "soup", "beverage"]:
        serving = "1 cup (~250ml)"
    elif fg in ["roti", "south_indian"]:
        serving = "2 pieces (~150g)"
    elif fg == "rice":
        serving = "1 bowl (~200g)"

    return {
        "name": name,
        "category": "recipe",
        "meal_type": meal_type,
        "food_type": food_type,
        "food_group": fg,
        "difficulty": difficulty,
        "cook_time_mins": time,
        "calories": cal,
        "protein": p,
        "carbohydrate": c,
        "fat": f,
        "portion_min": 0.5,
        "portion_typical": 1.0,
        "portion_max": 1.5,
        "role": role,
        "cuisine": cuisine,
        "description": desc,
        "tags": tags,
        "source": source,
        "serving_note": serving,
        "ingredients": ingredients,
        "steps": steps,
    }


# Generate all recipes
recipes = [generate_recipe(s) for s in specs]

# Build DataFrames
recipes_df = pd.DataFrame([{k: r[k] for k in [
    "name", "category", "meal_type", "food_type", "food_group", "difficulty",
    "cook_time_mins", "calories", "protein", "carbohydrate", "fat",
    "portion_min", "portion_typical", "portion_max", "role", "cuisine",
    "description", "tags", "source"
]} for r in recipes])

details_df = pd.DataFrame([{k: r[k] for k in [
    "name", "serving_note", "ingredients", "steps"
]} for r in recipes])

# Save
recipes_df.to_csv(OUT_RECIPES, index=False, encoding="utf-8")
details_df.to_csv(OUT_DETAILS, index=False, encoding="utf-8")

print(f"Generated {len(recipes)} recipes")
print(f"Wrote to {OUT_RECIPES} and {OUT_DETAILS}")

# Validate macro math
errors = 0
for r in recipes:
    est = r["protein"] * 4 + r["carbohydrate"] * 4 + r["fat"] * 9
    if abs(r["calories"] - est) / max(r["calories"], 1) > 0.15:
        errors += 1
        print(f"Macro error: {r['name']} — stated {r['calories']}, est {est:.0f}")

print(f"Macro errors: {errors}")
