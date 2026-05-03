#!/usr/bin/env python3
"""
data/seed_recipes.py
====================
Seeds users and the original 83 base recipes (+ raw ingredients)
into the consolidated recipes table.

Run from the project root after setup_db_complete.sql:

    python data/seed_recipes.py

Prerequisites:
    - setup/setup_db_complete.sql already run in Supabase SQL Editor
    - .env file with SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASS
"""

import sys, os, bcrypt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection, execute


# ── Edit users before running ─────────────────────────────────────────────────

USERS = [
    {"name": "Mohak",    "password": "change_me_1", "daily_cal": 2200, "num_meals": 2, "food_pref": "non-veg"},
    {"name": "Ish",      "password": "change_me_2", "daily_cal": 1800, "num_meals": 3, "food_pref": "non-veg"},
    {"name": "Varshita", "password": "change_me_3", "daily_cal": 1300, "num_meals": 4, "food_pref": "non-veg"},
    {"name": "Anushka",  "password": "change_me_4", "daily_cal": 1500, "num_meals": 4, "food_pref": "vegan"},
]


# ── Recipe data ───────────────────────────────────────────────────────────────
# Each dict maps directly to the consolidated recipes table columns.
# Fields: name, category, meal_type, food_type, food_group, difficulty,
#         cook_time_mins, calories, protein, carbohydrate, fat,
#         portion_min, portion_typical, portion_max, role, cuisine,
#         serving_note, ingredients, steps

RECIPES = [

  # ── GRAIN BREAKFASTS ────────────────────────────────────────────────────────
  dict(name="Poha", category="recipe", meal_type="Breakfast",
       food_type="vegan", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=15,
       calories=280, protein=6, carbohydrate=52, fat=5,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="north_indian",
       serving_note="1 plate (~220g)",
       ingredients="Flattened rice (poha) 100g|Onion 60g (finely chopped)|Mustard seeds 1 tsp|Curry leaves 6|Green chilli 1|Turmeric ¼ tsp|Oil 8ml|Salt to taste|Lemon juice 1 tsp|Coriander 2 tbsp|Peanuts 15g (optional)",
       steps="Rinse poha in water 30 sec; drain well — it should be soft but not mushy|Heat oil; add mustard seeds; wait till they pop|Add curry leaves, green chilli, onion; cook 3 min|Add peanuts if using; cook 1 min|Add poha, turmeric, salt; mix gently; cover and cook 2 min|Finish with lemon juice and coriander"),

  dict(name="Upma", category="recipe", meal_type="Breakfast",
       food_type="vegan", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=20,
       calories=295, protein=7, carbohydrate=50, fat=7,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="south_indian",
       serving_note="1 bowl (~240g)",
       ingredients="Semolina (rava) 80g|Onion 60g|Green chilli 1|Ginger ½ tsp|Mustard seeds 1 tsp|Curry leaves 6|Urad dal 1 tsp|Channa dal 1 tsp|Oil 10ml|Water 240ml|Salt to taste|Coriander 2 tbsp|Lemon juice ½ tsp",
       steps="Dry roast rava on medium heat 4 min until fragrant; set aside|Heat oil; add mustard seeds; pop|Add urad dal, channa dal; cook till golden|Add curry leaves, ginger, green chilli, onion; cook 3 min|Add water and salt; bring to boil|Add roasted rava stirring continuously to prevent lumps|Cover; cook 3 min; fluff with fork|Finish lemon and coriander"),

  dict(name="Besan Chilla", category="recipe", meal_type="Breakfast",
       food_type="vegan", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=15,
       calories=265, protein=12, carbohydrate=34, fat=8,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="north_indian",
       serving_note="2 chillas (~180g)",
       ingredients="Besan (gram flour) 80g|Onion 40g (finely chopped)|Tomato 30g (chopped)|Green chilli 1|Coriander 2 tbsp|Cumin seeds ½ tsp|Turmeric ¼ tsp|Oil 8ml|Water ~120ml|Salt to taste",
       steps="Mix besan with onion, tomato, chilli, coriander, cumin, turmeric, salt|Add water gradually to make pourable batter (consistency of dosa batter)|Heat non-stick pan; lightly oil|Pour ladle of batter; spread thin; cook 2 min until edges lift|Flip; cook 1 min; serve with chutney"),

  dict(name="Masala Omelette", category="recipe", meal_type="Breakfast",
       food_type="egg", food_group="egg", difficulty="Easy", cook_time_mins=8,
       calories=235, protein=16, carbohydrate=4, fat=17,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_protein", cuisine="north_indian",
       serving_note="2-egg omelette (~150g)",
       ingredients="Eggs 2|Onion 30g (finely chopped)|Tomato 20g (chopped)|Green chilli 1|Coriander 1 tbsp|Turmeric a pinch|Oil 8ml|Salt and pepper",
       steps="Beat eggs with all ingredients|Heat oil in pan on medium|Pour egg mixture; let set 1 min|Fold in half; cook 30 sec more|Serve immediately"),

  dict(name="Oats Porridge", category="recipe", meal_type="Breakfast",
       food_type="veg", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=10,
       calories=260, protein=9, carbohydrate=42, fat=6,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="continental",
       serving_note="1 bowl (~250g)",
       ingredients="Rolled oats 60g|Milk 200ml|Honey 1 tsp|Banana ½ (sliced)|Chia seeds 1 tsp|Cinnamon ¼ tsp",
       steps="Bring milk to simmer; add oats; cook stirring 4-5 min|Add cinnamon; adjust consistency with more milk if needed|Serve topped with banana, chia seeds and honey"),

  dict(name="Moong Dal Chilla", category="recipe", meal_type="Breakfast",
       food_type="vegan", food_group="grain_breakfast", difficulty="Medium", cook_time_mins=20,
       calories=255, protein=14, carbohydrate=36, fat=6,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="north_indian",
       serving_note="2 chillas (~180g)",
       ingredients="Yellow moong dal 80g (soaked 2 hr)|Ginger ½ tsp|Green chilli 1|Onion 30g|Coriander 2 tbsp|Oil 8ml|Salt to taste",
       steps="Drain soaked moong dal; blend with ginger, chilli and little water to smooth batter|Add onion, coriander, salt; mix|Cook like dosa on non-stick pan with oil 2 min per side"),

  dict(name="Aloo Paratha", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="roti", difficulty="Medium", cook_time_mins=25,
       calories=380, protein=8, carbohydrate=58, fat=12,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="complete_meal", cuisine="north_indian",
       serving_note="1 paratha (~200g)",
       ingredients="Whole wheat flour 100g|Potato 150g (boiled, mashed)|Onion 30g (finely chopped)|Green chilli 1|Coriander 2 tbsp|Garam masala ¼ tsp|Amchur ¼ tsp|Ghee 10ml|Salt to taste",
       steps="Make soft dough from flour; rest 10 min|Mix potato with onion, chilli, coriander, spices and salt|Roll dough circle; place filling; seal; roll to paratha|Cook on hot tawa with ghee 2-3 min per side till golden"),

  dict(name="Banana Oat Pancakes", category="recipe", meal_type="Breakfast",
       food_type="veg", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=15,
       calories=285, protein=10, carbohydrate=46, fat=7,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="continental",
       serving_note="3 small pancakes (~180g)",
       ingredients="Banana 1 ripe (mashed)|Oats 50g|Egg 1|Milk 30ml|Baking powder ¼ tsp|Cinnamon ¼ tsp|Oil 5ml",
       steps="Blend all ingredients to smooth batter|Heat non-stick pan with little oil on medium|Pour small rounds; cook 2 min until bubbles appear; flip; cook 1 min"),

  dict(name="Daliya", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="grain_breakfast", difficulty="Easy", cook_time_mins=25,
       calories=355, protein=15, carbohydrate=58, fat=5,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="north_indian",
       serving_note="1 bowl (~300g) — broken wheat porridge",
       ingredients="Broken wheat (daliya) 80g|Mixed vegetables 100g (carrot, peas, beans)|Onion 40g|Cumin seeds 1 tsp|Ghee 8ml|Turmeric ¼ tsp|Salt to taste|Coriander 2 tbsp",
       steps="Heat ghee; add cumin; add onion; cook 2 min|Add vegetables; cook 2 min|Add daliya; stir 1 min|Add 2.5× water; salt; pressure cook 2 whistles|Fluff; garnish coriander"),

  # ── SNACKS ──────────────────────────────────────────────────────────────────
  dict(name="Roasted Makhana", category="recipe", meal_type="Snack",
       food_type="vegan", food_group="chaat", difficulty="Easy", cook_time_mins=8,
       calories=165, protein=5, carbohydrate=28, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="north_indian",
       serving_note="1 bowl (~30g dry)",
       ingredients="Fox nuts (makhana) 30g|Ghee 5ml|Salt ¼ tsp|Black pepper ¼ tsp|Chaat masala ¼ tsp",
       steps="Heat ghee in pan on low|Add makhana; stir continuously 6-8 min until crispy|Season with salt, pepper, chaat masala immediately"),

  dict(name="Spiced Roasted Chana", category="recipe", meal_type="Snack",
       food_type="vegan", food_group="chaat", difficulty="Easy", cook_time_mins=10,
       calories=185, protein=10, carbohydrate=28, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="north_indian",
       serving_note="1 bowl (~40g)",
       ingredients="Roasted chana dal 40g|Chaat masala ½ tsp|Red chilli ¼ tsp|Lemon juice 1 tsp",
       steps="Mix all ingredients; toss|Serve as snack — no cooking needed"),

  dict(name="Sprouts Chaat", category="recipe", meal_type="Snack; Lunch",
       food_type="vegan", food_group="chaat", difficulty="Easy", cook_time_mins=5,
       calories=175, protein=9, carbohydrate=26, fat=3,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="north_indian",
       serving_note="1 bowl (~150g)",
       ingredients="Mixed sprouts 100g (moong, matki, channa)|Onion 30g (chopped)|Tomato 30g (chopped)|Cucumber 20g|Green chilli 1|Lemon juice 2 tsp|Chaat masala ½ tsp|Coriander 2 tbsp|Salt to taste",
       steps="Lightly steam sprouts 3 min or eat raw|Mix with vegetables and seasoning|Serve fresh"),

  dict(name="Paneer Tikka", category="recipe", meal_type="Snack; Dinner",
       food_type="veg", food_group="paneer", difficulty="Medium", cook_time_mins=30,
       calories=265, protein=16, carbohydrate=8, fat=18,
       portion_min=0.5, portion_typical=0.75, portion_max=1.0,
       role="anchor_protein", cuisine="north_indian",
       serving_note="6 pieces (~150g marinated paneer)",
       ingredients="Paneer 120g (cubed)|Yogurt 40ml|Ginger-garlic paste 1 tsp|Tandoori masala 1 tsp|Kashmiri chilli ½ tsp|Oil 8ml|Lemon juice 1 tsp|Kasuri methi ½ tsp|Salt to taste",
       steps="Mix marinade; coat paneer; marinate 30 min|Thread on skewers with capsicum and onion|Grill at 220°C 15 min OR grill pan 4 min per side"),

  dict(name="Boiled Eggs with Seasoning", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="egg", food_group="egg", difficulty="Easy", cook_time_mins=10,
       calories=155, protein=13, carbohydrate=1, fat=11,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="north_indian",
       serving_note="2 hard-boiled eggs",
       ingredients="Eggs 2|Salt ¼ tsp|Black pepper ¼ tsp|Chaat masala ¼ tsp (optional)",
       steps="Place eggs in cold water; bring to boil; cook 10 min for hard-boiled|Transfer to ice water immediately; peel|Season with salt, pepper, chaat masala"),

  dict(name="Greek Yogurt Bowl", category="recipe",
       meal_type="Breakfast; Snack",
       food_type="veg", food_group="dairy", difficulty="Easy", cook_time_mins=3,
       calories=180, protein=14, carbohydrate=20, fat=5,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="gap_filler", cuisine="continental",
       serving_note="1 bowl (~200g)",
       ingredients="Greek yogurt 150g|Banana ½ (sliced)|Honey 1 tsp|Chia seeds 1 tsp|Granola 15g (optional)",
       steps="Pour yogurt into bowl|Top with banana, honey, chia seeds and granola"),

  dict(name="Peanut Butter Banana Toast", category="recipe",
       meal_type="Breakfast; Snack",
       food_type="vegan", food_group="toast", difficulty="Easy", cook_time_mins=5,
       calories=310, protein=10, carbohydrate=42, fat=12,
       portion_min=1.0, portion_typical=1.0, portion_max=2.0,
       role="complete_meal", cuisine="continental",
       serving_note="2 slices (~160g)",
       ingredients="Whole wheat bread 2 slices|Peanut butter 2 tbsp (32g)|Banana ½ (sliced)|Honey ½ tsp (optional)",
       steps="Toast bread|Spread peanut butter evenly|Top with banana slices; drizzle honey"),

  dict(name="Laiyya Channa", category="recipe", meal_type="Snack",
       food_type="vegan", food_group="chaat", difficulty="Easy", cook_time_mins=5,
       calories=165, protein=7, carbohydrate=28, fat=3,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="north_indian",
       serving_note="1 bowl (~50g)",
       ingredients="Puffed rice (murmura) 20g|Roasted chana 20g|Onion 20g|Tomato 15g|Coriander 1 tbsp|Green chilli 1|Lemon juice 1 tsp|Chaat masala ½ tsp|Salt to taste",
       steps="Mix all ingredients just before serving — puffed rice goes soggy fast"),

  # ── INDO-CHINESE ────────────────────────────────────────────────────────────
  dict(name="Egg Fried Rice", category="recipe", meal_type="Lunch; Dinner",
       food_type="egg", food_group="rice", difficulty="Medium", cook_time_mins=20,
       calories=430, protein=17, carbohydrate=60, fat=14,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="indo_chinese",
       serving_note="1 plate (~300g)",
       ingredients="Cooked rice (day-old) 180g|Eggs 2|Spring onion 3 stalks|Carrot 30g (finely diced)|Peas 30g|Garlic 3 cloves|Soy sauce 2 tbsp|Oil 10ml|White pepper ¼ tsp|Salt to taste",
       steps="Heat wok on very high heat — this is critical|Add oil; scramble eggs; push to side|Add garlic, carrot, peas; stir-fry 2 min|Add day-old rice; spread and press; toss on high heat 3 min|Add soy sauce and spring onion; toss; add white pepper"),

  # ── SALADS ───────────────────────────────────────────────────────────────────
  dict(name="Grilled Chicken Salad", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="chicken", difficulty="Easy", cook_time_mins=20,
       calories=280, protein=30, carbohydrate=14, fat=10,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="continental",
       serving_note="1 large plate (~320g)",
       ingredients="Chicken breast 120g|Mixed greens 80g|Cherry tomatoes 6|Cucumber 50g|Capsicum 30g|Olive oil 8ml|Lemon juice 1 tbsp|Salt and pepper",
       steps="Season chicken; grill 5 min per side; slice|Arrange greens and vegetables|Top with sliced chicken; dress with olive oil and lemon"),

  # ── PASTA ────────────────────────────────────────────────────────────────────
  dict(name="Pasta Primavera", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="pasta", difficulty="Medium", cook_time_mins=25,
       calories=395, protein=11, carbohydrate=68, fat=9,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="continental",
       serving_note="1 plate (~300g)",
       ingredients="Penne pasta 80g (dry)|Mixed veg 150g (zucchini, capsicum, broccoli, cherry tomato)|Garlic 3 cloves|Olive oil 12ml|Parmesan 15g|Basil fresh 6 leaves|Salt and pepper",
       steps="Cook pasta al dente; reserve 60ml pasta water|Sauté garlic in olive oil 30 sec; add vegetables; cook 4 min|Add pasta and pasta water; toss; finish with parmesan and basil"),

  dict(name="Red Sauce Pasta (Veg)", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="pasta", difficulty="Medium", cook_time_mins=30,
       calories=380, protein=11, carbohydrate=66, fat=8,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="continental",
       serving_note="1 plate (~300g)",
       ingredients="Penne pasta 80g (dry)|Tomato 150g (crushed/pureed)|Onion 50g|Garlic 3 cloves|Capsicum 40g|Olive oil 10ml|Oregano 1 tsp|Red chilli flakes ¼ tsp|Salt and pepper|Parmesan 10g",
       steps="Cook pasta al dente|Sauté onion, garlic in olive oil 3 min|Add tomato puree; cook 8 min; add oregano and chilli|Add capsicum; cook 2 min; toss with pasta"),

  dict(name="Red Sauce Pasta (Chicken)", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="chicken", difficulty="Medium", cook_time_mins=35,
       calories=450, protein=32, carbohydrate=60, fat=10,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="complete_meal", cuisine="continental",
       serving_note="1 plate (~320g)",
       ingredients="Penne pasta 80g (dry)|Chicken breast 80g (diced)|Tomato 150g (pureed)|Onion 50g|Garlic 3 cloves|Olive oil 10ml|Oregano 1 tsp|Red chilli flakes ¼ tsp|Salt and pepper|Parmesan 10g",
       steps="Cook pasta al dente|Brown chicken in olive oil 4 min; remove|Sauté onion, garlic; add tomato puree; cook 8 min|Return chicken; add pasta; toss"),

  # ── GRILLED DISHES ───────────────────────────────────────────────────────────
  dict(name="Grilled Chicken with Vegetables", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="chicken", difficulty="Easy", cook_time_mins=25,
       calories=280, protein=32, carbohydrate=14, fat=11,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="continental",
       serving_note="1 serving (~250g chicken + vegetables)",
       ingredients="Chicken breast 150g|Zucchini 60g|Capsicum 60g|Onion 40g|Olive oil 10ml|Mixed herbs 1 tsp|Garlic 2 cloves|Lemon juice 1 tbsp|Salt and pepper",
       steps="Marinate chicken in herbs, garlic, lemon, oil 30 min|Grill chicken 5 min per side; rest 3 min|Grill vegetables 4 min each side"),

  # ── RICE ─────────────────────────────────────────────────────────────────────
  dict(name="Vegetable Pulao", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="rice", difficulty="Easy", cook_time_mins=25,
       calories=355, protein=7, carbohydrate=66, fat=7,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_starch", cuisine="north_indian",
       serving_note="1 plate (~280g)",
       ingredients="Basmati rice 80g|Mixed veg 100g (peas, carrot, beans)|Onion 40g|Bay leaf 1|Cumin seeds 1 tsp|Ghee 8ml|Water 160ml|Salt to taste|Mint 10 leaves",
       steps="Soak rice 20 min; drain|Heat ghee; add cumin, bay leaf; add onion; cook 3 min|Add vegetables; cook 2 min; add rice; stir 1 min|Add water, salt, mint; cover; cook 12 min on low; fluff"),

  dict(name="Steamed Chicken", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="chicken", difficulty="Easy", cook_time_mins=20,
       calories=220, protein=32, carbohydrate=3, fat=9,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="east_asian",
       serving_note="1 serving (~180g)",
       ingredients="Chicken breast 180g|Ginger 4 slices|Spring onion 2 stalks|Soy sauce 1 tbsp|Sesame oil 3ml|Salt to taste",
       steps="Score chicken; season with salt|Place on plate with ginger and spring onion|Steam over boiling water 15-18 min|Drizzle soy sauce and sesame oil"),

  # ── KEBABS ───────────────────────────────────────────────────────────────────
  dict(name="Masoor Dal Kababs", category="recipe", meal_type="Snack; Lunch",
       food_type="vegan", food_group="kabab", difficulty="Medium", cook_time_mins=30,
       calories=185, protein=9, carbohydrate=26, fat=5,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="north_indian",
       serving_note="4 kebabs (~150g)",
       ingredients="Red masoor dal 60g (boiled till dry)|Potato 60g (boiled, mashed)|Onion 30g|Green chilli 1|Coriander 2 tbsp|Garam masala ¼ tsp|Besan 15g|Oil 8ml|Salt to taste",
       steps="Mix mashed dal with all ingredients|Shape into flat patties|Shallow fry 3 min per side until crispy"),

  # ── FISH ────────────────────────────────────────────────────────────────────
  dict(name="Rohu Fish Curry", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="fish", difficulty="Medium", cook_time_mins=30,
       calories=260, protein=24, carbohydrate=8, fat=14,
       portion_min=0.75, portion_typical=1.0, portion_max=2.0,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~230g)",
       ingredients="Rohu fish 200g (steaks)|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tbsp|Mustard oil 12ml|Turmeric ¼ tsp|Red chilli ½ tsp|Coriander powder 1 tsp|Panch phoron ½ tsp|Salt to taste",
       steps="Marinate fish with turmeric and salt 15 min|Heat mustard oil; fry fish 3 min per side; remove|In same oil add panch phoron; add onion; cook golden|Add ginger-garlic, tomato and spices; cook 5 min|Add fish and 150ml water; simmer 8 min"),

  dict(name="Grilled Rohu Fish", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="fish", difficulty="Easy", cook_time_mins=20,
       calories=210, protein=24, carbohydrate=4, fat=10,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="anchor_protein", cuisine="continental",
       serving_note="1 fillet (~180g)",
       ingredients="Rohu fish 180g (boneless fillet)|Lemon juice 1 tbsp|Garlic 2 cloves|Mixed herbs 1 tsp|Olive oil 8ml|Salt and pepper",
       steps="Marinate fish 20 min|Grill on medium-high 4-5 min per side|Fish is done when it flakes easily"),

  # ── SANDWICHES ───────────────────────────────────────────────────────────────
  dict(name="Vegetable Salad Sandwich", category="recipe",
       meal_type="Breakfast; Lunch; Snack",
       food_type="vegan", food_group="toast", difficulty="Easy", cook_time_mins=8,
       calories=240, protein=7, carbohydrate=36, fat=7,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="continental",
       serving_note="1 sandwich (2 slices, ~180g)",
       ingredients="Whole wheat bread 2 slices|Cucumber 30g (sliced)|Tomato 30g (sliced)|Lettuce 1 leaf|Onion 15g (sliced)|Mayo or hung curd 1 tbsp|Mustard ½ tsp|Salt and pepper",
       steps="Spread mayo and mustard on bread|Layer vegetables; season|Press together; cut diagonally"),

  dict(name="Grilled Paneer", category="recipe", meal_type="Snack; Lunch; Dinner",
       food_type="veg", food_group="paneer", difficulty="Easy", cook_time_mins=12,
       calories=295, protein=18, carbohydrate=4, fat=22,
       portion_min=0.5, portion_typical=0.75, portion_max=1.0,
       role="anchor_protein", cuisine="north_indian",
       serving_note="4-5 slices (~120g)",
       ingredients="Paneer 120g (sliced 1cm thick)|Chilli powder ¼ tsp|Turmeric a pinch|Cumin ¼ tsp|Oil 6ml|Lemon juice 1 tsp|Salt to taste",
       steps="Mix spices with oil and lemon; coat paneer|Heat grill pan on high|Grill 2 min per side until char marks appear"),

  dict(name="Avocado Toast", category="recipe", meal_type="Breakfast; Snack",
       food_type="vegan", food_group="toast", difficulty="Easy", cook_time_mins=5,
       calories=205, protein=4, carbohydrate=20, fat=12,
       portion_min=1.0, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="continental",
       serving_note="2 slices (~150g)",
       ingredients="Whole wheat bread 2 slices|Avocado ½ (ripe)|Lemon juice 1 tsp|Chilli flakes ¼ tsp|Salt and pepper|Sesame seeds ½ tsp",
       steps="Toast bread|Mash avocado with lemon, salt, pepper|Spread on toast; sprinkle chilli flakes and sesame seeds"),

  # ── DRINKS ───────────────────────────────────────────────────────────────────
  dict(name="Milk Tea", category="recipe", meal_type="Breakfast; Snack",
       food_type="veg", food_group="drink", difficulty="Easy", cook_time_mins=8,
       calories=70, protein=3, carbohydrate=8, fat=2,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="beverage", cuisine="north_indian",
       serving_note="1 cup (150ml)",
       ingredients="Water 100ml|Milk 80ml|Black tea leaves 1 tsp|Sugar 1 tsp|Ginger ¼ tsp",
       steps="Boil water with ginger; add tea leaves; boil 1 min|Add milk; bring back to boil; strain|Add sugar"),

  dict(name="Milk Coffee", category="recipe", meal_type="Breakfast; Snack",
       food_type="veg", food_group="drink", difficulty="Easy", cook_time_mins=5,
       calories=80, protein=4, carbohydrate=8, fat=3,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="beverage", cuisine="continental",
       serving_note="1 cup (200ml)",
       ingredients="Milk 180ml|Instant coffee 1 tsp|Sugar 1 tsp (optional)",
       steps="Heat milk; froth if desired; add coffee; stir well"),

  dict(name="Buttermilk (Chaach)", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="veg", food_group="drink", difficulty="Easy", cook_time_mins=3,
       calories=40, protein=2, carbohydrate=4, fat=1,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="beverage", cuisine="north_indian",
       serving_note="1 glass (250ml)",
       ingredients="Yogurt 80ml|Water 200ml|Cumin powder ¼ tsp|Black salt ¼ tsp|Coriander 1 tsp|Ginger ¼ tsp",
       steps="Blend yogurt with water until frothy|Add all spices; mix well; serve chilled"),

  # ── SOUPS ────────────────────────────────────────────────────────────────────
  dict(name="Tomato Soup (Indian Style)", category="recipe",
       meal_type="Snack; Dinner",
       food_type="vegan", food_group="soup", difficulty="Easy", cook_time_mins=20,
       calories=95, protein=2, carbohydrate=14, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="north_indian",
       serving_note="1 bowl (250ml)",
       ingredients="Tomatoes 250g|Onion 40g|Garlic 2 cloves|Ginger ½ tsp|Butter 8g|Cumin seeds ½ tsp|Black pepper ¼ tsp|Salt to taste|Coriander 1 tbsp|Cream 10ml (optional)",
       steps="Sauté onion, garlic, ginger in butter 3 min|Add tomatoes; cook 8 min|Blend smooth; strain|Return to pot; season with cumin, pepper, salt; simmer 3 min|Finish with cream and coriander"),

  dict(name="Vegetable Clear Soup", category="recipe", meal_type="Snack; Dinner",
       food_type="vegan", food_group="soup", difficulty="Easy", cook_time_mins=15,
       calories=55, protein=2, carbohydrate=9, fat=1,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="continental",
       serving_note="1 bowl (300ml)",
       ingredients="Mixed veg 100g (carrot, beans, cabbage, corn)|Vegetable stock 400ml|Ginger 1 tsp|Garlic 1 clove|Soy sauce 1 tsp|Black pepper ¼ tsp|Salt to taste|Spring onion 1 tbsp",
       steps="Bring stock to boil with ginger and garlic|Add vegetables; simmer 6 min|Add soy sauce, pepper; garnish spring onion"),

  # ── SOUTH INDIAN ─────────────────────────────────────────────────────────────
  dict(name="Idli", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="south_indian", difficulty="Hard", cook_time_mins=20,
       calories=155, protein=5, carbohydrate=30, fat=1,
       portion_min=1.0, portion_typical=2.0, portion_max=3.0,
       role="anchor_starch", cuisine="south_indian",
       serving_note="3 idlis (~165g)",
       ingredients="Idli batter 200ml (fermented urad dal and rice batter)|Water as needed|Salt to taste",
       steps="Mix batter with salt; pour into greased moulds; steam 12-15 min|Idli is cooked when toothpick comes out clean|Serve with sambhar and chutney"),

  dict(name="Sambhar", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="south_indian", difficulty="Medium", cook_time_mins=30,
       calories=120, protein=6, carbohydrate=18, fat=3,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_protein", cuisine="south_indian",
       serving_note="1 bowl (200ml)",
       ingredients="Toor dal 40g (boiled)|Mixed veg 80g (drumstick, brinjal, tomato, shallot)|Tamarind 10g|Sambhar powder 1.5 tsp|Mustard seeds 1 tsp|Curry leaves 8|Red chilli 1|Oil 8ml|Salt to taste|Coriander 2 tbsp",
       steps="Pressure cook toor dal 3 whistles; mash|Soak tamarind in warm water; strain|Heat oil; add mustard, curry leaves, red chilli; add vegetables; cook 5 min|Add tamarind water and sambhar powder; cook 5 min|Add dal; simmer 8 min; adjust consistency"),

  dict(name="Rasam", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="south_indian", difficulty="Easy", cook_time_mins=15,
       calories=55, protein=2, carbohydrate=8, fat=2,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="south_indian",
       serving_note="1 bowl (250ml)",
       ingredients="Tomato 60g (crushed)|Tamarind 8g|Rasam powder 1 tsp|Garlic 2 cloves (crushed)|Mustard seeds 1 tsp|Curry leaves 6|Coriander 2 tbsp|Oil 5ml|Salt and pepper to taste",
       steps="Soak tamarind; strain; combine with tomato and rasam powder|Boil 5 min|Heat oil; add mustard, curry leaves, garlic; add to rasam|Simmer 2 min; garnish coriander"),

  dict(name="Plain Dosa", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="south_indian", difficulty="Hard", cook_time_mins=20,
       calories=180, protein=5, carbohydrate=34, fat=3,
       portion_min=1.0, portion_typical=1.5, portion_max=2.0,
       role="anchor_starch", cuisine="south_indian",
       serving_note="1 dosa (~120g)",
       ingredients="Dosa batter 150ml (fermented rice and urad dal)|Oil 5ml|Salt to taste",
       steps="Heat tawa; pour batter in center; spread in circular motion|Drizzle oil around edges; cook 2 min until golden|Serve with sambhar and coconut chutney"),

  dict(name="Masala Dosa", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="south_indian", difficulty="Hard", cook_time_mins=30,
       calories=310, protein=7, carbohydrate=52, fat=8,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="south_indian",
       serving_note="1 dosa with potato filling (~220g)",
       ingredients="Dosa batter 150ml|Potato filling: potato 150g (boiled, mashed), onion 40g, mustard seeds 1 tsp, turmeric ¼ tsp, curry leaves 6, oil 8ml, salt|Oil 5ml",
       steps="Make potato masala: heat oil; add mustard; add onion; cook 3 min; add potato, turmeric, salt; mash gently|Make crispy dosa; place potato masala in center; fold over"),

  dict(name="Multigrain Idli", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="south_indian", difficulty="Hard", cook_time_mins=20,
       calories=140, protein=5, carbohydrate=26, fat=2,
       portion_min=1.0, portion_typical=2.0, portion_max=3.0,
       role="anchor_starch", cuisine="south_indian",
       serving_note="3 idlis (~155g)",
       ingredients="Multigrain idli batter 200ml (ragi, oats, urad dal blend)|Salt to taste",
       steps="Pour batter into greased idli moulds; steam 15 min"),

  dict(name="Multigrain Dosa", category="recipe", meal_type="Breakfast; Lunch",
       food_type="vegan", food_group="south_indian", difficulty="Hard", cook_time_mins=20,
       calories=160, protein=5, carbohydrate=28, fat=3,
       portion_min=1.0, portion_typical=1.5, portion_max=2.0,
       role="anchor_starch", cuisine="south_indian",
       serving_note="1 dosa (~120g)",
       ingredients="Multigrain dosa batter 150ml|Oil 5ml|Salt to taste",
       steps="Cook thin crispy dosa on hot tawa; drizzle oil"),

  dict(name="Tomato Rice", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="rice", difficulty="Easy", cook_time_mins=20,
       calories=330, protein=6, carbohydrate=60, fat=7,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_starch", cuisine="south_indian",
       serving_note="1 plate (~270g)",
       ingredients="Cooked rice 180g|Tomato 80g (finely chopped)|Onion 40g|Mustard seeds 1 tsp|Curry leaves 6|Sambar powder ½ tsp|Turmeric ¼ tsp|Oil 8ml|Salt to taste|Coriander 2 tbsp",
       steps="Heat oil; add mustard, curry leaves; add onion; cook 2 min|Add tomato and spices; cook 4 min until pulpy|Add rice; mix gently; cook 2 min"),

  dict(name="Tehri", category="recipe", meal_type="Breakfast; Lunch; Dinner",
       food_type="vegan", food_group="rice", difficulty="Easy", cook_time_mins=25,
       calories=355, protein=9, carbohydrate=66, fat=7,
       portion_min=0.75, portion_typical=1.0, portion_max=1.5,
       role="complete_meal", cuisine="north_indian",
       serving_note="1 bowl (~300g) — spiced one-pot rice",
       ingredients="Basmati rice 80g|Mixed veg 100g (potato, peas, carrot)|Onion 40g|Ginger-garlic paste 1 tsp|Whole spices (bay, cloves, cardamom, cumin)|Ghee 8ml|Turmeric ¼ tsp|Garam masala ¼ tsp|Water 180ml|Salt to taste",
       steps="Heat ghee; add whole spices; add onion; cook 3 min|Add ginger-garlic; cook 1 min; add vegetables and spices; cook 3 min|Add rice; stir; add water; cover; cook 12 min on low"),


  # ── FLATBREADS ───────────────────────────────────────────────────────────────
  dict(name="Plain Paratha", category="recipe",
       meal_type="Breakfast; Lunch; Dinner",
       food_type="vegan", food_group="roti", difficulty="Easy", cook_time_mins=15,
       calories=245, protein=6, carbohydrate=38, fat=8,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="anchor_starch", cuisine="north_indian",
       serving_note="1 paratha (~120g)",
       ingredients="Whole wheat flour 80g|Water ~40ml|Oil 8ml|Salt a pinch",
       steps="Knead flour to soft dough; rest 10 min|Roll to circle; fold twice; roll out again to layered paratha|Cook on hot tawa with oil 2 min each side"),

  dict(name="Masala Paratha", category="recipe",
       meal_type="Breakfast; Lunch; Dinner",
       food_type="vegan", food_group="roti", difficulty="Easy", cook_time_mins=15,
       calories=265, protein=7, carbohydrate=40, fat=9,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="anchor_starch", cuisine="north_indian",
       serving_note="1 paratha (~130g)",
       ingredients="Whole wheat flour 80g|Onion 20g (finely chopped)|Green chilli 1|Coriander 1 tbsp|Ajwain ¼ tsp|Oil 8ml|Salt to taste",
       steps="Mix flour with onion, chilli, coriander, ajwain and salt; add water; knead|Roll and cook with oil on hot tawa"),

  dict(name="Multigrain Paratha / Roti", category="recipe",
       meal_type="Breakfast; Lunch; Dinner",
       food_type="vegan", food_group="roti", difficulty="Easy", cook_time_mins=15,
       calories=230, protein=7, carbohydrate=38, fat=6,
       portion_min=1.0, portion_typical=2.0, portion_max=4.0,
       role="anchor_starch", cuisine="north_indian",
       serving_note="2 rotis (~120g)",
       ingredients="Multigrain flour 80g (wheat, ragi, jowar, bajra mix)|Water ~50ml|Salt a pinch|Ghee 5ml",
       steps="Knead flour with water; rest 10 min|Roll thin rounds; cook on hot tawa 90 sec per side|Apply ghee while hot"),

  # ── NORTH INDIAN VEG DISHES ──────────────────────────────────────────────────
  dict(name="Aloo Bhuiya", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="veg_curry", difficulty="Easy", cook_time_mins=20,
       calories=210, protein=3, carbohydrate=30, fat=8,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_veg", cuisine="north_indian",
       serving_note="1 bowl (~200g) — dry potato sabzi",
       ingredients="Potato 200g (diced small)|Mustard seeds 1 tsp|Curry leaves 6|Turmeric ¼ tsp|Red chilli ¼ tsp|Amchur ¼ tsp|Oil 10ml|Salt to taste|Coriander 2 tbsp",
       steps="Heat oil; add mustard seeds; add curry leaves; add potato|Add all spices; cook covered 12 min stirring occasionally|Uncover; cook 5 min until edges crispy"),

  dict(name="Bhindi Bhujiya", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="veg_curry", difficulty="Easy", cook_time_mins=20,
       calories=165, protein=3, carbohydrate=16, fat=9,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="anchor_veg", cuisine="north_indian",
       serving_note="1 bowl (~200g)",
       ingredients="Okra (bhindi) 200g (sliced, dried completely)|Onion 60g (sliced)|Oil 12ml|Cumin seeds 1 tsp|Coriander powder 1 tsp|Amchur ¼ tsp|Red chilli ¼ tsp|Salt to taste",
       steps="Dry okra completely before cooking — moisture causes stickiness|Heat oil; add cumin; add onion; cook 3 min|Add okra; cook on medium-high WITHOUT covering 12-15 min|Add spices; toss; cook 3 more min"),

  # ── DALS ─────────────────────────────────────────────────────────────────────
  dict(name="Dal Tadka", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="dal", difficulty="Easy", cook_time_mins=25,
       calories=268, protein=14, carbohydrate=36, fat=8,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~220g)",
       ingredients="Yellow toor dal 80g|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tsp|Cumin seeds 1 tsp|Turmeric ¼ tsp|Red chilli ¼ tsp|Oil 10ml|Garam masala ¼ tsp|Salt to taste|Coriander 2 tbsp|Lemon juice ½ tsp",
       steps="Pressure cook dal with turmeric 3 whistles; mash slightly|Heat oil; add cumin; add onion; cook golden|Add ginger-garlic; cook 1 min; add tomato and spices; cook 4 min|Mix into dal; simmer 5 min; finish lemon and coriander"),

  dict(name="Rajma", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="dal", difficulty="Medium", cook_time_mins=50,
       calories=305, protein=16, carbohydrate=46, fat=7,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~250g)",
       ingredients="Red kidney beans 80g (soaked overnight)|Onion 80g|Tomato 80g|Ginger-garlic paste 1.5 tbsp|Coriander powder 1 tsp|Garam masala ½ tsp|Oil 10ml|Bay leaf 1|Whole spices|Salt to taste|Coriander 2 tbsp",
       steps="Pressure cook soaked rajma 6 whistles|Sauté onion deep golden; add ginger-garlic; cook 2 min|Add tomato and spices; cook 5 min|Add rajma with liquid; simmer 15-20 min until thick"),

  dict(name="Paneer Bhurji", category="recipe",
       meal_type="Breakfast; Lunch; Dinner",
       food_type="veg", food_group="paneer", difficulty="Easy", cook_time_mins=15,
       calories=310, protein=16, carbohydrate=8, fat=24,
       portion_min=0.5, portion_typical=0.75, portion_max=1.0,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~180g)",
       ingredients="Paneer 100g (crumbled)|Onion 50g (finely chopped)|Tomato 50g (finely chopped)|Green chilli 1|Ginger ½ tsp|Cumin seeds ½ tsp|Turmeric a pinch|Red chilli ¼ tsp|Oil 8ml|Salt to taste|Coriander 2 tbsp",
       steps="Heat oil; add cumin; add onion; cook 3 min|Add ginger, green chilli; cook 30 sec; add tomato; cook 3 min|Add turmeric, red chilli and paneer; mix gently|Cook 3 min; garnish coriander"),

  dict(name="Chole", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="dal", difficulty="Medium", cook_time_mins=50,
       calories=328, protein=14, carbohydrate=46, fat=10,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~250g) — kabuli chana / chickpea curry",
       ingredients="Kabuli chana (white chickpeas) 80g (soaked overnight)|Onion 80g|Tomato 80g|Ginger-garlic paste 1.5 tbsp|Chole masala 2 tsp|Oil 12ml|Bay leaf 1|Amchur ½ tsp|Salt to taste|Coriander 2 tbsp",
       steps="Pressure cook soaked chana 5-6 whistles|Sauté onion deep golden; add ginger-garlic; cook 2 min|Add tomato and chole masala; cook 6 min until oil separates|Add chana with liquid; mash some for thick gravy; simmer 15 min"),

  dict(name="Aloo Gobi", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="veg_curry", difficulty="Easy", cook_time_mins=25,
       calories=230, protein=5, carbohydrate=32, fat=9,
       portion_min=0.5, portion_typical=1.0, portion_max=1.25,
       role="anchor_veg", cuisine="north_indian",
       serving_note="1 bowl (~280g)",
       ingredients="Potato 150g (cubed)|Cauliflower 150g (florets)|Onion 60g|Tomato 50g|Ginger-garlic paste 1 tsp|Cumin seeds 1 tsp|Coriander powder 1 tsp|Turmeric ¼ tsp|Oil 12ml|Garam masala ¼ tsp|Salt to taste|Coriander 2 tbsp",
       steps="Heat oil; add cumin; add onion; cook 3 min; add ginger-garlic; cook 1 min|Add tomato and spices; cook 3 min|Add potato; cook covered 8 min; add cauliflower; cook covered 10 min|Uncover; cook 3 min"),

  dict(name="Dal Makhani", category="recipe", meal_type="Lunch; Dinner",
       food_type="veg", food_group="dal", difficulty="Hard", cook_time_mins=60,
       calories=345, protein=14, carbohydrate=40, fat=15,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~250g)",
       ingredients="Black urad dal 60g (soaked overnight)|Kidney beans 20g (soaked overnight)|Butter 15g|Cream 30ml|Onion 60g (pureed)|Tomato 80g (pureed)|Ginger-garlic paste 1.5 tbsp|Garam masala ½ tsp|Kasoori methi 1 tsp|Salt to taste",
       steps="Pressure cook dal and rajma 8-10 whistles; mash slightly|Heat butter; fry onion puree until golden; add ginger-garlic; cook 2 min|Add tomato puree; cook 8 min; add garam masala|Add dal; simmer 30 min on very low; stir in cream; finish kasoori methi"),

  dict(name="Palak Paneer", category="recipe", meal_type="Lunch; Dinner",
       food_type="veg", food_group="paneer", difficulty="Medium", cook_time_mins=30,
       calories=295, protein=14, carbohydrate=12, fat=22,
       portion_min=0.5, portion_typical=0.75, portion_max=1.0,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~250g)",
       ingredients="Paneer 100g (cubed)|Spinach 200g (blanched, blended)|Onion 60g|Tomato 40g|Ginger-garlic paste 1 tbsp|Cream 20ml|Ghee 12ml|Garam masala ¼ tsp|Kasuri methi 1 tsp|Salt to taste",
       steps="Blanch spinach 2 min; blend smooth|Heat ghee; fry paneer cubes golden; remove|In same ghee sauté onion golden; add ginger-garlic; cook 1 min; add tomato; cook 3 min|Add spinach puree; simmer 5 min; add cream and kasuri methi|Add paneer; cook 3 min"),

  dict(name="Masoor Dal", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="dal", difficulty="Easy", cook_time_mins=20,
       calories=250, protein=15, carbohydrate=36, fat=5,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~220g)",
       ingredients="Red masoor dal 80g|Onion 60g|Tomato 50g|Garlic 3 cloves|Cumin seeds 1 tsp|Turmeric ¼ tsp|Oil 8ml|Garam masala ¼ tsp|Salt to taste|Lemon juice ½ tsp|Coriander 2 tbsp",
       steps="Cook masoor dal with turmeric in 3× water 15 min (no soaking needed)|Heat oil; add cumin; add onion and garlic; cook golden|Add tomato and garam masala; cook 3 min|Mix into dal; simmer 5 min; finish lemon and coriander"),

  dict(name="Egg Curry", category="recipe", meal_type="Lunch; Dinner",
       food_type="egg", food_group="egg", difficulty="Medium", cook_time_mins=25,
       calories=278, protein=20, carbohydrate=12, fat=16,
       portion_min=0.75, portion_typical=1.0, portion_max=1.25,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl with 2 eggs (~250g)",
       ingredients="Eggs 2 (hard boiled, scored)|Onion 80g|Tomato 80g|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Garam masala ½ tsp|Oil 12ml|Turmeric ¼ tsp|Salt to taste|Coriander 2 tbsp",
       steps="Fry boiled eggs in oil 2 min until golden outside; remove|Sauté onion deep golden; add ginger-garlic; cook 1 min|Add tomato and all spices; cook 5 min|Add eggs to gravy; spoon sauce over; simmer 8 min"),

  dict(name="Chicken Curry", category="recipe", meal_type="Lunch; Dinner",
       food_type="non-veg", food_group="chicken", difficulty="Medium", cook_time_mins=40,
       calories=340, protein=27, carbohydrate=16, fat=17,
       portion_min=0.75, portion_typical=1.0, portion_max=2.5,
       role="anchor_protein", cuisine="north_indian",
       serving_note="1 bowl (~250g)",
       ingredients="Chicken 200g (bone-in)|Onion 80g|Tomato 80g|Ginger-garlic paste 1.5 tbsp|Yogurt 40ml|Coriander powder 1 tsp|Garam masala ½ tsp|Red chilli ½ tsp|Oil 12ml|Bay leaf 1|Salt to taste|Coriander 2 tbsp",
       steps="Marinate chicken in yogurt and spices 30 min|Heat oil; fry onion deep golden; add ginger-garlic; cook 2 min|Add tomato and spices; cook 5 min until oil separates|Add chicken; cook on high 5 min; reduce heat; cook covered 20 min"),

  dict(name="Steamed Rice", category="recipe", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="rice", difficulty="Easy", cook_time_mins=20,
       calories=212, protein=4, carbohydrate=46, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.5,
       role="anchor_starch", cuisine="north_indian",
       serving_note="1 plate (~180g cooked)",
       ingredients="Basmati or long-grain rice 80g (dry)|Water 160ml|Salt to taste",
       steps="Rinse rice 2-3 times; soak 20 min; drain|Add rice to boiling salted water; cook 10-12 min|Drain; steam dry 2 min; fluff with fork"),

  dict(name="Whole Wheat Roti (Chapati)", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="vegan", food_group="roti", difficulty="Easy", cook_time_mins=15,
       calories=150, protein=5, carbohydrate=30, fat=1,
       portion_min=1.0, portion_typical=2.0, portion_max=4.0,
       role="gap_filler", cuisine="north_indian",
       serving_note="2 rotis (~100g)",
       ingredients="Whole wheat flour (atta) 80g|Water ~45ml|Salt a pinch",
       steps="Knead flour with water to soft smooth dough; rest 10 min|Divide; roll thin circles 6-7 inch diameter|Cook on hot tawa 60 sec per side; puff directly on flame 10 sec"),

  # ── RAW INGREDIENTS / FRUITS / NUTS / SEEDS ──────────────────────────────────
  dict(name="Banana", category="ingredient", meal_type="Breakfast; Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=89, protein=1, carbohydrate=23, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="unknown",
       serving_note="1 medium banana (~90g)",
       ingredients="Banana 1 medium",
       steps="Eat as-is|Good gap-filler for carbohydrate deficit"),

  dict(name="Apple", category="ingredient", meal_type="Breakfast; Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=78, protein=0, carbohydrate=21, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="unknown",
       serving_note="1 medium apple (~150g)",
       ingredients="Apple 1 medium",
       steps="Eat as-is|Good gap-filler for carbohydrate deficit"),

  dict(name="Orange", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=62, protein=1, carbohydrate=15, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="1 medium orange (~150g)",
       ingredients="Orange 1 medium",
       steps="Peel and eat; or juice"),

  dict(name="Pomegranate", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=83, protein=2, carbohydrate=19, fat=1,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="½ fruit arils (~100g)",
       ingredients="Pomegranate ½",
       steps="Remove arils; eat as snack or add to salads|Rich in antioxidants"),

  dict(name="Watermelon", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=45, protein=1, carbohydrate=11, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="2 wedges (~200g)",
       ingredients="Watermelon 200g",
       steps="Slice and serve cold"),

  dict(name="Muskmelon", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=48, protein=1, carbohydrate=11, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="2 wedges (~180g)",
       ingredients="Muskmelon/cantaloupe 180g",
       steps="Slice and serve"),

  dict(name="Chia Seeds", category="ingredient", meal_type="Breakfast; Snack",
       food_type="vegan", food_group="seed", difficulty="Easy", cook_time_mins=0,
       calories=60, protein=3, carbohydrate=5, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="2 tbsp (~20g)",
       ingredients="Chia seeds 20g",
       steps="Soak in water/milk 20 min; use in yogurt, smoothie or porridge"),

  dict(name="Flaxseed", category="ingredient", meal_type="Breakfast; Snack",
       food_type="vegan", food_group="seed", difficulty="Easy", cook_time_mins=0,
       calories=55, protein=2, carbohydrate=3, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="1 tbsp (~15g) ground",
       ingredients="Flaxseed 15g (ground or whole)",
       steps="Add to smoothie, yogurt or baked goods|Ground flaxseed absorbs better than whole"),

  dict(name="Watermelon Seeds", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="seed", difficulty="Easy", cook_time_mins=0,
       calories=46, protein=3, carbohydrate=1, fat=4,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="2 tbsp (~15g) roasted",
       ingredients="Watermelon seeds 15g (roasted, shelled)",
       steps="Eat as snack; high in magnesium"),

  dict(name="Basil Seeds (Sabja)", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="seed", difficulty="Easy", cook_time_mins=0,
       calories=40, protein=2, carbohydrate=4, fat=2,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="1 tbsp (~15g) soaked",
       ingredients="Basil seeds (sabja) 15g",
       steps="Soak in water 15 min — they swell 10× in size|Add to falooda, lemonade or sharbat"),

  dict(name="Almonds", category="ingredient",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="vegan", food_group="nut", difficulty="Easy", cook_time_mins=0,
       calories=173, protein=6, carbohydrate=6, fat=15,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="unknown",
       serving_note="20 almonds (~20g)",
       ingredients="Almonds 20g",
       steps="Eat raw or soaked|Good fat and protein gap-filler"),

  dict(name="Peanuts", category="ingredient",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="vegan", food_group="nut", difficulty="Easy", cook_time_mins=0,
       calories=170, protein=8, carbohydrate=5, fat=15,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="unknown",
       serving_note="25g (~1 small handful)",
       ingredients="Roasted peanuts 25g",
       steps="Eat as snack|Good fat and protein gap-filler"),

  dict(name="Walnuts", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="nut", difficulty="Easy", cook_time_mins=0,
       calories=196, protein=5, carbohydrate=4, fat=20,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="4 halves (~20g)",
       ingredients="Walnuts 20g",
       steps="Eat as snack; rich in omega-3"),

  dict(name="Cashews", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="nut", difficulty="Easy", cook_time_mins=0,
       calories=180, protein=5, carbohydrate=10, fat=14,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="10 cashews (~20g)",
       ingredients="Cashews 20g",
       steps="Eat raw or roasted"),

  dict(name="Raisins", category="ingredient", meal_type="Snack",
       food_type="vegan", food_group="fruit", difficulty="Easy", cook_time_mins=0,
       calories=85, protein=1, carbohydrate=22, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="2 tbsp (~25g)",
       ingredients="Raisins 25g",
       steps="Eat as snack or add to salads and porridge"),

  # ── RAW VEGETABLES ───────────────────────────────────────────────────────────
  dict(name="Cucumber (Raw)", category="ingredient", meal_type="Snack; Lunch; Dinner",
       food_type="vegan", food_group="veg_raw", difficulty="Easy", cook_time_mins=0,
       calories=20, protein=1, carbohydrate=4, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="½ cucumber (~120g sliced)",
       ingredients="Cucumber ½",
       steps="Slice and serve with salt and lemon; good low-calorie snack"),

  dict(name="Tomato (Raw)", category="ingredient", meal_type="Snack; Lunch; Dinner",
       food_type="vegan", food_group="veg_raw", difficulty="Easy", cook_time_mins=0,
       calories=22, protein=1, carbohydrate=5, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="1 medium tomato (~120g)",
       ingredients="Tomato 1 medium",
       steps="Slice; serve raw with salt and pepper"),

  dict(name="Carrot (Raw)", category="ingredient", meal_type="Snack; Lunch",
       food_type="vegan", food_group="veg_raw", difficulty="Easy", cook_time_mins=0,
       calories=41, protein=1, carbohydrate=10, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="side", cuisine="unknown",
       serving_note="1 medium carrot (~100g)",
       ingredients="Carrot 1 medium",
       steps="Peel; eat as crudités with hummus or chutney"),

  dict(name="Onion (Raw)", category="ingredient", meal_type="Lunch; Dinner",
       food_type="vegan", food_group="veg_raw", difficulty="Easy", cook_time_mins=0,
       calories=40, protein=1, carbohydrate=9, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="1 small onion (~80g sliced)",
       ingredients="Onion 80g (sliced)",
       steps="Serve raw alongside curries and kebabs|Traditional Indian side"),

  dict(name="Beetroot (Raw)", category="ingredient", meal_type="Snack; Lunch",
       food_type="vegan", food_group="veg_raw", difficulty="Easy", cook_time_mins=0,
       calories=43, protein=2, carbohydrate=10, fat=0,
       portion_min=0.5, portion_typical=1.0, portion_max=1.5,
       role="side", cuisine="unknown",
       serving_note="½ beetroot (~80g grated)",
       ingredients="Beetroot ½ (grated or sliced)",
       steps="Eat raw grated with lemon and salt|Or slice thin for salads"),

  # ── GAP FILLERS (FAT) ────────────────────────────────────────────────────────
  dict(name="Ghee (1 tbsp)", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="veg", food_group="fat", difficulty="Easy", cook_time_mins=0,
       calories=135, protein=0, carbohydrate=0, fat=15,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="north_indian",
       serving_note="1 tablespoon (approx 15ml)",
       ingredients="Ghee 15ml",
       steps="Add to dal or sabzi while hot|Spread on roti or paratha|Log whenever used in cooking"),

  dict(name="Olive Oil (1 tbsp)", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="vegan", food_group="fat", difficulty="Easy", cook_time_mins=0,
       calories=126, protein=0, carbohydrate=0, fat=14,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="mediterranean",
       serving_note="1 tablespoon (15ml)",
       ingredients="Olive oil 15ml",
       steps="Drizzle over salad or grilled items|Use as finishing oil"),

  dict(name="Butter (10g)", category="recipe",
       meal_type="Breakfast; Lunch; Dinner; Snack",
       food_type="veg", food_group="fat", difficulty="Easy", cook_time_mins=0,
       calories=108, protein=0, carbohydrate=0, fat=12,
       portion_min=0.5, portion_typical=1.0, portion_max=2.0,
       role="gap_filler", cuisine="continental",
       serving_note="10g (approx 2 teaspoons)",
       ingredients="Butter 10g",
       steps="Spread on roti or toast|Melt into dal or rice|Log whenever used in cooking"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _seed_users(conn):
    print("Seeding users...")
    for u in USERS:
        existing = execute(conn,
            "SELECT id FROM users WHERE name=%s LIMIT 1", (u["name"],), fetch="one")
        if existing:
            print(f"  SKIP (exists): {u['name']}")
            continue
        execute(conn,
            "INSERT INTO users (name,password_hash,daily_cal,num_meals,food_pref) VALUES (%s,%s,%s,%s,%s)",
            (u["name"], _hash_pw(u["password"]), u["daily_cal"], u["num_meals"], u["food_pref"]))
        print(f"  ✓ {u['name']}")


def _seed_nutrition_targets(conn):
    print("Seeding nutrition targets (30P / 50C / 20F)...")
    users = execute(conn, "SELECT id, daily_cal FROM users", fetch="all")
    for u in users:
        existing = execute(conn,
            "SELECT user_id FROM nutrition_targets WHERE user_id=%s LIMIT 1",
            (u["id"],), fetch="one")
        if existing:
            # Update to correct macro split
            execute(conn,
                """UPDATE nutrition_targets
                   SET protein_g=ROUND((%s*0.30/4.0)::numeric,1),
                       carb_g   =ROUND((%s*0.50/4.0)::numeric,1),
                       fat_g    =ROUND((%s*0.20/9.0)::numeric,1),
                       cal_target=%s, updated_at=NOW()
                   WHERE user_id=%s""",
                (u["daily_cal"],)*4 + (u["id"],))
        else:
            execute(conn,
                """INSERT INTO nutrition_targets
                     (user_id,cal_target,protein_g,carb_g,fat_g,fiber_g)
                   VALUES (%s,%s,
                     ROUND((%s*0.30/4.0)::numeric,1),
                     ROUND((%s*0.50/4.0)::numeric,1),
                     ROUND((%s*0.20/9.0)::numeric,1),
                     30)""",
                (u["id"], u["daily_cal"],
                 u["daily_cal"], u["daily_cal"], u["daily_cal"]))
        print(f"  ✓ user_id={u['id']} cal={u['daily_cal']}")


def _seed_recipes(conn):
    print(f"\nSeeding {len(RECIPES)} recipes...")
    inserted = skipped = failed = 0
    for r in RECIPES:
        existing = execute(conn,
            "SELECT id FROM recipes WHERE name=%s LIMIT 1", (r["name"],), fetch="one")
        if existing:
            skipped += 1
            continue
        try:
            execute(conn,
                """INSERT INTO recipes
                     (name,category,meal_type,food_type,food_group,difficulty,
                      cook_time_mins,calories,protein,carbohydrate,fat,
                      portion_min,portion_typical,portion_max,role,cuisine,
                      serving_note,ingredients,steps)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (r["name"], r.get("category","recipe"), r["meal_type"],
                 r["food_type"], r["food_group"], r["difficulty"],
                 int(r["cook_time_mins"]),
                 float(r["calories"]), float(r["protein"]),
                 float(r["carbohydrate"]), float(r["fat"]),
                 float(r.get("portion_min",0.5)),
                 float(r.get("portion_typical",1.0)),
                 float(r.get("portion_max",1.5)),
                 r["role"], r["cuisine"],
                 r.get("serving_note"), r.get("ingredients"), r.get("steps")))
            inserted += 1
            print(f"  ✓ {r['name']}")
        except Exception as e:
            print(f"  ✗ {r['name']} — ERROR: {e}")
            failed += 1

    return inserted, skipped, failed


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Diet Tracker — DB Seed Script (v2 consolidated schema)")
    print("=" * 55)

    conn = get_connection()

    _seed_users(conn)
    print()
    _seed_nutrition_targets(conn)
    ins, skp, fail = _seed_recipes(conn)

    conn.close()

    print()
    print("=" * 55)
    print("Verification:")
    conn2 = get_connection()
    for tbl in ["users","recipes","nutrition_targets"]:
        row = execute(conn2, f"SELECT COUNT(*) AS n FROM {tbl}", fetch="one")
        print(f"  {tbl}: {row['n']} rows")
    conn2.close()

    print()
    if fail == 0:
        print(f"✓ Seed complete — Inserted: {ins}  Skipped: {skp}")
    else:
        print(f"⚠ Seed done with errors — Inserted: {ins}  Skipped: {skp}  Failed: {fail}")
