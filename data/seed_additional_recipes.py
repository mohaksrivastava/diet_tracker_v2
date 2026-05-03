#!/usr/bin/env python3
"""
data/seed_additional_recipes.py
================================
Adds ~223 new recipes to the Supabase DB.
Run from the project root (diet_tracker_py/) with venv active:

    python data/seed_additional_recipes.py

Prerequisites:
    1. setup/add_cuisines_v3.sql already run in Supabase SQL Editor
    2. .env file present with SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASS
    3. setup_db_complete.sql already run and seed_recipes.py already run
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection, execute

# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_recipe(conn, r: dict) -> bool:
    """
    Insert one recipe into the consolidated recipes table.
    serving_note, ingredients, steps come from r["detail"].
    Returns True if inserted, False if already exists (skipped).
    """
    existing = execute(conn,
        "SELECT id FROM recipes WHERE name=%s LIMIT 1",
        (r["name"],), fetch="one")
    if existing:
        print(f"  SKIP (exists): {r['name']}")
        return False

    det = r.get("detail", {})
    execute(conn,
        """INSERT INTO recipes
             (name, category, meal_type, food_type, food_group, difficulty,
              cook_time_mins, calories, protein, carbohydrate, fat,
              portion_min, portion_typical, portion_max, role, cuisine,
              serving_note, ingredients, steps)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (r["name"],
         r.get("category", "recipe"),
         r["meal_type"],
         r["food_type"],
         r["food_group"],
         r["difficulty"],
         int(r["cook_time"]),
         float(r["cal"]),
         float(r["prot"]),
         float(r["carb"]),
         float(r["fat"]),
         float(r.get("p_min", 0.5)),
         float(r.get("p_typ", 1.0)),
         float(r.get("p_max", 1.5)),
         r["role"],
         r["cuisine"],
         det.get("serving"),
         det.get("ingredients"),
         det.get("steps")))
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# RECIPE DATA
# Each entry: name, meal_type, food_type, food_group, difficulty, cook_time,
#             cal, prot, carb, fat, p_min, p_typ, p_max, role, cuisine,
#             detail: {serving, ingredients, steps}
# ═══════════════════════════════════════════════════════════════════════════════

RECIPES = []

# ── SOUTH INDIAN ──────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Set Dosa",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Hard",cook_time=45,cal=210,prot=6,carb=38,fat=4,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="3 small dosas (~180g)",
         ingredients="Dosa batter 200ml|Oil/ghee 8ml|Curry leaves 4|Mustard seeds ½ tsp",
         steps="Heat tawa; pour small rounds of batter (about 12cm)|Drizzle oil; cook 2 min on medium|Flip briefly 30 sec|Serve in sets of 3 with coconut chutney and sambhar")),

  dict(name="Rava Idli",meal_type="Breakfast; Lunch",food_type="veg",food_group="south_indian",
       difficulty="Medium",cook_time=30,cal=165,prot=5,carb=28,fat=4,
       p_min=1,p_typ=1.5,p_max=2,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="3 idlis (~165g)",
         ingredients="Semolina (rava) 80g|Yogurt 60ml|Water 40ml|Baking soda ¼ tsp|Mustard seeds 1 tsp|Curry leaves 6|Cashews 10g (broken)|Ginger ½ tsp|Green chilli 1|Oil 8ml|Salt to taste|Fresh coriander 2 tbsp",
         steps="Dry roast rava 4 min; cool|Mix with yogurt, water, salt; rest 10 min|Prepare tadka: heat oil; add mustard, cashews, curry leaves, ginger, chilli; cook 1 min|Fold tadka into batter; add baking soda; mix gently|Pour into greased moulds; steam 12-14 min")),

  dict(name="Neer Dosa",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Medium",cook_time=25,cal=130,prot=3,carb=27,fat=1,
       p_min=1,p_typ=2,p_max=3,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="2 dosas (~120g)",
         ingredients="Raw rice 80g (soaked 4 hr)|Water 200ml|Salt to taste|Oil 5ml",
         steps="Drain soaked rice; blend with water to very thin liquid batter|Season with salt|Heat non-stick pan; very lightly oil|Pour thin layer; do NOT spread with ladle — tilt pan to coat|Cover 1 min; fold and serve — do not flip")),

  dict(name="Wheat Dosa",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Easy",cook_time=20,cal=175,prot=5,carb=32,fat=3,
       p_min=1,p_typ=1.5,p_max=2,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="2 dosas (~160g)",
         ingredients="Whole wheat flour 80g|Rice flour 20g|Onion 40g (finely chopped)|Green chilli 1|Cumin seeds 1 tsp|Salt to taste|Water ~200ml|Oil 8ml",
         steps="Mix flours with onion, chilli, cumin, salt|Add water to make thin pourable batter|Rest 10 min|Cook on hot tawa like regular dosa — thin, crispy")),

  dict(name="Tomato Uttapam",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Hard",cook_time=40,cal=195,prot=6,carb=34,fat=4,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="1 large uttapam (~200g)",
         ingredients="Dosa/idli batter 200ml|Tomato 60g (finely chopped)|Onion 40g (finely chopped)|Green chilli 1|Fresh coriander 2 tbsp|Oil 8ml|Salt to taste",
         steps="Heat tawa on medium; pour thick round of batter (thicker than dosa)|Scatter tomato, onion, chilli, coriander on top; press lightly|Drizzle oil around edges; cook 3-4 min until underside golden|Flip; cook 2 min more")),

  dict(name="Onion Uttapam",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Hard",cook_time=40,cal=185,prot=6,carb=32,fat=3,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="1 large uttapam (~200g)",
         ingredients="Dosa/idli batter 200ml|Onion 80g (finely chopped)|Green chilli 1|Fresh coriander 2 tbsp|Oil 8ml|Salt to taste",
         steps="Heat tawa; pour thick batter round|Scatter onion, chilli, coriander|Drizzle oil; cook 3-4 min|Flip; cook 2 min")),

  dict(name="Ragi Dosa",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Medium",cook_time=30,cal=155,prot=5,carb=28,fat=3,
       p_min=1,p_typ=1.5,p_max=2,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="2 dosas (~160g)",
         ingredients="Ragi flour 60g|Rice flour 20g|Onion 40g (finely chopped)|Cumin seeds 1 tsp|Green chilli 1|Salt to taste|Water ~180ml|Oil 8ml",
         steps="Mix flours with onion, cumin, chilli, salt; add water to thin batter|Rest 10 min|Cook thin crispy dosas on hot tawa")),

  dict(name="Ragi Idli",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Hard",cook_time=50,cal=140,prot=4,carb=26,fat=2,
       p_min=1,p_typ=1.5,p_max=2,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="3 idlis (~150g)",
         ingredients="Ragi flour 60g|Urad dal 30g (soaked, ground)|Water as needed|Salt to taste",
         steps="Mix ragi flour with ground urad dal batter; add salt; ferment 6-8 hr|Steam in idli moulds 12-15 min")),

  dict(name="Thalipeeth",meal_type="Breakfast; Lunch",food_type="vegan",food_group="grain_breakfast",
       difficulty="Medium",cook_time=25,cal=265,prot=9,carb=42,fat=6,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="2 thalipeeth (~200g)",
         ingredients="Bhajani flour (multigrain) 100g|Onion 60g (chopped)|Green chilli 1|Fresh coriander 2 tbsp|Ajwain ¼ tsp|Oil 10ml|Salt to taste|Water as needed",
         steps="Mix bhajani flour with onion, chilli, coriander, ajwain, salt|Add water; knead to soft dough|Flatten on oiled tawa using wet hand — no rolling pin|Make a hole in center; cook on medium with oil 3 min each side")),

  dict(name="Puttu",meal_type="Breakfast; Lunch",food_type="vegan",food_group="south_indian",
       difficulty="Medium",cook_time=25,cal=210,prot=4,carb=44,fat=2,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="1 cylinder (~150g)",
         ingredients="Rice flour (puttu podi) 80g|Coconut (grated) 30g|Water as needed|Salt to taste",
         steps="Mix flour with salt; sprinkle water until it holds shape when pressed but crumbles|Layer coconut and flour alternately in puttu maker cylinder|Steam 8-10 min until steam comes through|Push out and serve with kadala curry or banana")),
]

# ── NORTH INDIAN VEG ──────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Aloo Matar",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=25,cal=220,prot=6,carb=32,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Potato 120g (cubed)|Peas 80g (fresh/frozen)|Onion 60g|Tomato 50g|Ginger-garlic paste 1 tsp|Cumin seeds 1 tsp|Coriander powder 1 tsp|Garam masala ¼ tsp|Oil 10ml|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil; add cumin; add onion; cook 4 min|Add ginger-garlic paste; cook 1 min|Add tomato and spices; cook 4 min|Add potato; stir; cook covered 8 min|Add peas; cook covered 5 min|Garnish coriander")),

  dict(name="Aloo Palak",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Medium",cook_time=25,cal=195,prot=5,carb=26,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Potato 100g (cubed, boiled)|Spinach 150g|Onion 60g|Tomato 40g|Garlic 3 cloves|Ginger 1 tsp|Oil 10ml|Cumin ½ tsp|Garam masala ¼ tsp|Salt to taste",
         steps="Blanch spinach 2 min; blend coarsely|Heat oil; add cumin; add onion; cook golden|Add garlic, ginger; cook 1 min|Add tomato; cook 3 min|Add spinach puree; simmer 5 min|Add boiled potato; cook 3 min")),

  dict(name="Kashmiri Aloo",meal_type="Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Medium",cook_time=30,cal=245,prot=4,carb=30,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Potato 200g (whole small, boiled, peeled)|Mustard oil 12ml|Fennel powder 1 tsp|Ginger powder ½ tsp|Kashmiri red chilli 1 tsp|Yogurt 30ml|Asafoetida a pinch|Whole spices: cloves 2, cardamom 1|Salt to taste",
         steps="Fry boiled potatoes in mustard oil until golden; remove|In same oil add asafoetida, whole spices; fry 30 sec|Add yogurt mixed with fennel, ginger, chilli; stir quickly|Add potato; coat well; simmer 8 min on low|Add a little water if needed")),

  dict(name="Jeera Aloo",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=215,prot=3,carb=30,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Potato 200g (boiled, diced)|Cumin seeds 1.5 tsp|Oil 12ml|Turmeric ¼ tsp|Coriander powder ½ tsp|Amchur ¼ tsp|Red chilli ¼ tsp|Salt to taste|Fresh coriander 2 tbsp",
         steps="Heat oil in pan; add cumin; let splutter|Add boiled potato; toss to coat|Add all dry spices; stir well|Cook 5-7 min on medium until edges crispy|Garnish coriander")),

  dict(name="Dahi Aloo",meal_type="Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=235,prot=6,carb=32,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Potato 180g (boiled, diced)|Yogurt 80ml|Cumin seeds 1 tsp|Mustard seeds ½ tsp|Turmeric ¼ tsp|Red chilli ¼ tsp|Oil 8ml|Salt to taste|Fresh coriander 2 tbsp",
         steps="Beat yogurt smooth|Heat oil; add mustard and cumin; let splutter|Add potato; stir 2 min|Reduce heat; add yogurt; stir quickly to prevent curdling|Add spices; cook gently 5 min|Garnish coriander")),

  dict(name="Dum Aloo",meal_type="Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Medium",cook_time=35,cal=255,prot=5,carb=30,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Baby potatoes 250g (boiled, peeled)|Yogurt 60ml|Tomato puree 60ml|Onion 80g|Ginger-garlic paste 1 tbsp|Kashmiri chilli 1 tsp|Garam masala ½ tsp|Oil 12ml|Bay leaf 1|Whole spices: cloves 3, cardamom 2, cinnamon ½ inch|Salt to taste",
         steps="Prick potatoes all over; shallow fry in oil until golden; set aside|In same oil add whole spices; add onion; cook deep golden|Add ginger-garlic paste; cook 2 min|Add tomato puree; cook 5 min|Beat yogurt with chilli; add to pan; stir quickly|Add potatoes; simmer 15 min covered on very low heat")),

  dict(name="Dhaniya Ke Aloo",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=208,prot=3,carb=28,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Potato 200g (boiled, diced)|Fresh coriander 50g (blended to paste)|Garlic 3 cloves|Green chilli 2|Cumin seeds 1 tsp|Oil 12ml|Lemon juice 1 tsp|Salt to taste",
         steps="Blend coriander with garlic, chilli and a little water to paste|Heat oil; add cumin; add coriander paste; cook 2 min|Add potato; toss well; cook 5 min|Finish with lemon juice")),

  dict(name="Gobi Matar",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=25,cal=180,prot=5,carb=22,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~280g)",
         ingredients="Cauliflower 200g (florets)|Peas 80g|Onion 60g|Tomato 50g|Ginger-garlic paste 1 tsp|Cumin seeds 1 tsp|Coriander powder 1 tsp|Oil 10ml|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil; add cumin; add onion; cook 3 min|Add ginger-garlic paste; cook 1 min|Add tomato and spices; cook 3 min|Add cauliflower; stir; cook covered 10 min|Add peas; cook 5 min more")),

  dict(name="Bhindi Do Pyaza",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=25,cal=175,prot=4,carb=18,fat=9,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Okra 200g (sliced)|Onion 120g (sliced — double the usual amount)|Oil 12ml|Cumin seeds 1 tsp|Coriander powder 1 tsp|Amchur ¼ tsp|Red chilli ¼ tsp|Salt to taste",
         steps="Dry okra completely|Heat oil; add cumin; add HALF the onion; cook golden|Add okra; cook on medium-high WITHOUT covering 12 min|Add remaining raw onion and all spices; toss; cook 5 more min")),

  dict(name="Karela Masala",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Medium",cook_time=30,cal=155,prot=3,carb=16,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Bitter gourd 200g (thinly sliced)|Salt 1 tsp (for soaking)|Onion 80g|Tomato 50g|Coriander powder 1 tsp|Red chilli ¼ tsp|Amchur ½ tsp|Oil 12ml|Jaggery 1 tsp (optional)|Salt to taste",
         steps="Rub bitter gourd with salt; rest 20 min; squeeze out water and rinse|Heat oil; fry bitter gourd 8-10 min until slightly crispy; set aside|In same oil sauté onion golden; add tomato and spices; cook 3 min|Add bitter gourd back; add jaggery if desired; cook 5 min")),

  dict(name="Bharwa Karela",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Hard",cook_time=40,cal=180,prot=4,carb=18,fat=9,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 stuffed pieces (~200g)",
         ingredients="Bitter gourd 4 (whole)|Onion 80g (finely chopped)|Coriander powder 1 tsp|Amchur 1 tsp|Fennel powder ½ tsp|Red chilli ¼ tsp|Oil 12ml|Salt to taste",
         steps="Slit bitter gourd; rub salt inside and out; rest 30 min; rinse and squeeze|Mix onion with all spices for stuffing|Fill bitter gourd with stuffing; tie with thread if needed|Shallow fry in oil on medium 15-20 min turning carefully until cooked and crispy")),

  dict(name="Lauki Kofta",meal_type="Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Medium",cook_time=35,cal=225,prot=7,carb=22,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl with 4 koftas (~280g)",
         ingredients="Bottle gourd 250g (grated, squeezed)|Besan 40g|Oil for frying + 10ml for gravy|Onion 80g|Tomato 80g|Ginger-garlic paste 1 tbsp|Cream 20ml|Garam masala ½ tsp|Salt to taste",
         steps="Mix grated gourd with besan, salt; shape into small balls|Shallow fry koftas until golden; set aside|Make gravy: sauté onion golden; add ginger-garlic; cook 2 min; add tomato and spices; cook 5 min; add cream; simmer 3 min|Add koftas to gravy; cook 2 min (do not over-simmer or koftas break)")),

  dict(name="Lauki Channa Dal",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Easy",cook_time=30,cal=230,prot=11,carb=34,fat=6,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Bottle gourd 150g (diced)|Channa dal 60g (soaked 30 min)|Onion 60g|Tomato 50g|Ginger 1 tsp|Cumin seeds 1 tsp|Turmeric ¼ tsp|Oil 8ml|Salt to taste|Coriander 2 tbsp",
         steps="Pressure cook channa dal with turmeric 3 whistles|In a pan heat oil; add cumin; add onion; cook 3 min|Add ginger, tomato; cook 3 min|Add lauki and cooked dal; simmer 10 min until lauki is soft")),

  dict(name="Jeera Lauki",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=120,prot=2,carb=15,fat=6,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Bottle gourd 300g (peeled, diced)|Cumin seeds 1.5 tsp|Oil 8ml|Green chilli 1|Turmeric ¼ tsp|Salt to taste|Coriander 2 tbsp|Lemon juice ½ tsp",
         steps="Heat oil; add cumin and green chilli; splutter|Add lauki; stir; add turmeric and salt|Cook covered on medium-low 12-15 min until soft|Finish with lemon and coriander")),

  dict(name="Phool Gobi",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=145,prot=4,carb=16,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Cauliflower 300g (florets)|Oil 10ml|Cumin seeds 1 tsp|Turmeric ¼ tsp|Coriander powder 1 tsp|Red chilli ¼ tsp|Garam masala ¼ tsp|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil; add cumin; add cauliflower; stir coat|Add all dry spices; mix|Cook covered on medium 12 min, stirring occasionally|Uncover; cook 5 min until edges golden")),

  dict(name="Malai Broccoli",meal_type="Snack; Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Medium",cook_time=25,cal=195,prot=8,carb=12,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="1 serving (~200g)",
         ingredients="Broccoli 250g (florets, blanched 2 min)|Fresh cream 40ml|Yogurt 30ml|Ginger-garlic paste 1 tsp|Kashmiri chilli 1 tsp|Garam masala ¼ tsp|Kasuri methi 1 tsp|Oil 8ml|Salt to taste",
         steps="Mix cream, yogurt, ginger-garlic paste, all spices; marinate broccoli 30 min|Grill in oven at 220°C for 15 min OR cook in grill pan 8-10 min turning once")),

  dict(name="Kadhai Mushroom",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Medium",cook_time=25,cal=170,prot=6,carb=14,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Mushrooms 200g (sliced)|Capsicum 80g (diced)|Onion 80g (diced)|Tomato 80g (pureed)|Ginger-garlic paste 1 tbsp|Kadhai masala 1.5 tsp|Oil 12ml|Kasuri methi 1 tsp|Salt to taste|Coriander 2 tbsp",
         steps="Dry roast whole spices; coarsely grind to make kadhai masala (or use store-bought)|Heat oil; add onion; cook 3 min; add ginger-garlic; cook 1 min|Add tomato puree and kadhai masala; cook 5 min|Add mushrooms and capsicum; cook 8 min on high|Finish with kasuri methi and coriander")),

  dict(name="Veg Kolhapuri",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Hard",cook_time=35,cal=210,prot=6,carb=24,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~280g)",
         ingredients="Mixed veg 250g (potato, carrot, peas, cauliflower)|Onion 80g|Tomato 80g|Coconut 20g (grated)|Kolhapuri masala 2 tsp|Oil 12ml|Salt to taste|Coriander 2 tbsp",
         steps="Dry roast and blend coconut with spices to make base paste|Sauté onion golden; add paste; cook 5 min|Add tomato; cook 5 min|Add vegetables and water; simmer 15 min")),

  dict(name="Ratatouille",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Medium",cook_time=40,cal=165,prot=4,carb=20,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="mediterranean",
       detail=dict(serving="1 bowl (~300g)",
         ingredients="Eggplant 100g|Zucchini 80g|Capsicum 60g|Tomato 100g|Onion 60g|Garlic 3 cloves|Olive oil 12ml|Thyme 1 tsp|Basil fresh 2 tbsp|Salt and pepper to taste",
         steps="Slice all veg into thin rounds|Sauté onion and garlic in olive oil 3 min|Add tomato puree and herbs; simmer 5 min|Layer veg alternately in baking dish; drizzle olive oil|Bake 200°C for 25 min until tender and slightly caramelized")),
]

# ── DALS ──────────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Green Moong Dal",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Easy",cook_time=20,cal=245,prot=16,carb=34,fat=5,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Green moong dal (whole) 80g|Onion 60g|Tomato 50g|Ginger 1 tsp|Cumin seeds 1 tsp|Turmeric ¼ tsp|Oil 8ml|Salt to taste|Lemon juice ½ tsp|Coriander 2 tbsp",
         steps="Wash moong dal; cook in 3× water with turmeric 15-18 min (no soaking needed)|Heat oil; add cumin; add onion; cook golden|Add ginger, tomato; cook 3 min|Mix into cooked dal; simmer 5 min|Finish lemon and coriander")),

  dict(name="Panchmel Dal",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Medium",cook_time=35,cal=278,prot=15,carb=40,fat=7,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Mixed 5 dals 80g total (toor, channa, masoor, moong, urad — equal parts)|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tsp|Ghee 8ml|Cumin seeds 1 tsp|Bay leaf 1|Whole spices: cloves 2, cardamom 1|Garam masala ¼ tsp|Salt to taste",
         steps="Soak mixed dals 30 min; pressure cook 3 whistles|Heat ghee; add whole spices and cumin; add onion; cook golden|Add ginger-garlic, tomato and garam masala; cook 5 min|Mix into dal; simmer 10 min")),

  dict(name="Kala Chana",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Hard",cook_time=45,cal=295,prot=14,carb=44,fat=7,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Black chickpeas 80g (soaked overnight)|Onion 80g|Tomato 80g|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Amchur 1 tsp|Garam masala ½ tsp|Oil 10ml|Salt to taste",
         steps="Pressure cook soaked kala chana 5-6 whistles until soft|Sauté onion deep golden; add ginger-garlic; cook 2 min|Add tomato and all spices; cook 5 min|Add cooked chana with water; simmer 15 min until thick")),

  dict(name="Vatana Curry / Peeli Matar",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Medium",cook_time=40,cal=268,prot=13,carb=42,fat=6,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g) — yellow dried peas curry, served with kulche",
         ingredients="Dried yellow peas (vatana/peeli matar) 80g (soaked overnight)|Onion 80g|Tomato 80g|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Amchur 1 tsp|Red chilli ½ tsp|Oil 10ml|Salt to taste|Coriander 2 tbsp",
         steps="Pressure cook soaked vatana 4-5 whistles until very soft — they should be creamy|Sauté onion golden; add ginger-garlic; cook 2 min|Add tomato and spices; cook 5 min|Mash some peas in pot for thick gravy; simmer 10 min|Garnish coriander; serve with kulche or bhatura")),

  dict(name="Moong Dal Khichdi",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="complete_meal",
       difficulty="Easy",cook_time=25,cal=320,prot=12,carb=52,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 bowl (~300g)",
         ingredients="Rice 60g|Yellow moong dal 40g|Ghee 10ml|Cumin seeds 1 tsp|Turmeric ¼ tsp|Ginger 1 tsp|Asafoetida a pinch|Water 400ml|Salt to taste",
         steps="Wash and soak rice+dal 15 min|Heat ghee in pressure cooker; add cumin, asafoetida, ginger|Add rice-dal; stir 1 min; add water, turmeric, salt|Pressure cook 2 whistles; rest 10 min|Serve soft and slightly mushy — consistency of thick porridge")),
]

# ── RICE DISHES ───────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Peas Pulao",meal_type="Lunch; Dinner",food_type="vegan",food_group="rice",
       difficulty="Easy",cook_time=25,cal=360,prot=8,carb=68,fat=6,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="1 plate (~280g)",
         ingredients="Basmati rice 80g|Peas 60g|Onion 40g|Ghee 8ml|Bay leaf 1|Cumin seeds 1 tsp|Cloves 2|Water 160ml|Salt to taste|Mint leaves 10",
         steps="Soak rice 20 min; drain|Heat ghee; add whole spices; add onion; cook 3 min|Add peas; stir 1 min; add rice; stir gently|Add water, salt, mint; bring to boil; cover; cook 12 min on low; fluff")),

  dict(name="Ghee Rice",meal_type="Lunch; Dinner",food_type="veg",food_group="rice",
       difficulty="Easy",cook_time=25,cal=420,prot=6,carb=72,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_starch",cuisine="south_indian",
       detail=dict(serving="1 plate (~280g)",
         ingredients="Basmati rice 80g|Ghee 15ml|Onion 40g (sliced)|Bay leaf 1|Cloves 3|Cardamom 2|Cinnamon ½ inch|Cashews 15g|Raisins 10g|Water 160ml|Salt to taste",
         steps="Soak rice 20 min; drain|Heat ghee; fry cashews golden; remove|Fry raisins till they puff; remove|Add whole spices; add onion; cook golden|Add rice; stir 1 min; add water and salt; cook 12 min covered|Top with cashews and raisins")),

  dict(name="Methi Rice",meal_type="Lunch; Dinner",food_type="vegan",food_group="rice",
       difficulty="Easy",cook_time=25,cal=345,prot=7,carb=62,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="1 plate (~280g)",
         ingredients="Basmati rice 80g|Fresh fenugreek (methi) leaves 60g|Onion 40g|Garlic 3 cloves|Oil 10ml|Cumin seeds 1 tsp|Turmeric ¼ tsp|Water 160ml|Salt to taste",
         steps="Soak rice 20 min; drain|Heat oil; add cumin; add garlic and onion; cook 3 min|Add methi leaves; cook 3 min until wilted|Add rice; stir; add water, turmeric, salt; cover; cook 12 min")),

  dict(name="Mint Pulao",meal_type="Lunch; Dinner",food_type="vegan",food_group="rice",
       difficulty="Easy",cook_time=25,cal=355,prot=7,carb=65,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="1 plate (~280g)",
         ingredients="Basmati rice 80g|Fresh mint leaves 30g|Coriander 20g|Green chilli 2|Garlic 3 cloves|Ginger 1 tsp|Oil 10ml|Cumin seeds 1 tsp|Water 160ml|Salt to taste",
         steps="Blend mint, coriander, chilli, garlic, ginger to paste|Heat oil; add cumin; add paste; cook 2 min|Add rice; stir 1 min; add water and salt; cover; cook 12 min")),

  dict(name="Egg Pulao",meal_type="Lunch; Dinner",food_type="egg",food_group="rice",
       difficulty="Medium",cook_time=30,cal=415,prot=16,carb=62,fat=12,
       p_min=0.5,p_typ=1,p_max=1.25,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~320g)",
         ingredients="Basmati rice 80g|Eggs 2 (hard boiled, halved)|Onion 60g|Tomato 50g|Ginger-garlic paste 1 tsp|Whole spices (bay, cloves, cardamom, cinnamon)|Oil 10ml|Water 160ml|Garam masala ¼ tsp|Salt to taste",
         steps="Soak rice 20 min; drain|Fry eggs in oil until golden outside; remove|In same oil fry whole spices; add onion golden; add ginger-garlic; cook 1 min|Add tomato and garam masala; cook 3 min|Add rice; stir; add water and salt; cook 12 min covered; place eggs on top")),

  dict(name="Curd Rice",meal_type="Breakfast; Lunch; Dinner",food_type="veg",food_group="rice",
       difficulty="Easy",cook_time=20,cal=310,prot=9,carb=52,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="1 bowl (~300g)",
         ingredients="Cooked rice 150g|Yogurt 100ml|Milk 30ml|Ginger ½ tsp|Green chilli 1|Mustard seeds 1 tsp|Curry leaves 6|Dried red chilli 1|Oil 6ml|Salt to taste|Pomegranate 20g (optional garnish)",
         steps="Mix warm rice with milk; mash slightly; cool|Beat yogurt smooth; mix into rice|Prepare tadka: heat oil; add mustard seeds; add curry leaves, dried chilli|Mix tadka into rice; add ginger and green chilli; adjust salt|Refrigerate 30 min; serve cold with pickle")),

  dict(name="Schezuan Fried Rice",meal_type="Lunch; Dinner",food_type="vegan",food_group="rice",
       difficulty="Medium",cook_time=25,cal=420,prot=9,carb=72,fat=11,
       p_min=0.5,p_typ=1,p_max=1.25,role="complete_meal",cuisine="indo_chinese",
       detail=dict(serving="1 plate (~300g)",
         ingredients="Cooked rice 180g (day-old)|Schezuan sauce 2 tbsp|Mixed veg 100g (capsicum, carrot, spring onion, cabbage)|Garlic 4 cloves|Soy sauce 1 tbsp|Oil 10ml|Black pepper ½ tsp|Salt to taste|Spring onion 2 tbsp",
         steps="Heat wok on high; add oil; fry garlic 30 sec|Add vegetables; stir-fry 3 min|Add schezuan sauce and soy; stir|Add rice; toss on high heat 3-4 min|Finish black pepper and spring onion")),

  dict(name="Cauliflower Rice",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=15,cal=85,prot=4,carb=10,fat=3,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Cauliflower 300g|Garlic 2 cloves|Oil 8ml|Salt and pepper to taste|Lemon juice 1 tsp|Herbs as desired",
         steps="Pulse cauliflower in food processor to rice-sized grains; or grate coarsely|Heat oil; add garlic 30 sec|Add cauliflower rice; stir-fry 5-7 min until slightly golden|Season with salt, pepper, lemon juice")),
]

# ── BIRYANIS ──────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Hyderabadi Chicken Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=90,cal=520,prot=30,carb=62,fat=15,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~380g)",
         ingredients="Basmati rice 100g|Chicken 150g (bone-in)|Yogurt 60ml|Fried onions 40g|Saffron a pinch in 2 tbsp milk|Ginger-garlic paste 1.5 tbsp|Whole spices (bay, cloves, cardamom, cinnamon, star anise)|Ghee 15ml|Biryani masala 1.5 tsp|Mint 15g|Coriander 15g|Lemon juice 1 tbsp|Salt to taste",
         steps="Marinate chicken: yogurt, ginger-garlic, biryani masala, half fried onions, lemon, salt — 2 hr|Parboil rice with whole spices until 70% cooked; drain|Layer chicken at bottom; layer rice on top; drizzle ghee and saffron milk|Scatter mint, coriander, remaining fried onions|Seal pot with dough or tight lid; dum cook 35 min on very low heat")),

  dict(name="Hyderabadi Mutton Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=120,cal=580,prot=28,carb=60,fat=22,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~380g)",
         ingredients="Basmati rice 100g|Mutton 150g (bone-in)|Yogurt 80ml|Fried onions 50g|Saffron in milk|Ginger-garlic paste 2 tbsp|Whole spices|Ghee 20ml|Biryani masala 2 tsp|Papaya paste 1 tbsp (tenderiser)|Mint and coriander 20g each|Salt to taste",
         steps="Marinate mutton with papaya paste, yogurt, all spices — 4 hr min (overnight better)|Slow cook mutton 45 min until 80% done|Parboil rice 70%|Layer mutton then rice; drizzle ghee and saffron milk; scatter herbs|Dum cook 45 min on very low")),

  dict(name="Hyderabadi Veg Biryani",meal_type="Lunch; Dinner",food_type="veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=445,prot=10,carb=72,fat=14,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~350g)",
         ingredients="Basmati rice 100g|Mixed veg 200g (potato, carrot, cauliflower, peas, paneer 50g)|Yogurt 60ml|Fried onions 40g|Saffron in milk|Ginger-garlic paste 1 tbsp|Biryani masala 1.5 tsp|Ghee 12ml|Mint and coriander 15g each|Salt to taste",
         steps="Parboil rice 70%; drain|Cook veg with spices and yogurt until 80% done|Layer veg then rice; drizzle ghee and saffron|Dum cook 25 min")),

  dict(name="Lucknowi Chicken Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=90,cal=510,prot=28,carb=64,fat=15,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~380g)",
         ingredients="Basmati rice 100g|Chicken 150g|Yogurt 60ml|Fried onions 40g|Saffron in milk|Ginger-garlic paste 1.5 tbsp|Rose water 1 tsp|Kewra water 1 tsp|Ghee 15ml|Awadhi biryani masala 1.5 tsp|Mint 15g|Salt to taste",
         steps="Marinate chicken in yogurt and awadhi spices 2 hr — note: NO tomato, milder than Hyderabadi|Parboil rice with whole spices 70%|Layer and dum cook 30 min; finish with rose water and kewra water — these are key to Lucknowi style")),

  dict(name="Lucknowi Mutton Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=120,cal=570,prot=26,carb=62,fat=22,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~380g)",
         ingredients="Basmati rice 100g|Mutton 150g|Yogurt 80ml|Fried onions 50g|Saffron in milk|Ginger-garlic paste 2 tbsp|Rose water 1 tsp|Kewra water 1 tsp|Ghee 20ml|Awadhi biryani masala 2 tsp|Mint 15g|Salt to taste",
         steps="Marinate mutton overnight; slow cook 50 min|Parboil rice 70%|Layer and dum cook 40 min; finish with rose and kewra water")),

  dict(name="Lucknowi Veg Biryani",meal_type="Lunch; Dinner",food_type="veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=440,prot=9,carb=74,fat=13,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~350g)",
         ingredients="Basmati rice 100g|Mixed veg 200g|Yogurt 60ml|Fried onions 40g|Rose water 1 tsp|Kewra water 1 tsp|Ghee 12ml|Awadhi masala 1.5 tsp|Salt to taste",
         steps="Cook veg with spices; parboil rice; layer and dum cook 25 min; finish with rose and kewra water")),

  dict(name="Kolkata Chicken Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=90,cal=535,prot=28,carb=66,fat=17,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~400g with potato)",
         ingredients="Basmati rice 100g|Chicken 120g|Potato 80g (whole, boiled, fried golden)|Egg 1 (hard boiled, halved)|Yogurt 60ml|Fried onions 40g|Saffron in milk|Ginger-garlic paste 1.5 tbsp|Attar/rose water 1 tsp|Ghee 15ml|Kolkata biryani masala 1.5 tsp|Salt to taste",
         steps="Key feature: Kolkata biryani includes potato and egg — this is non-negotiable|Marinate chicken 2 hr|Parboil rice 70%|Layer chicken, fried potato, egg, rice; drizzle ghee and saffron; finish with rose water|Dum cook 30 min")),

  dict(name="Kolkata Mutton Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=120,cal=595,prot=26,carb=64,fat=25,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~400g with potato)",
         ingredients="Basmati rice 100g|Mutton 130g|Potato 80g (whole, fried)|Egg 1 (halved)|Yogurt 80ml|Fried onions 50g|Saffron in milk|Ghee 20ml|Kolkata biryani masala 2 tsp|Rose water 1 tsp|Salt to taste",
         steps="Marinate mutton overnight; slow cook 50 min|Layer with potato and egg; dum cook 45 min")),

  dict(name="Malabar Chicken Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=75,cal=525,prot=30,carb=60,fat=18,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="1 plate (~370g)",
         ingredients="Kaima/jeerakasala rice 100g (short-grain)|Chicken 150g|Coconut milk 60ml|Fried onions 50g|Ginger-garlic paste 2 tbsp|Green chilli 3|Whole spices|Ghee 15ml|Fresh coconut 20g|Mint 15g|Coriander 15g|Salt to taste",
         steps="Key difference: uses kaima rice and coconut milk — very fragrant|Cook chicken in coconut milk and spices|Parboil rice separately; layer; dum cook 25 min")),

  dict(name="Malabar Fish Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=490,prot=28,carb=58,fat=16,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="south_indian",
       detail=dict(serving="1 plate (~360g)",
         ingredients="Kaima rice 100g|Fish (kingfish/pomfret) 150g|Coconut milk 60ml|Fried onions 50g|Ginger-garlic paste 2 tbsp|Green chilli 3|Whole spices|Ghee 12ml|Curry leaves 10|Lemon juice 1 tbsp|Salt to taste",
         steps="Marinate fish with ginger-garlic, chilli, lemon 30 min; shallow fry briefly|Cook in coconut milk with spices 10 min|Parboil kaima rice; layer fish then rice; dum cook 20 min — careful not to overcook fish")),

  dict(name="Bombay Chicken Biryani",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=75,cal=515,prot=29,carb=62,fat=16,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~370g)",
         ingredients="Basmati rice 100g|Chicken 150g|Fried onions 50g|Tomato 80g|Yogurt 60ml|Ginger-garlic paste 2 tbsp|Biryani masala 2 tsp|Oil 15ml|Lemon juice 1 tbsp|Mint 15g|Saffron in milk|Salt to taste",
         steps="Bombay style is typically more masala-forward with tomato|Marinate chicken 2 hr|Cook masala with tomato until oil separates; add chicken; cook 20 min|Layer with parboiled rice; dum cook 25 min")),

  dict(name="Bombay Veg Biryani",meal_type="Lunch; Dinner",food_type="veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=445,prot=10,carb=72,fat=13,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 plate (~350g)",
         ingredients="Basmati rice 100g|Mixed veg 200g (including potato and paneer)|Fried onions 40g|Tomato 80g|Yogurt 60ml|Biryani masala 2 tsp|Oil 12ml|Mint 15g|Salt to taste",
         steps="Cook veg masala with tomato; parboil rice; layer and dum cook 25 min")),
]

# ── BREADS ────────────────────────────────────────────────────────────────────
RECIPES += [
  # Bread matrix
  dict(name="White Bread (Raw)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=0,cal=158,prot=5,carb=30,fat=2,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices (~60g)",
         ingredients="White bread 2 slices",
         steps="Eat as-is or use as base for sandwich|Pairs well with eggs, peanut butter, or jam")),

  dict(name="White Bread (Toasted)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=3,cal=162,prot=5,carb=31,fat=2,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted (~58g)",
         ingredients="White bread 2 slices",
         steps="Toast until golden; slight calorie reduction from moisture loss")),

  dict(name="White Bread (Toasted with Butter)",meal_type="Breakfast; Snack",food_type="veg",food_group="toast",
       difficulty="Easy",cook_time=3,cal=240,prot=5,carb=31,fat=10,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted with 10g butter",
         ingredients="White bread 2 slices|Butter 10g",
         steps="Toast bread until golden|Spread butter immediately while hot so it melts")),

  dict(name="Brown Bread (Raw)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=0,cal=146,prot=6,carb=27,fat=2,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices (~60g)",
         ingredients="Brown/whole wheat bread 2 slices",
         steps="Eat as-is or use as sandwich base|Higher fibre than white bread")),

  dict(name="Brown Bread (Toasted)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=3,cal=150,prot=6,carb=28,fat=2,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted (~58g)",
         ingredients="Brown/whole wheat bread 2 slices",
         steps="Toast until golden and crispy")),

  dict(name="Multigrain Bread (Raw)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=0,cal=178,prot=7,carb=31,fat=3,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices (~70g)",
         ingredients="Multigrain bread 2 slices",
         steps="Eat as-is; highest fibre and nutrient density of the bread varieties")),

  dict(name="Multigrain Bread (Toasted)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=3,cal=182,prot=7,carb=32,fat=3,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted (~68g)",
         ingredients="Multigrain bread 2 slices",
         steps="Toast until golden")),

  dict(name="Multigrain Bread (Toasted with Butter)",meal_type="Breakfast; Snack",food_type="veg",food_group="toast",
       difficulty="Easy",cook_time=3,cal=260,prot=7,carb=32,fat=11,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted with 10g butter",
         ingredients="Multigrain bread 2 slices|Butter 10g",
         steps="Toast until golden; spread butter while hot")),

  dict(name="Sourdough Bread (Raw)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=0,cal=186,prot=7,carb=36,fat=1,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices (~70g)",
         ingredients="Sourdough bread 2 slices",
         steps="Lower glycemic index than regular bread due to fermentation|Eat as-is or as sandwich base")),

  dict(name="Sourdough Bread (Toasted)",meal_type="Breakfast; Snack",food_type="vegan",food_group="toast",
       difficulty="Easy",cook_time=3,cal=190,prot=7,carb=37,fat=1,
       p_min=1,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="2 slices toasted (~68g)",
         ingredients="Sourdough bread 2 slices",
         steps="Toast until golden and crispy — sourdough toasts beautifully")),

  # Indian flatbreads
  dict(name="Makki Di Roti",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="roti",
       difficulty="Medium",cook_time=20,cal=190,prot=4,carb=34,fat=4,
       p_min=1,p_typ=2,p_max=3,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="2 rotis (~120g)",
         ingredients="Maize flour (makki atta) 100g|Water ~60ml (warm)|Salt a pinch|Ghee 5ml",
         steps="Mix flour with salt; add warm water gradually — use WARM water; maize flour needs it|Knead to firm dough; rest 5 min|Flatten with wet hands (maize flour is tricky to roll — use palm)|Cook on medium tawa 2 min per side; apply ghee; serve with sarson da saag")),

  dict(name="Bajra Roti",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="roti",
       difficulty="Medium",cook_time=15,cal=180,prot=5,carb=32,fat=4,
       p_min=1,p_typ=2,p_max=3,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="2 rotis (~120g)",
         ingredients="Pearl millet flour (bajra atta) 100g|Water ~60ml (warm)|Salt a pinch|Ghee 5ml",
         steps="Mix bajra flour with salt; knead with warm water to soft dough; rest 5 min|Pat out to 5-inch circle with wet hands (harder to roll than wheat)|Cook on hot tawa 2 min per side; best eaten fresh and hot with ghee")),

  dict(name="Jowar Roti",meal_type="Breakfast; Lunch; Dinner",food_type="vegan",food_group="roti",
       difficulty="Medium",cook_time=15,cal=175,prot=5,carb=33,fat=3,
       p_min=1,p_typ=2,p_max=3,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="2 rotis (~120g)",
         ingredients="Sorghum flour (jowar atta) 100g|Water ~60ml (warm)|Salt a pinch|Ghee 5ml",
         steps="Knead jowar flour with warm water to smooth dough; rest 5 min|Roll thin with rolling pin (easier than makki or bajra)|Cook on hot tawa 2 min each side")),

  dict(name="Sattu Paratha",meal_type="Breakfast; Lunch",food_type="vegan",food_group="roti",
       difficulty="Medium",cook_time=25,cal=320,prot=12,carb=46,fat=9,
       p_min=0.5,p_typ=1,p_max=2,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="2 parathas (~200g)",
         ingredients="Whole wheat flour 100g|Sattu (roasted chana flour) 60g|Onion 30g (finely chopped)|Green chilli 1|Ginger 1 tsp|Ajwain ¼ tsp|Lemon juice 1 tsp|Mustard oil 5ml|Ghee 8ml for cooking|Salt to taste",
         steps="Mix sattu with onion, chilli, ginger, ajwain, lemon, mustard oil and salt for filling|Make wheat flour dough; rest 10 min|Roll dough; place sattu filling; seal and roll to paratha|Cook on hot tawa with ghee until golden")),

  dict(name="Roomali Roti",meal_type="Lunch; Dinner",food_type="vegan",food_group="roti",
       difficulty="Hard",cook_time=30,cal=145,prot=4,carb=28,fat=2,
       p_min=1,p_typ=2,p_max=4,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="2 rotis (~100g)",
         ingredients="Maida 60g|Whole wheat flour 40g|Water ~50ml|Salt a pinch|Oil 3ml",
         steps="Knead very soft, elastic dough; rest 20 min|Roll paper-thin — as thin as a handkerchief|Cook on INVERTED wok (tawa upside down) for just 30-40 seconds — it cooks instantly|Fold into quarters; serve immediately")),

  dict(name="Kulcha",meal_type="Breakfast; Lunch; Dinner",food_type="veg",food_group="roti",
       difficulty="Medium",cook_time=25,cal=225,prot=6,carb=38,fat=6,
       p_min=0.5,p_typ=1,p_max=2,role="anchor_starch",cuisine="north_indian",
       detail=dict(serving="1 kulcha (~120g)",
         ingredients="Maida 100g|Yogurt 30ml|Baking soda ¼ tsp|Sugar ½ tsp|Oil 8ml|Nigella seeds (kalonji) ½ tsp|Salt to taste|Butter 8g for finishing",
         steps="Mix maida with yogurt, baking soda, sugar, salt, oil; knead soft; rest 2 hr|Roll to oval shape; sprinkle kalonji; fold and re-roll|Cook on hot tawa on medium 2 min; finish in flame 10 sec for char marks|Apply butter while hot")),

  dict(name="Egg Paratha",meal_type="Breakfast; Lunch",food_type="egg",food_group="roti",
       difficulty="Medium",cook_time=15,cal=295,prot=12,carb=32,fat=13,
       p_min=0.5,p_typ=1,p_max=2,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 paratha (~160g)",
         ingredients="Whole wheat flour 80g|Egg 2|Onion 30g (chopped)|Green chilli 1|Coriander 1 tbsp|Ghee 8ml|Salt to taste",
         steps="Make soft dough; rest 10 min; roll thin circle|Beat egg with onion, chilli, coriander, salt|Pour egg mix on rolled dough; fold edges over to seal|Cook on hot tawa pressing gently; apply ghee; cook both sides until golden")),
]

# ── CHICKEN DISHES ────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Kadai Chicken",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=35,cal=360,prot=30,carb=16,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Chicken 200g (bone-in or breast)|Capsicum 80g (diced)|Onion 80g (diced)|Tomato 100g|Ginger-garlic paste 1.5 tbsp|Kadai masala 2 tsp|Oil 12ml|Kasuri methi 1 tsp|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil in kadai (wok); cook onion 3 min; add ginger-garlic; cook 1 min|Add tomato and kadai masala; cook 6 min|Add chicken; cook on high 5 min; reduce heat; cook covered 15 min|Add capsicum; cook 3 min; finish kasuri methi")),

  dict(name="Chicken Korma",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=45,cal=395,prot=30,carb=12,fat=26,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Chicken 200g|Yogurt 80ml|Onion 100g (fried golden, blended)|Cashew 20g (soaked, blended)|Cream 30ml|Ginger-garlic paste 1.5 tbsp|Whole spices|Ghee 15ml|Coriander powder 1 tsp|Garam masala ½ tsp|Salt to taste|Saffron in 2 tbsp milk",
         steps="Make korma paste: blend fried onion and cashew together|Heat ghee; add whole spices; add korma paste; cook 5 min|Add yogurt in parts, stirring; add ginger-garlic; cook 5 min|Add chicken; cook covered 20 min|Stir in cream and saffron; simmer 5 min")),

  dict(name="Chicken Vindaloo",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=50,cal=350,prot=30,carb=12,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Chicken 200g|Vindaloo masala paste 3 tbsp (red chilli, vinegar, garlic, ginger, spices)|Onion 80g|Tomato 60g|Mustard oil 12ml|Vinegar 1 tbsp|Salt to taste",
         steps="Marinate chicken in vindaloo paste and vinegar 4 hr|Heat mustard oil; fry onion golden; add marinated chicken|Cook on high 5 min; add tomato; cook covered 25 min|Should be fiery, tangy and dry-ish gravy — Goan origin")),

  dict(name="Garlic Chicken",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Easy",cook_time=25,cal=310,prot=32,carb=8,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 serving (~200g)",
         ingredients="Chicken breast 200g|Garlic 8 cloves (minced)|Butter 15g|Olive oil 8ml|Lemon juice 1 tbsp|Thyme 1 tsp|Rosemary ½ tsp|Salt and pepper to taste|Parsley 2 tbsp",
         steps="Season chicken; sear in olive oil on high 3 min per side|Reduce heat; add butter and garlic; baste chicken with garlic butter 2 min|Add herbs; rest 5 min before slicing|Finish with lemon juice and parsley")),

  dict(name="Lemon Chicken",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Easy",cook_time=25,cal=295,prot=32,carb=6,fat=15,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 serving (~200g)",
         ingredients="Chicken breast 200g|Lemon 1 (juice and zest)|Garlic 3 cloves|Olive oil 10ml|Honey 1 tsp|Thyme ½ tsp|Salt and pepper to taste|Capers 1 tsp (optional)",
         steps="Marinate chicken in lemon juice, zest, garlic, olive oil, honey, thyme — 30 min|Sear in pan 4-5 min per side until cooked through|Deglaze pan with remaining marinade; pour over chicken")),

  dict(name="Kung Pao Chicken",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=25,cal=340,prot=30,carb=18,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Chicken breast 150g (diced)|Peanuts 20g|Dried red chilli 6|Szechuan peppercorns 1 tsp|Garlic 4 cloves|Ginger 1 tsp|Spring onion 3 stalks|Soy sauce 2 tbsp|Rice vinegar 1 tbsp|Sesame oil 5ml|Oil 10ml|Cornstarch 1 tsp",
         steps="Marinate chicken with soy sauce and cornstarch 15 min|Heat wok on high; fry peanuts till golden; remove|Fry dried chilli and peppercorns 30 sec|Add chicken; stir-fry 4 min|Add garlic, ginger; cook 30 sec|Add vinegar, sesame oil, spring onion; toss; add peanuts")),

  dict(name="Sweet and Sour Chicken",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=360,prot=26,carb=38,fat=12,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 serving (~300g)",
         ingredients="Chicken breast 150g (cubed)|Capsicum 60g|Pineapple 40g (chunks)|Onion 40g|Egg 1|Cornstarch 30g|Oil for frying + 10ml|Ketchup 2 tbsp|Vinegar 1 tbsp|Soy sauce 1 tbsp|Sugar 1 tsp",
         steps="Coat chicken in egg and cornstarch; deep fry until golden; drain|Make sauce: mix ketchup, vinegar, soy, sugar|Sauté capsicum, onion, pineapple 2 min|Add sauce; bring to boil; add fried chicken; toss")),

  dict(name="Chicken Katsu",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=25,cal=375,prot=30,carb=28,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~220g)",
         ingredients="Chicken breast 150g (flattened to 1cm)|Panko breadcrumbs 40g|Egg 1|Plain flour 20g|Oil for frying|Tonkatsu sauce 2 tbsp|Cabbage 50g (shredded)",
         steps="Pound chicken flat; season|Coat in flour → egg → panko|Shallow fry in oil 3-4 min per side until golden|Drain; slice diagonally; serve with tonkatsu sauce and cabbage")),

  dict(name="Chicken Manchurian",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=345,prot=26,carb=22,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="indo_chinese",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Chicken 150g (cubed)|Cornstarch 20g|Egg 1|Ginger 1 tsp|Garlic 4 cloves|Spring onion 3 stalks|Soy sauce 2 tbsp|Chilli sauce 1 tbsp|Vinegar 1 tsp|Oil for frying + 10ml|Salt to taste",
         steps="Coat chicken in egg, cornstarch, salt; deep fry until crispy|Heat oil; fry ginger, garlic 30 sec; add sauces; simmer 2 min|Add fried chicken; toss; garnish spring onion")),

  dict(name="Tandoori Chicken",meal_type="Lunch; Dinner; Snack",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=40,cal=285,prot=35,carb=6,fat=13,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 serving (2-3 pieces ~200g)",
         ingredients="Chicken 200g (bone-in, deep cuts made)|Yogurt 80ml|Ginger-garlic paste 2 tbsp|Tandoori masala 2 tsp|Kashmiri chilli 1 tsp|Lemon juice 2 tbsp|Mustard oil 8ml|Salt to taste|Lemon wedges and onion rings to serve",
         steps="Make deep cuts in chicken; apply lemon juice and salt; rest 15 min|Mix remaining ingredients; coat chicken well; marinate minimum 4 hr (overnight better)|Grill at 220°C for 25-30 min turning once; OR grill pan 8-10 min per side|Serve with lemon wedges, onion rings, and mint chutney")),

  dict(name="Chicken Tikka",meal_type="Snack; Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=255,prot=32,carb=6,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="6 pieces (~180g boneless)",
         ingredients="Chicken breast 150g (cubed)|Yogurt 50ml|Ginger-garlic paste 1.5 tbsp|Tandoori masala 1.5 tsp|Kashmiri chilli 1 tsp|Lemon juice 1 tbsp|Oil 8ml|Salt to taste|Kasuri methi 1 tsp",
         steps="Mix all marinade ingredients; coat chicken; marinate 2-4 hr|Thread on skewers; grill at 220°C 15-18 min turning once|OR grill pan on high 4-5 min per side")),

  dict(name="Keema Matar",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=355,prot=28,carb=16,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Minced meat (chicken or mutton) 150g|Peas 60g|Onion 80g|Tomato 80g|Ginger-garlic paste 1.5 tbsp|Coriander powder 1 tsp|Garam masala ½ tsp|Oil 12ml|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil; brown onion well; add ginger-garlic; cook 1 min|Add tomato and spices; cook 5 min|Add mince; break with spoon; cook on high 5 min|Add peas and 80ml water; cook covered 10 min")),
]

# ── MUTTON / LAMB ─────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Laal Maas",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=75,cal=410,prot=28,carb=10,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Mutton 200g (bone-in)|Mathania red chilli 8 (soaked in water) OR Kashmiri chilli 2 tsp|Yogurt 80ml|Onion 100g|Garlic 8 cloves|Mustard oil 15ml|Whole spices (cloves, cardamom, bay leaf)|Salt to taste",
         steps="Rajasthani preparation — very fiery|Heat mustard oil until smoking; add whole spices|Add onion; cook deep brown 15 min|Blend soaked red chilli with garlic to paste; add; cook 8 min|Add mutton; cook on high 8 min; add yogurt; cook covered 40 min|Should be dark red, very spicy — add water as needed")),

  dict(name="Lamb Chops",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=370,prot=30,carb=4,fat=26,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="2 chops (~180g)",
         ingredients="Lamb chops 2 (~180g)|Garlic 3 cloves (minced)|Rosemary 1 tsp|Olive oil 10ml|Lemon juice 1 tbsp|Salt and black pepper to taste",
         steps="Score chops; rub with garlic, rosemary, olive oil, lemon, salt, pepper|Marinate 1 hr (or overnight)|Heat grill pan on high until smoking|Cook 3-4 min per side for medium-rare; 5 min for medium|Rest 5 min before serving")),

  dict(name="Lamb Kofta",meal_type="Snack; Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=320,prot=24,carb=12,fat=20,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="4 koftas (~180g)",
         ingredients="Minced lamb 150g|Onion 40g (grated)|Ginger-garlic paste 1 tsp|Garam masala ½ tsp|Cumin powder ½ tsp|Green chilli 1|Coriander 2 tbsp|Salt to taste|Oil 8ml",
         steps="Mix all ingredients thoroughly; shape into elongated balls or cylinders|Thread on skewers; grill or pan-fry on medium 8-10 min turning regularly")),

  dict(name="Galouti Kebab",meal_type="Snack; Lunch",food_type="non-veg",food_group="kabab",
       difficulty="Hard",cook_time=40,cal=295,prot=20,carb=14,fat=18,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 kebabs (~160g)",
         ingredients="Minced lamb/mutton 150g|Papaya paste 1 tbsp (tenderiser)|Onion 30g (fried, blended)|Garam masala 1 tsp|Rose water ½ tsp|Kewra water ½ tsp|Besan 15g|Ghee 10ml|Salt to taste",
         steps="Marinate mince with papaya paste 2 hr — this is what makes them melt-in-mouth|Mix in all other ingredients; rest 30 min in fridge|Shape into flat round patties|Shallow fry in ghee on medium 3-4 min per side — DO NOT press")),

  dict(name="Shami Kebab",meal_type="Snack; Lunch",food_type="non-veg",food_group="kabab",
       difficulty="Medium",cook_time=45,cal=270,prot=20,carb=16,fat=14,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 kebabs (~160g)",
         ingredients="Minced meat 120g|Channa dal 30g|Onion 30g|Ginger-garlic paste 1 tsp|Whole spices (cloves, peppercorns, cardamom)|Egg 1|Oil 8ml|Salt to taste",
         steps="Pressure cook mince with dal, onion, whole spices and water 3 whistles|Drain; blend smooth|Mix with egg and salt; shape into flat patties|Shallow fry in oil 3 min per side")),
]

# ── BEEF / PORK ───────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Steak Diane",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=20,cal=420,prot=34,carb=6,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 steak (~200g) with sauce",
         ingredients="Beef sirloin/tenderloin 150g|Butter 15g|Shallots 30g|Garlic 2 cloves|Dijon mustard 1 tsp|Worcestershire sauce 1 tbsp|Brandy 20ml (optional flambé)|Cream 30ml|Parsley 2 tbsp|Salt and pepper",
         steps="Season steak; sear in very hot pan 2-3 min per side for medium; rest|In same pan add butter; sauté shallots and garlic 1 min|Add Worcestershire and mustard; stir|Add brandy and flambé (tilt pan carefully) OR skip|Add cream; simmer 1 min; pour over steak")),

  dict(name="Beef Wellington",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=90,cal=520,prot=30,carb=30,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 portion (~250g with pastry)",
         ingredients="Beef fillet 150g|Puff pastry 80g|Mushrooms 80g (duxelles — very finely chopped, cooked dry)|Prosciutto/serrano ham 3 slices|Dijon mustard 1 tbsp|Egg 1 (wash)|Salt and pepper",
         steps="Sear beef fillet on all sides 2 min; coat with mustard; cool completely|Spread ham flat; cover with mushroom duxelles; wrap beef tightly|Wrap in pastry; egg wash; refrigerate 30 min|Bake 200°C for 25-30 min until pastry golden; internal temp 52°C for medium-rare|Rest 10 min before slicing")),

  dict(name="Beef Bourguignon",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=180,cal=470,prot=32,carb=20,fat=26,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 bowl (~300g)",
         ingredients="Beef chuck 200g (cubed)|Red wine 150ml|Bacon 30g|Mushrooms 60g|Pearl onions 40g|Carrots 40g|Garlic 3 cloves|Thyme 2 sprigs|Bay leaf 1|Butter 10g|Oil 10ml|Salt and pepper",
         steps="Marinate beef in wine with vegetables overnight|Brown bacon and vegetables; set aside; brown beef in batches|Return everything to pot; add wine and beef stock; add herbs|Simmer covered 2.5 hr at very low heat until fork-tender|Sauce should be rich and thick — reduce uncovered last 15 min")),

  dict(name="Sweet and Sour Pork",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=30,cal=375,prot=22,carb=36,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~280g)",
         ingredients="Pork belly/shoulder 150g (cubed)|Pineapple 40g|Capsicum 60g|Onion 40g|Egg 1|Cornstarch 30g|Oil for frying + 10ml|Ketchup 2 tbsp|Vinegar 1 tbsp|Soy sauce 1 tbsp|Sugar 1 tsp",
         steps="Coat pork in egg and cornstarch; deep fry until golden|Sauté vegetables and pineapple 2 min|Add sauce; toss in fried pork")),

  dict(name="Pork Ribs",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=120,cal=440,prot=28,carb=18,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 rack portion (~300g with bone)",
         ingredients="Pork ribs 300g|Dry rub (paprika, cumin, brown sugar, salt, pepper, garlic powder) 2 tbsp|BBQ sauce 3 tbsp|Oil 8ml",
         steps="Apply dry rub all over ribs; rest 1 hr (or overnight)|Wrap in foil; bake 160°C for 2 hr until tender|Unwrap; brush BBQ sauce; grill at 200°C for 15-20 min until caramelised")),

  dict(name="Char Siu",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=60,cal=350,prot=28,carb=20,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~180g sliced)",
         ingredients="Pork shoulder/belly 200g|Hoisin sauce 2 tbsp|Oyster sauce 1 tbsp|Soy sauce 1 tbsp|Honey 1 tbsp|Five spice ½ tsp|Sesame oil 5ml|Red food colour a few drops (optional)|Garlic 2 cloves",
         steps="Mix all sauce ingredients; marinate pork 4 hr minimum (overnight better)|Grill at 200°C for 25 min, basting every 8 min|Turn and grill 15 more min until caramelised and slightly charred|Rest 5 min; slice thin")),

  dict(name="Wiener Schnitzel",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=20,cal=390,prot=28,carb=24,fat=22,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 schnitzel (~200g)",
         ingredients="Veal or pork escalope 150g|Breadcrumbs 40g|Egg 1|Plain flour 20g|Oil/butter 15ml|Lemon 1|Salt and pepper",
         steps="Pound meat very thin (3-4mm); season|Coat in flour → beaten egg → breadcrumbs|Fry in generous oil on medium 2-3 min per side until golden|The schnitzel should 'swim' in oil — do not press|Drain; serve immediately with lemon")),

  dict(name="Tonkatsu",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=20,cal=395,prot=26,carb=26,fat=22,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~200g with sauce)",
         ingredients="Pork loin 150g (2cm thick)|Panko breadcrumbs 40g|Egg 1|Plain flour 20g|Oil for frying|Tonkatsu sauce 2 tbsp|Cabbage 60g (shredded)",
         steps="Score pork edges to prevent curling; season|Coat flour → egg → panko|Deep fry at 170°C for 6-8 min until golden|Drain; rest 2 min; slice diagonally|Serve with tonkatsu sauce and raw shredded cabbage")),

  dict(name="Osso Buco",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=150,cal=460,prot=32,carb=16,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 shank (~300g)",
         ingredients="Veal/lamb shank 300g (cross-cut)|Onion 60g|Carrot 40g|Celery 30g|Tomato 80g|White wine 100ml|Beef stock 200ml|Gremolata (lemon zest, garlic, parsley)|Flour 10g|Butter 10g|Oil 10ml|Salt and pepper",
         steps="Brown shanks on all sides; set aside|Sauté vegetables (soffritto) in butter 5 min|Add wine; reduce 2 min; add tomato and stock|Return shanks; cover; braise at 160°C for 2 hr until meat falls off bone|Finish with gremolata (lemon zest + garlic + parsley mixture)")),

  dict(name="Pork Sausages (Banger)",meal_type="Breakfast; Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Easy",cook_time=15,cal=295,prot=14,carb=6,fat=24,
       p_min=0.5,p_typ=1,p_max=2,role="anchor_protein",cuisine="continental",
       detail=dict(serving="2 sausages (~120g)",
         ingredients="Pork sausages 2|Oil 5ml",
         steps="Prick sausages; cook in pan on medium 12-15 min turning regularly until browned all over|OR bake at 200°C for 20 min|Part of Bangers and Mash — serve with mashed potato")),

  dict(name="Mashed Potato",meal_type="Breakfast; Lunch; Dinner",food_type="veg",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=215,prot=4,carb=32,fat=8,
       p_min=0.5,p_typ=1,p_max=2,role="anchor_starch",cuisine="continental",
       detail=dict(serving="1 portion (~200g)",
         ingredients="Potato 250g (boiled)|Butter 15g|Milk 30ml|Salt and white pepper to taste|Nutmeg a pinch (optional)",
         steps="Boil potatoes until very soft; drain; steam dry 1 min|Rice or mash while hot — lumps form when you overwork cold potato|Add warm butter and milk gradually; season; finish with nutmeg")),
]

# ── SEAFOOD ───────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Prawn Malai Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=310,prot=24,carb=10,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Prawns 150g (medium, cleaned)|Coconut milk 100ml|Onion 60g|Ginger-garlic paste 1 tbsp|Mustard oil 10ml|Green chilli 2|Garam masala ¼ tsp|Turmeric ¼ tsp|Salt to taste|Coriander 2 tbsp",
         steps="Marinate prawns with turmeric and salt 10 min|Heat mustard oil; fry onion till soft; add ginger-garlic; cook 1 min|Add green chilli and garam masala; cook 1 min|Pour coconut milk; simmer 5 min|Add prawns; cook 5-6 min only — overcooked prawns become rubbery")),

  dict(name="Prawn Balchao",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Hard",cook_time=35,cal=265,prot=22,carb=10,fat=14,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Prawns 150g|Onion 80g|Kashmiri chilli 8|Vinegar 3 tbsp|Garlic 6 cloves|Ginger 1 tsp|Mustard seeds ½ tsp|Oil 12ml|Sugar 1 tsp|Salt to taste",
         steps="Blend chilli, garlic, ginger with vinegar to paste|Heat oil; fry onion until crispy golden; add mustard seeds; pop|Add chilli paste; cook 8 min until oil separates|Add prawns; cook 6 min|Add sugar; simmer 5 min — Goan pickle-style spicy prawn")),

  dict(name="Fish Moilee",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=285,prot=22,carb=8,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Fish 150g (pomfret or kingfish)|Coconut milk 120ml|Onion 60g (sliced)|Green chilli 3|Ginger 1 tsp (julienned)|Curry leaves 8|Turmeric ¼ tsp|Mustard oil 10ml|Lemon juice 1 tsp|Salt to taste",
         steps="Heat oil; add mustard seeds; add curry leaves, ginger, onion; cook soft — do NOT brown|Add green chilli and turmeric; cook 1 min|Pour coconut milk; simmer 3 min|Add fish pieces; cook 8-10 min gently|Finish with lemon juice — very mild, white curry")),

  dict(name="Patra ni Machi (Pomfret)",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Hard",cook_time=45,cal=295,prot=26,carb=8,fat=17,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="parsi",
       detail=dict(serving="1 whole pomfret (~250g wrapped)",
         ingredients="Pomfret 1 whole (~250g, cleaned)|Green chutney (coriander 50g, mint 20g, coconut 30g, green chilli 3, garlic 3, lemon juice 2 tbsp, sugar 1 tsp, salt)|Banana leaves 2 (softened over flame)|String to tie",
         steps="Blend chutney ingredients to smooth paste|Score pomfret; apply generous chutney inside cavity and all over|Wrap tightly in banana leaf; tie with string|Steam 20-25 min until fish cooked through|OR bake 180°C wrapped in foil 25 min|Open at table for dramatic presentation and aroma")),

  dict(name="Grilled Salmon",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=15,cal=295,prot=30,carb=2,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~180g)",
         ingredients="Salmon fillet 180g|Lemon juice 1 tbsp|Olive oil 8ml|Garlic 2 cloves|Salt and pepper|Dill 1 tsp (optional)",
         steps="Marinate salmon in lemon, oil, garlic, salt, pepper — 15 min|Heat grill pan on high; cook 3-4 min per side|Salmon is done when it flakes easily; do not overcook|Finish with lemon and dill")),

  dict(name="Miso Glazed Salmon",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=20,cal=315,prot=30,carb=10,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 fillet (~180g)",
         ingredients="Salmon fillet 180g|White miso paste 2 tbsp|Sake/mirin 1 tbsp|Honey 1 tsp|Soy sauce 1 tsp|Sesame oil 3ml|Sesame seeds 1 tsp",
         steps="Mix miso, sake, honey, soy to glaze; coat salmon; marinate 30 min (up to 24 hr)|Grill at 200°C for 12-15 min until glaze is caramelised|Watch carefully — miso burns quickly|Garnish sesame seeds")),

  dict(name="Nicoise Salad",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=20,cal=310,prot=20,carb=18,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 large salad plate (~350g)",
         ingredients="Tuna (canned in water) 80g|Mixed greens 60g|Green beans 60g (blanched)|Cherry tomatoes 6|Olives 20g|Egg 2 (hard boiled, halved)|Potato 60g (boiled, sliced)|Olive oil 10ml|Lemon juice 1 tbsp|Dijon mustard ½ tsp|Anchovy paste ½ tsp (optional)|Salt and pepper",
         steps="Make dressing: whisk oil, lemon, mustard, anchovy, salt, pepper|Arrange greens on plate; top with green beans, tomatoes, potato, olives|Place tuna in centre; arrange egg halves|Drizzle dressing generously")),

  dict(name="Tuna Salad",meal_type="Lunch; Snack",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=5,cal=230,prot=22,carb=10,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Tuna canned in water 120g (drained)|Greek yogurt or light mayo 30g|Celery 30g (chopped)|Onion 20g (finely chopped)|Lemon juice 1 tsp|Dijon mustard ½ tsp|Salt and pepper",
         steps="Drain tuna; flake with fork|Mix with all ingredients|Serve on bread, with crackers, or on lettuce leaves|Can refrigerate up to 2 days")),

  dict(name="Fish Tikka",meal_type="Snack; Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=235,prot=28,carb=6,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="6 pieces (~180g)",
         ingredients="Fish (surmai/salmon/basa) 150g (cubed)|Yogurt 50ml|Ginger-garlic paste 1.5 tbsp|Tandoori masala 1.5 tsp|Kashmiri chilli 1 tsp|Lemon juice 1 tbsp|Oil 8ml|Besan 1 tsp|Salt to taste|Kasuri methi 1 tsp",
         steps="Mix marinade; coat fish; marinate 1 hr — fish needs less time than chicken|Thread on skewers; grill at 220°C 12-15 min|OR grill pan 3-4 min per side — fish tikka cooks faster than chicken")),

  # Meen Curry variants
  dict(name="Pomfret Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=30,cal=270,prot=24,carb=8,fat=15,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Pomfret 1 small (~200g, cleaned, scored)|Coconut milk 80ml|Onion 60g|Tomato 60g|Tamarind 15g|Kokum 2 pieces (OR use extra tamarind)|Green chilli 2|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Turmeric ¼ tsp|Mustard oil 10ml|Curry leaves 8|Salt to taste",
         steps="Make tamarind water (soak tamarind in warm water; strain)|Heat oil; add curry leaves; add onion; cook soft|Add ginger-garlic; cook 1 min; add tomato and spices; cook 4 min|Add tamarind water and coconut milk; simmer 5 min|Add pomfret; cook 10 min gently — pomfret is delicate")),

  dict(name="Seer Fish Curry (Vanjiram)",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=285,prot=28,carb=8,fat=15,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Seer fish / Surmai 150g (steaks)|Coconut 30g (grated)|Onion 60g|Tomato 60g|Tamarind 15g|Chilli powder 1 tsp|Coriander powder 1 tsp|Turmeric ¼ tsp|Mustard seeds 1 tsp|Curry leaves 8|Oil 10ml|Salt to taste",
         steps="Blend coconut with spices to paste|Heat oil; add mustard seeds; add curry leaves|Add onion; cook 3 min; add tomato; cook 3 min|Add coconut-spice paste; cook 5 min|Add tamarind water; simmer 5 min|Add fish steaks; cook 10 min until done")),

  dict(name="Red Snapper Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=30,cal=265,prot=26,carb=8,fat=13,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="south_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Red snapper 150g (fillets or steaks)|Coconut milk 80ml|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Turmeric ¼ tsp|Red chilli 1 tsp|Curry leaves 8|Oil 10ml|Salt to taste",
         steps="Heat oil; add curry leaves; add onion; cook soft|Add ginger-garlic; cook 1 min; add tomato and all spices; cook 4 min|Add coconut milk; simmer 4 min|Add red snapper; cook gently 8-10 min")),

  # Rohu variants
  dict(name="Catla Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=30,cal=260,prot=24,carb=8,fat=14,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~230g)",
         ingredients="Catla fish 200g (steaks)|Mustard paste 1 tbsp|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tbsp|Mustard oil 12ml|Turmeric ¼ tsp|Red chilli ½ tsp|Panch phoron ½ tsp|Salt to taste",
         steps="Marinate fish with turmeric and salt 15 min|Heat mustard oil until smoking; fry fish steaks 3 min per side; remove|In same oil add panch phoron; add onion; cook golden|Add ginger-garlic, tomato and spices; cook 5 min|Add mustard paste; cook 2 min; add 150ml water; simmer 5 min; add fish")),

  dict(name="Hilsa Curry (Ilish Maach)",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=310,prot=22,carb=6,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~230g) — Bengali staple",
         ingredients="Hilsa/Ilish fish 200g (steaks)|Mustard paste 2 tbsp (black + yellow mustard, ground with water)|Yogurt 30ml|Green chilli 4|Turmeric ½ tsp|Mustard oil 12ml|Salt to taste|Coriander to garnish",
         steps="Marinate fish with turmeric, salt, some mustard paste 15 min|Heat mustard oil; lightly fry fish 2 min per side; remove|In same oil add remaining mustard paste and green chilli; cook 2 min|Add yogurt; stir; add 100ml water|Add fish; cook covered 8 min on low — ilish is very fatty and cooks fast")),

  dict(name="Bhetki Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=250,prot=26,carb=8,fat=12,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~230g)",
         ingredients="Bhetki/Barramundi 150g (boneless fillets)|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tbsp|Mustard oil 10ml|Coriander powder 1 tsp|Turmeric ¼ tsp|Garam masala ¼ tsp|Salt to taste",
         steps="Marinate bhetki with turmeric and salt 10 min|Fry lightly in mustard oil 2 min per side; remove|Sauté onion golden; add ginger-garlic; cook 1 min; add tomato and spices; cook 4 min|Add fish; simmer gently 8 min")),

  # Basa preparations
  dict(name="Grilled Basa Fillet",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=15,cal=180,prot=24,carb=2,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~150g) — high protein, low fat",
         ingredients="Basa fillet 150g|Lemon juice 1.5 tbsp|Garlic 2 cloves (minced)|Mixed herbs 1 tsp|Olive oil 8ml|Salt and pepper",
         steps="Marinate basa with lemon, garlic, herbs, oil, salt — 15 min|Heat grill pan on medium-high|Cook 3-4 min per side; basa is done when it turns white and flakes|Do not overcook — basa cooks fast and becomes dry")),

  dict(name="Steamed Basa Fillet",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=12,cal=155,prot=24,carb=1,fat=5,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~150g) — lowest calorie fish preparation",
         ingredients="Basa fillet 150g|Ginger slices 4|Spring onion 2 stalks|Soy sauce 1 tsp|Sesame oil 3ml|Salt to taste",
         steps="Place basa on steaming plate; top with ginger and spring onion|Steam over medium-high heat 8-10 min|Drizzle soy sauce and sesame oil; serve immediately")),

  dict(name="Pan-Seared Basa in Lemon Herb Sauce",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=15,cal=220,prot=24,carb=4,fat=11,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~150g) with sauce",
         ingredients="Basa fillet 150g|Butter 10g|Garlic 2 cloves|Lemon juice 1.5 tbsp|Parsley 2 tbsp|Capers 1 tsp|White wine 20ml (optional)|Salt and pepper",
         steps="Season basa; sear in non-stick pan 3-4 min per side; remove|In same pan add butter, garlic; cook 30 sec|Add wine; reduce 1 min; add lemon, capers, parsley|Pour sauce over fish")),

  # Tilapia preparations
  dict(name="Grilled Tilapia Fillet",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=15,cal=190,prot=26,carb=2,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~160g) — very lean, high protein",
         ingredients="Tilapia fillet 160g|Lemon juice 1 tbsp|Garlic powder ½ tsp|Paprika ½ tsp|Cumin ¼ tsp|Olive oil 8ml|Salt and pepper",
         steps="Mix spices with oil; coat tilapia; rest 15 min|Grill on medium-high 4-5 min per side|Tilapia is done when it turns opaque — do not overcook")),

  dict(name="Baked Tilapia",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Easy",cook_time=20,cal=195,prot=26,carb=3,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 fillet (~160g) — good for meal prep",
         ingredients="Tilapia fillet 160g|Cherry tomatoes 40g|Zucchini 40g|Olive oil 8ml|Italian herbs 1 tsp|Garlic 2 cloves|Lemon 1 (sliced)|Salt and pepper",
         steps="Place tilapia in baking dish; surround with vegetables and lemon slices|Drizzle olive oil; season; add herbs|Bake 200°C for 18-20 min until fish flakes easily")),

  dict(name="Tilapia Curry",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=25,cal=240,prot=26,carb=8,fat=11,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Tilapia fillet 160g (cut into pieces)|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tbsp|Coriander powder 1 tsp|Cumin ½ tsp|Turmeric ¼ tsp|Red chilli ½ tsp|Oil 10ml|Salt to taste|Coriander 2 tbsp",
         steps="Marinate tilapia with turmeric, salt 10 min|Sauté onion golden; add ginger-garlic; cook 1 min|Add tomato and spices; cook 4 min; add 100ml water; simmer 3 min|Gently add tilapia; cook 8-10 min")),

  # Seafood misc
  dict(name="Paella",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=480,prot=24,carb=58,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="mediterranean",
       detail=dict(serving="1 portion (~350g)",
         ingredients="Paella/short grain rice 100g|Prawns 80g|Mussels 60g|Chicken 60g (cubed)|Capsicum 60g|Tomato 80g|Onion 60g|Garlic 4 cloves|Saffron in stock 400ml|Smoked paprika 1 tsp|Olive oil 15ml|Lemon|Salt and pepper",
         steps="Heat olive oil in wide flat pan; sauté onion, garlic, capsicum 3 min|Add chicken; brown 3 min; add tomato and paprika; cook 3 min|Add rice; stir 1 min; add hot saffron stock (do NOT stir again after this)|Arrange seafood on top; cook 18-20 min until stock absorbed|Allow socarrat (crust) to form; rest 5 min")),

  dict(name="Seafood Thukpa",meal_type="Lunch; Dinner",food_type="non-veg",food_group="fish",
       difficulty="Medium",cook_time=30,cal=310,prot=18,carb=36,fat=10,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 large bowl (~350ml)",
         ingredients="Noodles 60g (dried)|Prawns 50g|Fish 50g (cubed)|Squid 30g (optional)|Onion 40g|Ginger 1 tsp|Garlic 3 cloves|Carrot 30g|Cabbage 40g|Soy sauce 1 tbsp|Fish stock or water 500ml|Oil 8ml|Spring onion 2 tbsp|Lemon juice 1 tsp",
         steps="Heat oil; sauté ginger, garlic, onion 2 min|Add vegetables; cook 2 min|Add stock; bring to boil; add noodles; cook 5 min|Add all seafood; cook 4-5 min only|Season with soy and lemon; garnish spring onion")),
]

# ── EGG DISHES ───────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Scrambled Eggs",meal_type="Breakfast; Snack",food_type="egg",food_group="egg",
       difficulty="Easy",cook_time=8,cal=195,prot=14,carb=2,fat=14,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="2 eggs scrambled (~120g)",
         ingredients="Eggs 2|Butter 8g|Milk 20ml|Salt and pepper|Chives or coriander 1 tbsp",
         steps="Beat eggs with milk, salt, pepper until fully mixed|Melt butter in pan on LOW heat — low is the secret|Add eggs; stir gently and continuously with spatula|Remove from heat when STILL slightly wet — residual heat finishes cooking|Garnish herbs; serve immediately")),

  dict(name="Omelette",meal_type="Breakfast; Snack",food_type="egg",food_group="egg",
       difficulty="Easy",cook_time=5,cal=175,prot=14,carb=1,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="continental",
       detail=dict(serving="2-egg plain omelette (~120g)",
         ingredients="Eggs 2|Butter 8g|Salt and pepper",
         steps="Beat eggs with salt and pepper|Heat butter in pan on medium; pour eggs|Let set 30 sec; lift edges to let uncooked egg flow under|When top is just set (still glossy), fold in half; slide onto plate")),

  dict(name="Egg Bhurji",meal_type="Breakfast; Lunch; Dinner",food_type="egg",food_group="egg",
       difficulty="Easy",cook_time=10,cal=215,prot=14,carb=6,fat=14,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 serving (~160g) — Indian scrambled egg",
         ingredients="Eggs 2|Onion 40g (finely chopped)|Tomato 30g|Green chilli 1|Ginger ½ tsp|Cumin seeds ½ tsp|Turmeric a pinch|Oil 8ml|Salt to taste|Coriander 2 tbsp",
         steps="Heat oil; add cumin; add onion; cook 2 min|Add ginger, green chilli; cook 30 sec; add tomato; cook 2 min|Crack eggs directly into pan; scramble with vegetables|Cook until eggs just set — do not dry out; finish coriander")),

  dict(name="Egg Keema",meal_type="Lunch; Dinner",food_type="egg",food_group="egg",
       difficulty="Easy",cook_time=15,cal=235,prot=16,carb=8,fat=15,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Eggs 3 (hard boiled, chopped or crumbled)|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tsp|Cumin seeds 1 tsp|Garam masala ¼ tsp|Oil 8ml|Salt to taste|Peas 30g (optional)|Coriander 2 tbsp",
         steps="Heat oil; add cumin; add onion; cook golden|Add ginger-garlic; cook 1 min; add tomato and spices; cook 3 min|Add peas; cook 2 min; add crumbled hard-boiled eggs; mix gently|Cook 3 min; garnish coriander")),

  dict(name="Egg Frankie",meal_type="Breakfast; Lunch; Snack",food_type="egg",food_group="kabab",
       difficulty="Medium",cook_time=20,cal=310,prot=14,carb=36,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 frankie/roll (~200g)",
         ingredients="Whole wheat roti 1 (large)|Eggs 2|Onion 40g (sliced)|Capsicum 30g|Frankie masala 1 tsp|Oil 8ml|Mint chutney 1 tbsp|Lemon juice 1 tsp|Salt to taste",
         steps="Make thin large roti; coat with beaten egg; cook egg side until set; flip briefly|Remove and place on plate egg side up|Spread mint chutney; place sautéed onion and capsicum|Sprinkle frankie masala and lemon juice|Roll tightly; wrap lower half in foil")),

  dict(name="Egg Kofta",meal_type="Snack; Lunch; Dinner",food_type="egg",food_group="egg",
       difficulty="Medium",cook_time=30,cal=265,prot=15,carb=14,fat=16,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="4 koftas (~200g) in gravy",
         ingredients="Eggs 3 (hard boiled, halved)|Potato 80g (boiled, mashed)|Onion 30g (grated)|Green chilli 1|Garam masala ¼ tsp|Oil for frying + 10ml for gravy|Tomato 80g|Ginger-garlic paste 1 tbsp|Cream 20ml|Salt to taste",
         steps="Coat hard-boiled egg halves with spiced mashed potato shell; seal tightly|Deep fry until golden; set aside|Make gravy: sauté onion golden; add ginger-garlic; add tomato and spices; cook 5 min; add cream|Gently add koftas to gravy; simmer 3 min")),

  dict(name="Egg Korma",meal_type="Lunch; Dinner",food_type="egg",food_group="egg",
       difficulty="Medium",cook_time=30,cal=280,prot=14,carb=10,fat=20,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Eggs 3 (hard boiled, scored)|Onion 80g (fried, blended)|Cashew 15g (soaked, blended)|Yogurt 50ml|Cream 20ml|Ginger-garlic paste 1 tbsp|Whole spices|Ghee 12ml|Garam masala ¼ tsp|Salt to taste",
         steps="Score hard-boiled eggs all over|Heat ghee; add whole spices; add blended onion-cashew paste; cook 5 min|Add yogurt gradually, stirring; add ginger-garlic; cook 3 min|Add eggs; spoon gravy over; simmer 8 min; stir in cream")),

  dict(name="Egg Patty",meal_type="Breakfast; Snack",food_type="egg",food_group="egg",
       difficulty="Easy",cook_time=10,cal=155,prot=12,carb=2,fat=11,
       p_min=0.5,p_typ=1,p_max=2,role="anchor_protein",cuisine="continental",
       detail=dict(serving="1 patty (~80g) — like a McDonald's egg muffin patty",
         ingredients="Egg 1|Salt and pepper|Oil 5ml or butter 5g|Round mold (optional)",
         steps="Heat oil in small pan; crack egg into mold or directly into pan|Cook on low-medium 3 min until white is set; yolk can be runny or fully cooked|Season; use in sandwich or eat standalone")),

  dict(name="Egg Cutlet",meal_type="Snack; Breakfast",food_type="egg",food_group="egg",
       difficulty="Medium",cook_time=25,cal=220,prot=12,carb=18,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="2 cutlets (~140g)",
         ingredients="Eggs 2 (hard boiled, chopped)|Potato 100g (boiled, mashed)|Onion 30g (chopped)|Green chilli 1|Garam masala ¼ tsp|Breadcrumbs 30g|Oil 8ml|Salt to taste",
         steps="Mix chopped egg with potato, onion, chilli, garam masala, salt|Shape into oval patties; coat in breadcrumbs|Shallow fry in oil 3-4 min per side until golden")),

  dict(name="Egg Toast",meal_type="Breakfast; Snack",food_type="egg",food_group="toast",
       difficulty="Easy",cook_time=8,cal=255,prot=14,carb=22,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="continental",
       detail=dict(serving="2 slices egg toast (~160g)",
         ingredients="Bread 2 slices|Eggs 2|Butter 8g|Salt and pepper|Optional: cheese slice or herbs",
         steps="Scramble or fry eggs to preference|Toast bread; butter it|Top with eggs; season; serve hot")),

  dict(name="Egg Sandwich",meal_type="Breakfast; Lunch; Snack",food_type="egg",food_group="toast",
       difficulty="Easy",cook_time=10,cal=295,prot=16,carb=28,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 sandwich (2 slices, ~180g)",
         ingredients="Bread 2 slices|Eggs 2 (scrambled or fried)|Lettuce leaf 1|Tomato 1 slice|Cheese slice 1 (optional)|Mayo/mustard 1 tsp|Salt and pepper",
         steps="Cook eggs to preference|Toast bread; spread condiments|Layer lettuce, tomato, eggs, cheese; press together")),

  dict(name="Egg Spring Roll",meal_type="Snack; Lunch",food_type="egg",food_group="kabab",
       difficulty="Medium",cook_time=25,cal=235,prot=11,carb=22,fat=12,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="indo_chinese",
       detail=dict(serving="2 spring rolls (~160g)",
         ingredients="Spring roll wrappers 2|Eggs 2 (beaten)|Cabbage 60g (shredded)|Carrot 30g (julienned)|Spring onion 3 stalks|Soy sauce 1 tsp|Ginger ½ tsp|Oil for frying + 5ml",
         steps="Stir-fry vegetables with ginger, soy 2 min; cool|Mix in beaten eggs|Place filling in wrapper; fold sides; roll tightly; seal with water-flour paste|Deep fry at 180°C for 3-4 min until golden and crispy")),

  dict(name="Egg Vada",meal_type="Snack; Breakfast",food_type="egg",food_group="south_indian",
       difficulty="Medium",cook_time=20,cal=245,prot=13,carb=18,fat=14,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="south_indian",
       detail=dict(serving="2 vadas (~150g)",
         ingredients="Urad dal 80g (soaked 2 hr)|Egg 1|Onion 30g (finely chopped)|Green chilli 1|Curry leaves 4|Ginger ½ tsp|Oil for frying|Salt to taste",
         steps="Grind soaked urad dal to smooth fluffy batter; beat in egg|Add onion, chilli, curry leaves, ginger, salt|Heat oil to 180°C; wet hands; shape into rings; slide into oil|Fry 4-5 min until golden and cooked through; drain")),
]

# ── PANEER ────────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Paneer Korma",meal_type="Lunch; Dinner",food_type="veg",food_group="paneer",
       difficulty="Hard",cook_time=40,cal=370,prot=16,carb=12,fat=28,
       p_min=0.5,p_typ=0.75,p_max=1,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Paneer 100g (cubed)|Onion 80g (fried, blended)|Cashew 20g (soaked, blended)|Yogurt 50ml|Cream 30ml|Ginger-garlic paste 1 tbsp|Whole spices|Ghee 12ml|Garam masala ¼ tsp|Rose water 1 tsp|Saffron in milk|Salt to taste",
         steps="Heat ghee; add whole spices; add blended onion-cashew paste; cook 5 min|Add yogurt gradually; add ginger-garlic; cook 3 min|Add saffron milk; simmer 3 min; stir in cream|Add paneer; cook gently 5 min; finish with rose water")),

  dict(name="Paneer Pasanda",meal_type="Lunch; Dinner",food_type="veg",food_group="paneer",
       difficulty="Hard",cook_time=40,cal=355,prot=15,carb=12,fat=26,
       p_min=0.5,p_typ=0.75,p_max=1,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Paneer 120g (sliced, stuffed with filling: cashew, raisin, green chilli 30g)|Onion 80g (fried, blended)|Tomato 60g|Cream 30ml|Yogurt 50ml|Ginger-garlic paste 1 tbsp|Ghee 12ml|Garam masala ½ tsp|Cardamom powder ¼ tsp|Salt to taste",
         steps="Make filling: mix chopped cashew, raisin, green chilli, salt|Sandwich filling between paneer slices; coat in batter if desired; shallow fry|Make gravy: blend fried onion; cook with tomato and spices; add cream|Place fried paneer in gravy; simmer 5 min")),

  dict(name="Navratan Korma",meal_type="Lunch; Dinner",food_type="veg",food_group="paneer",
       difficulty="Hard",cook_time=45,cal=340,prot=10,carb=28,fat=22,
       p_min=0.5,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~300g) — 9 ingredients curry",
         ingredients="Paneer 60g|Mixed vegetables 100g (carrot, peas, cauliflower, beans)|Cashew 20g|Raisins 10g|Pineapple 20g|Onion 80g (fried, blended)|Cream 40ml|Yogurt 50ml|Ghee 12ml|Garam masala ¼ tsp|Rose water 1 tsp|Salt to taste",
         steps="This curry must have 9 main ingredients — hence navratan|Make korma base: blended fried onion + yogurt + cream|Cook vegetables 80% done separately; add to gravy|Add paneer, cashew, raisins, pineapple; simmer 5 min|Finish with rose water")),

  dict(name="Paneer Manchurian",meal_type="Lunch; Dinner; Snack",food_type="veg",food_group="paneer",
       difficulty="Medium",cook_time=25,cal=310,prot=14,carb=22,fat=18,
       p_min=0.5,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="indo_chinese",
       detail=dict(serving="1 serving (~250g)",
         ingredients="Paneer 120g (cubed)|Cornstarch 20g|Egg 1 (or 2 tbsp water for vegan)|Ginger 1 tsp|Garlic 4 cloves|Spring onion 3 stalks|Soy sauce 2 tbsp|Chilli sauce 1 tbsp|Oil for frying + 10ml|Salt to taste",
         steps="Coat paneer in cornstarch, egg, salt; deep fry until golden|Heat oil; fry ginger and garlic 30 sec; add sauces; simmer 2 min|Add fried paneer; toss; garnish spring onion")),
]

# ── SOYA / PLANT PROTEIN ──────────────────────────────────────────────────────
RECIPES += [
  dict(name="Veg Soya Keema",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Easy",cook_time=25,cal=265,prot=22,carb=18,fat=10,
       p_min=0.5,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Soya granules 60g (soaked in hot water, squeezed dry)|Peas 40g|Onion 60g|Tomato 60g|Ginger-garlic paste 1 tsp|Garam masala ¼ tsp|Cumin seeds 1 tsp|Oil 8ml|Salt to taste|Coriander 2 tbsp",
         steps="Soak soya granules in hot water 10 min; squeeze out water — this removes beany taste|Sauté onion golden; add ginger-garlic; cook 1 min|Add tomato and spices; cook 3 min|Add soya and peas; cook covered 8 min|Garnish coriander")),

  dict(name="Soya Masala",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Medium",cook_time=30,cal=275,prot=22,carb=20,fat=12,
       p_min=0.5,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="north_indian",
       detail=dict(serving="1 bowl (~220g)",
         ingredients="Soya chunks 60g (boiled 10 min, squeezed)|Onion 80g|Tomato 80g|Ginger-garlic paste 1.5 tbsp|Coriander powder 1 tsp|Garam masala ½ tsp|Red chilli ½ tsp|Oil 10ml|Salt to taste",
         steps="Boil soya chunks 10 min; drain; squeeze well|Sauté onion deep golden; add ginger-garlic; cook 2 min|Add tomato and spices; cook 5 min until oil separates|Add soya chunks and 100ml water; simmer 10 min")),

  dict(name="Soya Kabab",meal_type="Snack; Lunch",food_type="vegan",food_group="kabab",
       difficulty="Medium",cook_time=25,cal=225,prot=18,carb=20,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 kababs (~150g)",
         ingredients="Soya granules 60g (soaked, squeezed)|Potato 80g (boiled, mashed)|Onion 30g|Green chilli 1|Coriander 2 tbsp|Garam masala ½ tsp|Besan 15g|Oil 8ml|Salt to taste",
         steps="Mix soaked squeezed soya with potato, onion, chilli, coriander, besan, spices|Shape into flat patties|Shallow fry in oil 3-4 min per side until crispy")),

  dict(name="Grilled Tofu",meal_type="Snack; Lunch; Dinner",food_type="vegan",food_group="paneer",
       difficulty="Easy",cook_time=15,cal=175,prot=14,carb=4,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 serving (~150g firm tofu)",
         ingredients="Firm tofu 150g (pressed dry)|Soy sauce 2 tbsp|Sesame oil 5ml|Garlic 2 cloves|Ginger ½ tsp|Rice vinegar 1 tsp|Sesame seeds 1 tsp",
         steps="Press tofu under heavy weight 30 min to remove water — critical step; wet tofu won't grill|Cut into 1cm slices; marinate in soy, sesame oil, garlic, ginger 30 min|Heat grill pan on high; cook 3-4 min per side until char marks appear|Sprinkle sesame seeds")),

  dict(name="Roasted Edamame",meal_type="Snack",food_type="vegan",food_group="chaat",
       difficulty="Easy",cook_time=15,cal=160,prot=12,carb=12,fat=6,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="east_asian",
       detail=dict(serving="1 bowl (~120g shelled edamame)",
         ingredients="Frozen edamame (in pod or shelled) 150g|Salt 1 tsp|Olive oil 5ml|Chilli flakes ¼ tsp (optional)|Garlic powder ¼ tsp (optional)",
         steps="Thaw or steam edamame 5 min|Toss with oil and seasoning|Roast at 200°C for 10-12 min until slightly crispy|If in pod: squeeze beans out to eat; discard pod")),
]

# ── SNACKS / STREET FOOD ──────────────────────────────────────────────────────
RECIPES += [
  dict(name="Dahi Puri",meal_type="Snack",food_type="veg",food_group="chaat",
       difficulty="Medium",cook_time=20,cal=195,prot=6,carb=28,fat=7,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="6 puris (~180g assembled)",
         ingredients="Puri shells 6 (small, hollow, store-bought or homemade)|Potato 80g (boiled, mashed)|Chickpeas 40g (boiled)|Yogurt 80ml (whisked, chilled)|Tamarind chutney 2 tbsp|Green chutney 1 tbsp|Chaat masala ½ tsp|Cumin powder ¼ tsp|Coriander 2 tbsp|Sev 20g",
         steps="Fill each puri with potato and chickpea|Pour yogurt into puri|Drizzle tamarind and green chutney|Sprinkle chaat masala, cumin, coriander|Top with sev; serve immediately — soggy in 2 min")),

  dict(name="Mysore Bonda",meal_type="Snack; Breakfast",food_type="vegan",food_group="south_indian",
       difficulty="Medium",cook_time=25,cal=225,prot=6,carb=32,fat=9,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="south_indian",
       detail=dict(serving="4 bondas (~160g)",
         ingredients="Maida 80g|Yogurt 40ml|Baking soda ¼ tsp|Ginger ½ tsp|Green chilli 1|Curry leaves 6|Coconut 20g (grated)|Oil for frying|Salt to taste",
         steps="Mix maida with yogurt, baking soda, ginger, chilli, curry leaves, coconut, salt|Rest 30 min|Heat oil to 180°C; drop spoonful of batter; fry 4-5 min until golden and crispy|Serve with coconut chutney")),

  dict(name="Misal Pav",meal_type="Breakfast; Lunch",food_type="vegan",food_group="chaat",
       difficulty="Medium",cook_time=35,cal=380,prot=14,carb=56,fat=10,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="1 serving with 2 pav (~280g)",
         ingredients="Sprouted matki/moth beans 80g|Pav 2|Kolhapuri masala 2 tsp|Onion 60g|Tomato 60g|Oil 10ml|Farsan/chiwda 20g (crunchy topping)|Lemon juice 1 tsp|Coriander 2 tbsp|Salt to taste",
         steps="Cook matki with masala: sauté onion; add tomato; add kolhapuri masala; add sprouted matki and water; simmer 15 min — should be spicy gravy (kat)|Toast pav with butter|Serve kat in bowl; top with crunchy farsan, onion, lemon, coriander; eat with pav")),

  dict(name="Sabudana Vada",meal_type="Breakfast; Snack",food_type="veg",food_group="chaat",
       difficulty="Medium",cook_time=25,cal=265,prot=5,carb=38,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 vadas (~160g)",
         ingredients="Sabudana 100g (soaked 4 hr, drained)|Potato 80g (boiled, mashed)|Peanuts 30g (roasted, coarsely ground)|Green chilli 2|Cumin seeds 1 tsp|Lemon juice 1 tsp|Oil for frying|Salt to taste|Coriander 2 tbsp",
         steps="Mix soaked sabudana with potato, peanuts, chilli, cumin, lemon, coriander, salt|Shape into round patties (if mixture sticks, refrigerate 30 min)|Shallow fry in oil on medium 3-4 min per side until golden and crispy")),

  dict(name="Khaman Dhokla",meal_type="Breakfast; Snack",food_type="vegan",food_group="chaat",
       difficulty="Medium",cook_time=30,cal=220,prot=9,carb=34,fat=6,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="north_indian",
       detail=dict(serving="6 pieces (~180g)",
         ingredients="Besan 80g|Yogurt 40ml|Water 60ml|Eno (fruit salt) 1 tsp|Turmeric ¼ tsp|Green chilli 1|Ginger ½ tsp|Lemon juice 1 tsp|Sugar 1 tsp|For tadka: mustard seeds, curry leaves, green chilli, oil 8ml, sugar syrup 2 tbsp|Salt to taste",
         steps="Mix besan with yogurt, water, turmeric, chilli, ginger, lemon, salt and sugar — thick batter|Add eno just before steaming; fold gently and immediately pour into greased plate|Steam 15 min; test with toothpick|Cut into pieces; apply hot tadka|Apply sugar syrup diluted with water for moisture")),

  dict(name="Methi Muthia",meal_type="Snack; Breakfast",food_type="vegan",food_group="chaat",
       difficulty="Medium",cook_time=30,cal=185,prot=7,carb=26,fat=6,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4-5 pieces (~150g)",
         ingredients="Fresh methi leaves 80g|Besan 50g|Whole wheat flour 30g|Oil 10ml|Sesame seeds 1 tsp|Ginger ½ tsp|Green chilli 1|Turmeric ¼ tsp|Salt to taste|Sugar ½ tsp",
         steps="Mix all ingredients to firm dough; add water only if needed|Shape into cylinders; steam 15 min|Cool; slice; shallow fry in oil until golden|Alternatively: bake 180°C for 20 min")),

  dict(name="Samosa",meal_type="Snack",food_type="vegan",food_group="chaat",
       difficulty="Hard",cook_time=60,cal=265,prot=5,carb=30,fat=14,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="north_indian",
       detail=dict(serving="2 samosas (~140g)",
         ingredients="Maida 100g|Oil 15ml (for pastry)|Potato 200g (boiled, mashed)|Peas 40g|Ginger 1 tsp|Green chilli 1|Cumin seeds 1 tsp|Coriander seeds ½ tsp|Amchur ½ tsp|Oil for frying|Salt to taste",
         steps="Rub oil into maida; add water; knead stiff dough; rest 20 min|Make filling: cook peas with spices; mix with potato|Shape cones from rolled dough; fill; seal tightly|Deep fry on MEDIUM heat 12-15 min — low heat makes crispy samosa; high heat makes it soft")),

  dict(name="Kachori",meal_type="Snack",food_type="vegan",food_group="chaat",
       difficulty="Hard",cook_time=45,cal=295,prot=7,carb=34,fat=14,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="north_indian",
       detail=dict(serving="2 kachoris (~140g)",
         ingredients="Maida 100g|Oil 15ml (for pastry)|Moong dal or urad dal 60g (filling)|Fennel seeds 1 tsp|Coriander seeds ½ tsp|Red chilli ½ tsp|Asafoetida a pinch|Oil for frying|Salt to taste",
         steps="Make stiff pastry dough; rest 20 min|Soak and grind dal coarsely; dry roast with spices until fragrant|Fill round discs of dough with filling; seal into balls|Deep fry on LOW heat 15-18 min until evenly golden and crispy")),

  dict(name="Black Channa Kebab",meal_type="Snack; Lunch",food_type="vegan",food_group="kabab",
       difficulty="Medium",cook_time=30,cal=240,prot=10,carb=30,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 kebabs (~150g)",
         ingredients="Black chickpeas 80g (soaked, boiled)|Potato 60g (boiled)|Onion 30g|Green chilli 1|Garam masala ½ tsp|Amchur ½ tsp|Coriander 2 tbsp|Besan 15g|Oil 8ml|Salt to taste",
         steps="Drain and mash black chana — keep some texture|Mix with potato, onion, chilli, spices, coriander and besan|Shape into flat patties|Shallow fry in oil 3-4 min per side until crispy")),

  dict(name="Hara Bhara Kabab",meal_type="Snack; Lunch",food_type="veg",food_group="kabab",
       difficulty="Medium",cook_time=25,cal=215,prot=8,carb=26,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="4 kababs (~150g)",
         ingredients="Spinach 100g (blanched, squeezed dry, chopped)|Potato 80g (boiled, mashed)|Peas 40g (boiled, coarsely mashed)|Paneer 30g (grated)|Green chilli 1|Ginger ½ tsp|Garam masala ¼ tsp|Besan or breadcrumbs 15g|Oil 8ml|Salt to taste",
         steps="Mix all ingredients; ensure spinach is very dry — moisture causes disintegration|Shape into round flat patties|Shallow fry in oil 3 min per side until crispy outside, green inside")),

  dict(name="Roasted Sweet Potato",meal_type="Snack; Breakfast",food_type="vegan",food_group="chaat",
       difficulty="Easy",cook_time=35,cal=185,prot=3,carb=40,fat=3,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="continental",
       detail=dict(serving="1 medium sweet potato (~200g)",
         ingredients="Sweet potato 200g|Olive oil 8ml|Salt|Cinnamon ¼ tsp (optional)|Black pepper ¼ tsp",
         steps="Wash sweet potato; cut into wedges or cubes|Toss with oil, salt, pepper, cinnamon|Roast 200°C for 25-30 min until caramelised and tender|High natural sugar content — watch for burning")),

  dict(name="Air Fried Potato Wedges",meal_type="Snack; Lunch",food_type="vegan",food_group="chaat",
       difficulty="Easy",cook_time=25,cal=190,prot=4,carb=36,fat=4,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="continental",
       detail=dict(serving="1 serving (~200g)",
         ingredients="Potato 250g (cut into wedges)|Oil 8ml|Garlic powder ½ tsp|Paprika ½ tsp|Mixed herbs ½ tsp|Salt to taste",
         steps="Soak wedges in cold water 20 min; pat very dry — this is key for crispiness|Toss with oil and all spices|Air fry at 200°C for 18-22 min, shaking basket halfway|OR bake at 220°C for 25-30 min on a wire rack")),

  dict(name="French Fries",meal_type="Snack",food_type="vegan",food_group="chaat",
       difficulty="Medium",cook_time=30,cal=280,prot=4,carb=38,fat=13,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="continental",
       detail=dict(serving="1 portion (~150g)",
         ingredients="Potato 200g (peeled, cut into strips)|Oil for frying|Salt to taste",
         steps="Soak potato strips in cold water 30 min; pat completely dry|DOUBLE FRY method: first fry at 150°C for 5 min (blanch); drain; cool completely|Second fry at 190°C for 3-4 min until golden and crispy|Season immediately with salt")),

  # Dim Sum trio
  dict(name="Har Gow (Steamed Prawn Dumplings)",meal_type="Snack; Lunch",food_type="non-veg",food_group="fish",
       difficulty="Hard",cook_time=45,cal=175,prot=10,carb=22,fat=5,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
       detail=dict(serving="4 dumplings (~100g)",
         ingredients="Wheat starch dough 80g (wheat starch + tapioca starch + boiling water)|Prawns 80g (chopped)|Bamboo shoots 20g|Ginger 1 tsp|Sesame oil 3ml|Cornstarch 1 tsp|Salt and white pepper",
         steps="Mix chopped prawns with bamboo shoots, ginger, sesame oil, cornstarch|Make translucent dough with wheat starch and boiling water; knead well|Roll into thin circles; pleat into crescent shapes — 7 pleats is traditional|Steam on greased paper 7-8 min until translucent and cooked")),

  dict(name="Siu Mai (Pork & Prawn Dumplings)",meal_type="Snack; Lunch",food_type="non-veg",food_group="fish",
       difficulty="Hard",cook_time=30,cal=190,prot=12,carb=16,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
       detail=dict(serving="4 dumplings (~100g)",
         ingredients="Wonton wrappers 4|Pork mince 60g|Prawns 40g (chopped)|Shiitake mushroom 20g|Ginger 1 tsp|Soy sauce 1 tsp|Sesame oil 3ml|Cornstarch 1 tsp|Crab roe or carrot for garnish",
         steps="Mix pork, prawns, mushroom, ginger, soy, sesame oil, cornstarch|Cup wrapper in palm; fill generously; gather sides leaving top open|Steam 8-10 min; garnish with carrot dot or crab roe on top")),

  dict(name="Char Siu Bao (Steamed BBQ Pork Bun)",meal_type="Snack; Breakfast",food_type="non-veg",food_group="grain_breakfast",
       difficulty="Hard",cook_time=60,cal=235,prot=8,carb=32,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
       detail=dict(serving="2 buns (~120g)",
         ingredients="Soft white dough (flour, yeast, sugar, baking powder, milk) 100g|Char siu pork filling 60g (BBQ pork, oyster sauce, soy sauce, hoisin)|",
         steps="Make soft yeast dough; rest 1 hr until doubled|Punch down; divide into portions|Flatten each; fill with char siu filling; gather and pleat to seal|Rest 15 min|Steam on parchment paper 12-15 min until fluffy and white")),

  dict(name="Gyoza",meal_type="Snack; Lunch",food_type="non-veg",food_group="fish",
       difficulty="Hard",cook_time=30,cal=195,prot=9,carb=22,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
       detail=dict(serving="6 dumplings (~120g)",
         ingredients="Gyoza wrappers 6|Pork mince 60g|Cabbage 40g (finely chopped, salted, squeezed)|Ginger 1 tsp|Garlic 2 cloves|Soy sauce 1 tsp|Sesame oil 3ml|Spring onion 2 stalks|Oil 8ml|Water 60ml",
         steps="Mix pork with cabbage (must be squeezed VERY dry), ginger, garlic, soy, sesame oil|Pleat wrappers into crescent shapes — 5-6 pleats per dumpling|Heat oil in flat pan; place gyoza flat side down; fry 2 min until golden|Add water; cover; steam 4 min; uncover to evaporate water|Serve golden side up with dipping sauce")),

  dict(name="Yakitori",meal_type="Snack; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=20,cal=210,prot=24,carb=10,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="4 skewers (~160g)",
         ingredients="Chicken thigh 150g (boneless, cut into pieces)|Tare sauce: soy sauce 3 tbsp, mirin 2 tbsp, sake 1 tbsp, sugar 1 tsp (simmer together 5 min to thicken)|Spring onion 3 stalks|Oil 5ml|Shichimi togarashi to serve",
         steps="Thread alternating chicken and spring onion on skewers|Grill over charcoal or under high broiler, turning frequently|Baste generously with tare sauce in final 2-3 min of cooking|Should have slight char and caramelisation")),
]

# ── MOMOS ─────────────────────────────────────────────────────────────────────
def _momo(name, food_type, cal, prot, carb, fat, ww=False):
    flour = "Whole wheat flour" if ww else "Maida/plain flour"
    return dict(name=name,meal_type="Snack; Lunch",food_type=food_type,food_group="kabab",
        difficulty="Medium",cook_time=30,cal=cal,prot=prot,carb=carb,fat=fat,
        p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
        detail=dict(serving="6 momos (~180g)",
          ingredients=f"{flour} 80g|Filling 100g|Ginger 1 tsp|Garlic 2 cloves|Soy sauce 1 tsp|Sesame oil 3ml|Spring onion 2 stalks|Salt to taste",
          steps="Mix flour with water to firm dough; rest 15 min|Prepare filling; season with ginger, garlic, soy, sesame oil, spring onion|Roll dough into thin rounds; fill; pleat into crescent or circle shapes|Steam 12-15 min on greased steamer|Serve with chilli-garlic dipping sauce"))

RECIPES += [
  _momo("Chicken Momos","non-veg",200,14,20,7),
  _momo("Whole Wheat Chicken Momos","non-veg",195,14,20,7,ww=True),
  _momo("Veg Momos","vegan",165,5,26,4),
  _momo("Whole Wheat Veg Momos","vegan",160,5,26,4,ww=True),
  _momo("Paneer Momos","veg",205,9,22,9),
  _momo("Whole Wheat Paneer Momos","veg",200,9,22,9,ww=True),
  _momo("Soya Momos","vegan",185,12,22,5),
  _momo("Whole Wheat Soya Momos","vegan",180,12,22,5,ww=True),
  dict(name="Mutton Momos",meal_type="Snack; Lunch",food_type="non-veg",food_group="kabab",
       difficulty="Medium",cook_time=35,cal=215,prot=16,carb=20,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="east_asian",
       detail=dict(serving="6 momos (~180g)",
         ingredients="Maida 80g|Mutton mince 100g|Onion 40g|Ginger 1 tsp|Garlic 2 cloves|Soy sauce 1 tsp|Sesame oil 3ml|Spring onion 2 stalks|Salt and pepper",
         steps="Make dough; rest 15 min|Mix mutton with onion, ginger, garlic, soy, sesame oil, spring onion|Pleat into shapes; steam 15-18 min (mutton needs longer than chicken)")),
]

# ── SOUPS ─────────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Pumpkin Soup",meal_type="Snack; Dinner",food_type="veg",food_group="soup",
       difficulty="Easy",cook_time=30,cal=135,prot=3,carb=18,fat=6,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (250ml)",
         ingredients="Pumpkin 250g (cubed)|Onion 40g|Garlic 2 cloves|Vegetable stock 300ml|Fresh cream 20ml|Butter 8g|Nutmeg a pinch|Salt and white pepper",
         steps="Sauté onion and garlic in butter 3 min|Add pumpkin; cook 3 min; add stock; simmer 15 min until soft|Blend completely smooth; strain if desired|Return to pot; add cream and nutmeg; simmer 3 min")),

  dict(name="Wonton Soup",meal_type="Snack; Lunch",food_type="non-veg",food_group="soup",
       difficulty="Hard",cook_time=40,cal=210,prot=12,carb=22,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 bowl with 4 wontons (300ml)",
         ingredients="Wonton wrappers 4|Pork mince 60g|Prawns 30g|Ginger 1 tsp|Soy sauce 1 tsp|Sesame oil 3ml|Chicken stock 400ml|Spring onion 2 tbsp|Bok choy 40g|White pepper|Sesame oil for finishing",
         steps="Make wonton filling: mix pork, prawn, ginger, soy, sesame oil|Fill and fold wontons into triangles or nurse cap shapes|Bring stock to boil; add wontons; cook 5 min|Add bok choy; cook 1 min|Bowl up with spring onion and white pepper")),

  dict(name="Cream of Mushroom Soup",meal_type="Snack; Dinner",food_type="veg",food_group="soup",
       difficulty="Easy",cook_time=25,cal=175,prot=4,carb=12,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (250ml)",
         ingredients="Mushrooms 150g (sliced)|Onion 40g|Garlic 2 cloves|Butter 12g|Flour 10g|Milk 150ml|Stock 150ml|Cream 30ml|Thyme ½ tsp|Salt and pepper|Parsley 1 tbsp",
         steps="Sauté onion and garlic in butter 2 min; add mushrooms; cook 6 min until golden|Add flour; stir 1 min; add stock gradually, whisking|Add milk; simmer 5 min; stir in cream|Season; garnish parsley")),

  dict(name="Manchow Soup",meal_type="Snack; Dinner",food_type="non-veg",food_group="soup",
       difficulty="Easy",cook_time=20,cal=155,prot=8,carb=18,fat=5,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="indo_chinese",
       detail=dict(serving="1 bowl (300ml)",
         ingredients="Chicken stock or water 400ml|Mixed veg 80g (carrot, cabbage, capsicum, spring onion)|Chicken 40g (shredded, cooked)|Cornstarch 1 tbsp|Soy sauce 1 tbsp|Chilli sauce 1 tsp|Vinegar 1 tsp|Ginger 1 tsp|Garlic 2 cloves|Oil 5ml|Fried noodles for topping|Salt and pepper",
         steps="Sauté ginger and garlic in oil 30 sec|Add stock; bring to boil; add vegetables; cook 3 min|Add chicken, soy sauce, chilli sauce, vinegar|Thicken with cornstarch mixed in cold water; stir until clear|Serve topped with fried noodles")),

  dict(name="French Onion Soup",meal_type="Snack; Dinner",food_type="veg",food_group="soup",
       difficulty="Medium",cook_time=60,cal=225,prot=6,carb=24,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (300ml) with crouton and cheese",
         ingredients="Onion 250g (thinly sliced)|Butter 15g|White wine 60ml|Beef or veg stock 400ml|Thyme 2 sprigs|Bay leaf 1|Baguette slice 1|Gruyere or cheddar 20g (grated)|Salt and pepper",
         steps="Caramelise onion in butter on very low heat 35-40 min — patience is required; they should be deep golden brown|Add wine; reduce 2 min; add stock and herbs; simmer 15 min|Pour into oven-proof bowl; float baguette; top with cheese|Grill under broiler 3-4 min until cheese bubbling and brown")),

  dict(name="Veg Thukpa",meal_type="Lunch; Dinner",food_type="vegan",food_group="soup",
       difficulty="Easy",cook_time=25,cal=285,prot=8,carb=44,fat=7,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 large bowl (~350ml)",
         ingredients="Noodles 60g (dried)|Mixed veg 100g (carrot, cabbage, beans, capsicum)|Onion 40g|Ginger 1 tsp|Garlic 3 cloves|Soy sauce 1 tbsp|Vegetable stock or water 500ml|Oil 8ml|Lemon juice 1 tsp|Coriander 2 tbsp|Salt and pepper",
         steps="Heat oil; sauté ginger, garlic, onion 2 min|Add vegetables; cook 3 min|Add stock; bring to boil; add noodles; cook as per packet|Season with soy, salt, pepper; finish with lemon and coriander")),

  dict(name="Chicken Thukpa",meal_type="Lunch; Dinner",food_type="non-veg",food_group="soup",
       difficulty="Easy",cook_time=30,cal=325,prot=18,carb=44,fat=8,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 large bowl (~350ml)",
         ingredients="Noodles 60g|Chicken 80g (sliced thin)|Onion 40g|Ginger 1 tsp|Garlic 3 cloves|Carrot 30g|Cabbage 40g|Soy sauce 1 tbsp|Chicken stock or water 500ml|Oil 8ml|Lemon juice 1 tsp|Coriander 2 tbsp|Spring onion 2 tbsp",
         steps="Marinate chicken in soy sauce 10 min|Heat oil; sauté ginger, garlic; add chicken; cook 3 min|Add onion and vegetables; cook 2 min|Add stock; boil; add noodles; cook|Finish with lemon and herbs")),
]

# ── SALADS ────────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Cobb Salad",meal_type="Lunch",food_type="non-veg",food_group="chicken",
       difficulty="Easy",cook_time=15,cal=345,prot=28,carb=10,fat=22,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 large salad plate (~350g)",
         ingredients="Romaine lettuce 80g|Chicken breast 80g (grilled, sliced)|Bacon 30g (cooked crispy)|Egg 1 (hard boiled, sliced)|Avocado ½ (sliced)|Blue cheese 20g (crumbled)|Cherry tomatoes 6|Olive oil 10ml|Lemon juice 1 tbsp|Salt and pepper",
         steps="Arrange lettuce as base|Place rows of chicken, bacon, egg, avocado, cheese, tomatoes over lettuce|Do NOT toss — serve with dressing on side|Whisk olive oil with lemon, salt, pepper for dressing")),

  dict(name="Greek Salad",meal_type="Lunch; Snack",food_type="veg",food_group="chaat",
       difficulty="Easy",cook_time=5,cal=195,prot=7,carb=12,fat=14,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="mediterranean",
       detail=dict(serving="1 salad bowl (~300g)",
         ingredients="Cucumber 100g (chunks)|Tomato 100g (chunks)|Red onion 40g (sliced)|Olives 20g|Feta cheese 40g|Olive oil 12ml|Lemon juice 1 tbsp|Dried oregano 1 tsp|Salt and pepper",
         steps="Combine cucumber, tomato, onion, olives|Drizzle olive oil and lemon juice|Season with oregano, salt, pepper|Top with crumbled feta — do NOT mix feta in; leave it on top")),

  dict(name="Green Salad",meal_type="Lunch; Snack",food_type="vegan",food_group="veg_raw",
       difficulty="Easy",cook_time=5,cal=80,prot=3,carb=8,fat=4,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (~200g)",
         ingredients="Mixed greens 100g (lettuce, rocket, spinach)|Cucumber 40g|Capsicum 30g|Spring onion 20g|Olive oil 8ml|Lemon juice 1 tsp|Salt and pepper|Herbs as desired",
         steps="Wash and dry greens thoroughly|Combine all vegetables|Dress with olive oil, lemon, salt and pepper; toss lightly")),

  dict(name="Russian Salad",meal_type="Lunch; Snack",food_type="veg",food_group="chaat",
       difficulty="Easy",cook_time=20,cal=230,prot=6,carb=24,fat=12,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="continental",
       detail=dict(serving="1 bowl (~250g)",
         ingredients="Potato 80g (diced, boiled)|Carrot 60g (diced, boiled)|Peas 40g (boiled)|Corn 30g|Mayo or hung curd 40g|Lemon juice 1 tsp|Salt and pepper|Parsley 1 tbsp",
         steps="Cool all boiled vegetables completely before mixing|Fold in mayo gently; season|Refrigerate 30 min before serving — tastes better cold|Can add boiled egg, pickles or gherkins")),

  dict(name="Caesar Salad",meal_type="Lunch",food_type="veg",food_group="chaat",
       difficulty="Medium",cook_time=10,cal=250,prot=9,carb=16,fat=17,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 large salad (~280g)",
         ingredients="Romaine lettuce 120g (torn)|Caesar dressing 40ml (mayo, parmesan, lemon, Worcestershire, anchovy paste, garlic)|Croutons 30g|Parmesan 20g (shaved)|Black pepper",
         steps="Chill lettuce|Toss with caesar dressing; coat well|Add croutons and parmesan|Serve immediately")),

  dict(name="Caesar Salad (Chicken)",meal_type="Lunch",food_type="non-veg",food_group="chicken",
       difficulty="Medium",cook_time=20,cal=340,prot=28,carb=16,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 large salad (~350g)",
         ingredients="Romaine lettuce 120g|Chicken breast 100g (grilled, sliced)|Caesar dressing 40ml|Croutons 30g|Parmesan 20g|Black pepper",
         steps="Grill chicken; cool slightly; slice|Toss lettuce with dressing; top with chicken, croutons and parmesan")),

  dict(name="Hummus Bowl",meal_type="Breakfast; Snack; Lunch",food_type="vegan",food_group="dal",
       difficulty="Easy",cook_time=5,cal=280,prot=10,carb=26,fat=16,
       p_min=0.5,p_typ=1,p_max=1.25,role="complete_meal",cuisine="middle_eastern",
       detail=dict(serving="1 bowl (~200g hummus with toppings)",
         ingredients="Hummus 150g (chickpeas, tahini, lemon, garlic, olive oil — store-bought or homemade)|Olive oil 8ml|Paprika ¼ tsp|Cumin ¼ tsp|Cherry tomatoes 4|Cucumber 30g|Olives 15g|Pita or flatbread (extra calories if added)",
         steps="Spread hummus in bowl; make a well in centre|Drizzle olive oil; sprinkle paprika and cumin|Arrange vegetables around|Eat with pita, flatbread, or raw vegetables")),

  dict(name="Falafel Bowl",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Medium",cook_time=30,cal=360,prot=14,carb=42,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="middle_eastern",
       detail=dict(serving="1 bowl with 4 falafels (~320g)",
         ingredients="Chickpeas 80g (soaked overnight — do NOT use canned)|Onion 30g|Garlic 3 cloves|Parsley 20g|Cumin 1 tsp|Coriander powder 1 tsp|Baking soda ¼ tsp|Oil for frying|Hummus 50g|Tabbouleh or greens 60g|Tahini sauce 20ml",
         steps="Blend soaked (not cooked) chickpeas with onion, garlic, herbs, spices, baking soda — coarse texture|Rest 30 min in fridge; shape into balls|Deep fry at 180°C for 4-5 min until deep golden|Assemble bowl: greens, hummus, falafel, tahini drizzle")),

  dict(name="Acai Bowl",meal_type="Breakfast; Snack",food_type="vegan",food_group="fruit",
       difficulty="Easy",cook_time=5,cal=285,prot=6,carb=42,fat=10,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 bowl (~280g)",
         ingredients="Frozen acai puree 100g (or acai powder 2 tbsp)|Banana 1 (frozen)|Almond milk 60ml|Toppings: banana slices, granola 30g, chia seeds 1 tsp, honey 1 tsp, berries 30g",
         steps="Blend frozen acai with frozen banana and almond milk — keep very thick (thicker than smoothie)|Pour into bowl immediately|Arrange toppings: granola, banana, berries, chia, honey")),
]

# ── CONTINENTAL / WESTERN ─────────────────────────────────────────────────────
RECIPES += [
  dict(name="Shepherd's Pie",meal_type="Lunch; Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=60,cal=420,prot=24,carb=36,fat=20,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 portion (~320g)",
         ingredients="Minced lamb 150g|Potato 180g (boiled, mashed with butter 10g, milk 30ml)|Onion 60g|Carrot 40g|Celery 30g|Peas 40g|Worcestershire sauce 1 tbsp|Tomato paste 1 tbsp|Rosemary ½ tsp|Thyme ½ tsp|Butter 8g|Salt and pepper",
         steps="Sauté onion, carrot, celery 5 min|Add mince; brown 5 min; drain excess fat|Add tomato paste, Worcestershire, herbs, peas and stock 80ml; simmer 15 min|Transfer to baking dish; top with mashed potato; rough up top with fork|Bake 200°C for 25 min until top golden")),

  dict(name="Quiche Lorraine",meal_type="Breakfast; Lunch",food_type="non-veg",food_group="egg",
       difficulty="Hard",cook_time=60,cal=385,prot=16,carb=22,fat=26,
       p_min=0.5,p_typ=1,p_max=1.25,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 slice (~200g)",
         ingredients="Shortcrust pastry 80g (store-bought or homemade)|Eggs 2|Cream 80ml|Milk 40ml|Bacon 50g (diced)|Gruyere 30g (grated)|Onion 30g (sautéed)|Nutmeg a pinch|Salt and pepper",
         steps="Blind bake pastry shell 15 min at 180°C|Fry bacon until crispy; add to pastry shell with onion and cheese|Beat eggs with cream, milk, nutmeg, salt, pepper|Pour custard into shell; bake 30-35 min at 170°C until just set — centre should wobble slightly|Rest 10 min before slicing")),

  dict(name="Burrito Bowl",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Medium",cook_time=30,cal=450,prot=28,carb=48,fat=16,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="mexican",
       detail=dict(serving="1 bowl (~380g)",
         ingredients="Rice 80g (cooked, seasoned with lime and coriander)|Chicken 100g (grilled, spiced with cumin and chilli)|Black beans 60g (seasoned)|Corn 30g|Capsicum 40g (sautéed)|Salsa 30ml|Guacamole 30g|Sour cream 20ml|Cheddar 15g|Lettuce 30g",
         steps="Cook rice with lime juice and coriander; season with cumin and salt|Grill chicken with Mexican spices (cumin, chilli, paprika)|Layer in bowl: rice base, beans, corn, capsicum, chicken|Top with salsa, guacamole, sour cream, cheese, lettuce")),
]

# ── EAST ASIAN ────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Soba Noodles",meal_type="Lunch; Dinner",food_type="vegan",food_group="pasta",
       difficulty="Easy",cook_time=15,cal=305,prot=12,carb=56,fat=4,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 bowl (~280g)",
         ingredients="Soba noodles 80g (dried)|Soy sauce 2 tbsp|Mirin 1 tbsp|Dashi or vegetable stock 200ml|Spring onion 3 stalks|Nori 1 sheet|Sesame seeds 1 tsp|Ginger ½ tsp",
         steps="Cook soba noodles 5-6 min; rinse under cold water immediately — this stops cooking and removes starch|Heat dashi with soy and mirin for tsuyu broth|Serve cold soba in bowl with broth on side OR hot in broth|Top with spring onion, nori strips, sesame seeds")),

  dict(name="Udon Noodles",meal_type="Lunch; Dinner",food_type="non-veg",food_group="pasta",
       difficulty="Easy",cook_time=15,cal=340,prot=14,carb=60,fat=6,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 bowl (~320g)",
         ingredients="Udon noodles 100g (fresh or dried)|Dashi stock 400ml|Soy sauce 2 tbsp|Mirin 1 tbsp|Fish cake 30g (optional)|Egg 1 (soft boiled, halved)|Spring onion 2 tbsp|Tempura flakes for topping",
         steps="Cook udon noodles; drain; divide into bowl|Heat dashi with soy and mirin; pour over noodles|Top with fish cake, soft-boiled egg, spring onion, tempura flakes|Serve very hot")),

  dict(name="Chilli Garlic Noodles",meal_type="Lunch; Dinner",food_type="vegan",food_group="pasta",
       difficulty="Easy",cook_time=15,cal=360,prot=8,carb=54,fat=12,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="indo_chinese",
       detail=dict(serving="1 plate (~280g)",
         ingredients="Hakka noodles 80g|Garlic 6 cloves (minced)|Red chilli 3 (dried or fresh)|Soy sauce 2 tbsp|Chilli sauce 1 tbsp|Vinegar 1 tsp|Spring onion 3 stalks|Oil 12ml|Salt and pepper",
         steps="Cook noodles; drain; toss with 3ml oil to prevent sticking|Heat remaining oil on high; fry garlic and chilli 1 min until fragrant — do not burn|Add noodles; toss on high heat; add soy, chilli sauce, vinegar; toss 2 min|Finish spring onion")),

  dict(name="Yakisoba",meal_type="Lunch; Dinner",food_type="non-veg",food_group="pasta",
       difficulty="Easy",cook_time=15,cal=375,prot=14,carb=54,fat=12,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 plate (~300g)",
         ingredients="Soba or egg noodles 80g|Chicken or pork 60g (sliced thin)|Cabbage 60g|Carrot 30g|Onion 40g|Yakisoba sauce 3 tbsp (or: Worcestershire 2tbsp + ketchup 1tbsp + soy 1tbsp + oyster sauce 1tbsp)|Oil 10ml|Aonori (seaweed flakes) 1 tsp|Pickled ginger 10g",
         steps="Stir-fry protein on high until just cooked; remove|Stir-fry vegetables 3 min; add noodles; add sauce; toss on high heat 2 min|Return protein; toss together|Serve with aonori and pickled ginger")),

  dict(name="Onigiri",meal_type="Snack; Breakfast",food_type="non-veg",food_group="rice",
       difficulty="Medium",cook_time=20,cal=220,prot=8,carb=40,fat=3,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="east_asian",
       detail=dict(serving="2 rice balls (~160g)",
         ingredients="Japanese short-grain rice 80g (cooked and slightly warm)|Filling 30g (tuna-mayo, salmon flakes, or umeboshi plum)|Nori sheets 2 half-sheets|Salt for hands|Sesame seeds optional",
         steps="Cook rice; cool to just warm|Wet hands; salt lightly; take handful of rice|Place filling in centre; mould into triangle or cylinder pressing firmly|Wrap with nori; eat immediately or wrap in plastic for later")),

  dict(name="Congee",meal_type="Breakfast; Lunch",food_type="non-veg",food_group="rice",
       difficulty="Easy",cook_time=40,cal=265,prot=12,carb=38,fat=7,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 bowl (350ml)",
         ingredients="Rice 40g|Chicken stock 600ml|Chicken 60g (poached, shredded)|Ginger 3 slices|Soy sauce 1 tbsp|Sesame oil 3ml|Spring onion 2 tbsp|White pepper|Fried shallots 10g|Century egg (optional)",
         steps="Simmer rice in stock with ginger on low 30-35 min — stir occasionally; it should break down completely|Add shredded chicken; cook 3 min|Season with soy, white pepper|Bowl up; drizzle sesame oil; top with spring onion, shallots")),

  dict(name="Mapo Tofu",meal_type="Lunch; Dinner",food_type="non-veg",food_group="paneer",
       difficulty="Medium",cook_time=20,cal=295,prot=16,carb=12,fat=19,
       p_min=0.75,p_typ=1,p_max=1.25,role="anchor_protein",cuisine="east_asian",
       detail=dict(serving="1 bowl (~280g)",
         ingredients="Soft/silken tofu 200g (cubed gently)|Pork mince 60g (or omit for vegan)|Doubanjiang (chilli bean paste) 1.5 tbsp|Ginger 1 tsp|Garlic 3 cloves|Soy sauce 1 tbsp|Szechuan peppercorns 1 tsp (ground)|Cornstarch 1 tsp|Chicken stock 100ml|Oil 10ml|Spring onion 2 tbsp",
         steps="Heat oil; fry doubanjiang until oil turns red 1 min|Add pork mince; cook 3 min; add garlic and ginger; cook 30 sec|Add stock and soy; bring to simmer|Gently slide in tofu cubes — do NOT stir hard or tofu breaks|Thicken with cornstarch in water; drizzle sesame oil; add Szechuan pepper|Garnish spring onion")),

  dict(name="Peking Duck",meal_type="Dinner",food_type="non-veg",food_group="chicken",
       difficulty="Hard",cook_time=180,cal=480,prot=30,carb=28,fat=28,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="east_asian",
       detail=dict(serving="1 portion with pancakes (~280g)",
         ingredients="Duck breast 200g (or whole duck portion)|Chinese five spice 1 tsp|Hoisin sauce 3 tbsp|Mandarin pancakes 3|Cucumber 40g (julienned)|Spring onion 3 stalks|Maltose or honey 2 tbsp|Soy sauce 1 tbsp",
         steps="Score duck skin; rub with five spice and salt; hang to air-dry 4-6 hr (or overnight in fridge uncovered)|Coat with maltose-soy glaze; roast at 180°C for 25-30 min; glaze again; raise to 220°C for 10 min for crispy skin|Rest; carve thin slices of skin and meat|Serve wrapped in warm pancake with hoisin, cucumber, spring onion")),

  dict(name="Masala Noodles (Maggi Style)",meal_type="Breakfast; Snack; Lunch",food_type="vegan",food_group="pasta",
       difficulty="Easy",cook_time=10,cal=335,prot=7,carb=52,fat=11,
       p_min=0.75,p_typ=1,p_max=1.5,role="complete_meal",cuisine="indo_chinese",
       detail=dict(serving="1 packet equivalent (~180g cooked)",
         ingredients="Instant noodles 70g|Onion 30g (sliced)|Tomato 30g (chopped)|Green chilli 1|Turmeric a pinch|Chilli powder ¼ tsp|Coriander 1 tbsp|Oil 8ml|Salt to taste|Masala sachet or 1.5 tsp chaat masala + ½ tsp cumin",
         steps="Boil noodles 2 min in water; drain 90% (keep some water)|Heat oil; sauté onion 1 min; add tomato and chilli; cook 1 min|Add noodles and masala; toss on high 1 min|Garnish coriander; eat immediately")),

  dict(name="Shirataki Noodles",meal_type="Lunch; Dinner",food_type="vegan",food_group="pasta",
       difficulty="Easy",cook_time=10,cal=35,prot=1,carb=5,fat=0,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="east_asian",
       detail=dict(serving="1 packet (~200g ready to eat) — extremely low calorie",
         ingredients="Shirataki noodles 200g (konjac noodles)|Soy sauce 1 tbsp|Sesame oil 3ml|Spring onion 2 tbsp|Any desired sauce or broth",
         steps="Drain and rinse noodles VERY well under cold water — they smell strongly from packaging|Dry-fry in a non-stick pan 2-3 min to remove excess water — this improves texture|Add to any sauce, broth or stir-fry|Mostly water and glucomannan fibre — effectively zero net carbs")),

]

# ── MIDDLE EASTERN ────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Mutabbal",meal_type="Snack; Lunch",food_type="vegan",food_group="chaat",
       difficulty="Easy",cook_time=25,cal=175,prot=5,carb=14,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="middle_eastern",
       detail=dict(serving="1 bowl (~180g) with pita",
         ingredients="Eggplant/brinjal 2 large (roasted whole)|Tahini 2 tbsp|Lemon juice 2 tbsp|Garlic 2 cloves|Olive oil 10ml|Pomegranate seeds 1 tbsp|Cumin ¼ tsp|Salt to taste|Parsley 1 tbsp",
         steps="Char eggplant directly on gas flame turning until completely charred outside and soft inside — 15-20 min|Peel; drain in colander 10 min to remove bitter liquid|Chop; mix with tahini, lemon, garlic, cumin, salt|Serve topped with olive oil and pomegranate — similar to baba ganoush but smoother")),

  dict(name="Muhammara",meal_type="Snack; Lunch",food_type="vegan",food_group="chaat",
       difficulty="Medium",cook_time=30,cal=220,prot=5,carb=16,fat=15,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="middle_eastern",
       detail=dict(serving="1 bowl (~180g) — spicy red pepper walnut dip",
         ingredients="Red capsicum 2 (roasted and peeled)|Walnuts 40g (lightly toasted)|Breadcrumbs 20g|Pomegranate molasses 1 tbsp|Lemon juice 1 tbsp|Cumin ½ tsp|Red chilli flakes ½ tsp|Olive oil 10ml|Garlic 2 cloves|Salt to taste",
         steps="Roast capsicum over flame until charred; peel; remove seeds|Blend capsicum with walnuts, breadcrumbs, pomegranate molasses, lemon, garlic, cumin, chilli, salt — leave slightly chunky|Drizzle olive oil on top to serve")),

  dict(name="Dolma",meal_type="Snack; Lunch",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=60,cal=235,prot=8,carb=28,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="middle_eastern",
       detail=dict(serving="4 stuffed grape leaves (~180g)",
         ingredients="Grape leaves 8 (jarred, rinsed)|Rice 40g (short-grain, soaked)|Minced meat 40g (optional — skip for vegan)|Onion 30g|Pine nuts 15g|Raisins 10g|Cinnamon ¼ tsp|Allspice ¼ tsp|Lemon juice 2 tbsp|Olive oil 10ml|Salt and pepper",
         steps="Mix filling: raw rice with meat, onion, pine nuts, raisins, spices, half the oil, salt|Place 1 tsp filling on each leaf; fold sides in; roll tightly|Layer in pot; pour remaining oil, lemon, water to just cover|Weigh down with plate; simmer 40-45 min until rice tender")),

  dict(name="Mujaddara",meal_type="Lunch; Dinner",food_type="vegan",food_group="dal",
       difficulty="Easy",cook_time=45,cal=340,prot=12,carb=52,fat=9,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="middle_eastern",
       detail=dict(serving="1 bowl (~280g) — lentils with rice and crispy onions",
         ingredients="Green or brown lentils 60g|Rice 40g|Onion 150g (sliced)|Cumin 1 tsp|Olive oil 15ml|Salt and pepper|Yogurt to serve (optional)",
         steps="Caramelise onions in olive oil on medium for 25-30 min — they should be deep brown and crispy|Meanwhile cook lentils in water 20 min; add rice; cook 15 min more|Season with cumin, salt, pepper|Top generously with crispy onions — they are the star of this dish")),

  dict(name="Maqluba",meal_type="Lunch; Dinner",food_type="non-veg",food_group="rice",
       difficulty="Hard",cook_time=90,cal=510,prot=28,carb=58,fat=18,
       p_min=0.75,p_typ=1,p_max=1.25,role="complete_meal",cuisine="middle_eastern",
       detail=dict(serving="1 portion (~350g) — upside-down rice dish",
         ingredients="Basmati rice 100g|Chicken 150g (bone-in)|Eggplant 100g (sliced, fried)|Cauliflower 80g (fried)|Onion 60g|Tomato 60g|Chicken stock 400ml|Cumin, turmeric, cinnamon, allspice 1 tsp each|Olive oil 15ml|Pine nuts and almonds for topping|Salt to taste",
         steps="Fry eggplant and cauliflower slices until golden; set aside|Layer in deep pot: fried vegetables at bottom, then chicken, then spiced rice|Pour spiced stock; cover tightly; cook 45 min on low|Flip pot onto serving plate — the drama is in the reveal|Top with toasted pine nuts and almonds")),

  dict(name="Kibbeh",meal_type="Lunch; Dinner; Snack",food_type="non-veg",food_group="kabab",
       difficulty="Hard",cook_time=50,cal=310,prot=18,carb=24,fat=16,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_protein",cuisine="middle_eastern",
       detail=dict(serving="4 pieces (~200g) — spiced lamb and bulgur wheat",
         ingredients="Fine bulgur wheat 60g (soaked 15 min, squeezed)|Minced lamb 100g|Onion 40g|Pine nuts 15g|Raisins 10g|Cumin 1 tsp|Allspice ½ tsp|Cinnamon ¼ tsp|Olive oil 10ml|Salt and pepper",
         steps="Shell: blend bulgur with half the mince, onion, cumin, salt to smooth paste|Filling: sauté remaining mince with pine nuts, raisins, spices 5 min|Shape oval shells around filling; seal tightly|Deep fry at 180°C for 6-8 min until dark golden|OR bake 200°C for 25 min")),
]

# ── DRINKS ────────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Badam Milk",meal_type="Breakfast; Snack",food_type="veg",food_group="drink",
       difficulty="Easy",cook_time=10,cal=215,prot=8,carb=20,fat=11,
       p_min=0.5,p_typ=1,p_max=1.5,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 glass (250ml)",
         ingredients="Milk 200ml|Almonds 15g (soaked overnight, peeled, ground to paste)|Saffron 8-10 strands|Cardamom ¼ tsp (ground)|Sugar or honey 1 tsp|Rose water ¼ tsp (optional)",
         steps="Soak almonds overnight; peel; blend to smooth paste with 2 tbsp milk|Heat milk; add almond paste; whisk well|Add saffron, cardamom, sugar; simmer 5 min on low|Add rose water; serve hot or chilled")),

  dict(name="Sweet Lassi",meal_type="Breakfast; Snack",food_type="veg",food_group="drink",
       difficulty="Easy",cook_time=5,cal=185,prot=7,carb=26,fat=5,
       p_min=0.5,p_typ=1,p_max=1.5,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 glass (250ml)",
         ingredients="Yogurt 150ml (full fat)|Milk 60ml (chilled)|Sugar 2 tsp|Cardamom ¼ tsp|Rose water ¼ tsp|Ice cubes 3-4|Dried rose petals (garnish)",
         steps="Blend yogurt, milk, sugar, cardamom and rose water with ice until frothy|Pour into glass; garnish rose petals and a pinch of cardamom")),

  dict(name="Aam Panna",meal_type="Snack; Breakfast",food_type="vegan",food_group="drink",
       difficulty="Easy",cook_time=20,cal=95,prot=0,carb=24,fat=0,
       p_min=0.5,p_typ=1,p_max=2,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 glass (250ml) — raw mango summer cooler",
         ingredients="Raw green mango 1 medium (~150g)|Sugar 2-3 tsp|Black salt ¼ tsp|Cumin powder ½ tsp|Mint leaves 8|Water 200ml|Ice",
         steps="Pressure cook or boil raw mango until soft; cool; peel and extract pulp|Blend pulp with sugar, black salt, cumin, mint and some water to concentrate|Strain; dilute with cold water to taste|Serve with ice; adjust sweet/sour/salty balance")),

  dict(name="Jaljeera",meal_type="Snack",food_type="vegan",food_group="drink",
       difficulty="Easy",cook_time=5,cal=40,prot=0,carb=10,fat=0,
       p_min=0.5,p_typ=1,p_max=2,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 glass (250ml) — spiced cumin water",
         ingredients="Water 250ml (chilled)|Jaljeera masala 1 tsp (or: cumin powder ½ tsp, black salt ¼ tsp, dried ginger ¼ tsp, amchur ¼ tsp, mint powder)|Lemon juice 1 tsp|Sugar ½ tsp|Boondi 1 tbsp (optional garnish)",
         steps="Mix all ingredients in glass; stir well|Taste and adjust salt, sour, spice balance|Add boondi on top if desired; serve chilled")),

  dict(name="Sattu Sharbat",meal_type="Breakfast; Snack",food_type="vegan",food_group="drink",
       difficulty="Easy",cook_time=3,cal=145,prot=8,carb=22,fat=2,
       p_min=0.5,p_typ=1,p_max=1.5,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 glass (300ml) — roasted chana flour drink, high protein",
         ingredients="Sattu flour 40g|Water 250ml (chilled)|Black salt ¼ tsp|Cumin powder ¼ tsp|Lemon juice 1 tsp|Sugar 1 tsp OR salt and green chilli for savoury version|Mint leaves 4",
         steps="Mix sattu flour with water first — add water to flour gradually, whisking to avoid lumps|Add black salt, cumin, lemon|Sweeten or savour to taste|Serve chilled with ice; excellent electrolyte drink in summer")),

  dict(name="Masala Chai",meal_type="Breakfast; Snack",food_type="veg",food_group="drink",
       difficulty="Easy",cook_time=8,cal=70,prot=3,carb=8,fat=2,
       p_min=0.5,p_typ=1,p_max=2,role="beverage",cuisine="north_indian",
       detail=dict(serving="1 cup (150ml)",
         ingredients="Water 100ml|Milk 80ml|Tea leaves 1 tsp (strong black tea)|Ginger ½ tsp (freshly grated)|Cardamom 1 pod (crushed)|Cloves 1|Cinnamon small piece|Sugar 1 tsp (or to taste)",
         steps="Bring water to boil with ginger, cardamom, cloves, cinnamon|Add tea leaves; boil 1 min|Add milk; bring back to boil; reduce 1 min|Strain into cup; add sugar|Adjust milk/water ratio to strength preference")),
]

# ── DESSERTS ──────────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Rava Kesari",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Easy",cook_time=20,cal=320,prot=4,carb=46,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="south_indian",
       detail=dict(serving="1 portion (~150g) — South Indian semolina dessert",
         ingredients="Semolina (rava) 60g|Ghee 15ml|Sugar 40g|Water 200ml|Saffron 8 strands|Cashews 10g|Raisins 10g|Cardamom ¼ tsp",
         steps="Heat ghee; fry cashews and raisins until golden; remove|Roast rava in same ghee 4 min until fragrant|Boil water with saffron; gradually add to rava, stirring constantly|Add sugar; cook 3-4 min until thick and glossy|Finish with cardamom; top with cashews and raisins")),

  dict(name="Kulfi",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Medium",cook_time=120,cal=265,prot=7,carb=30,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="1 kulfi (~100ml) — traditional Indian ice cream",
         ingredients="Full fat milk 300ml|Sugar 30g|Cardamom ½ tsp|Saffron 8 strands|Pistachios 15g (chopped)|Almonds 10g (chopped)|Rose water ½ tsp",
         steps="Simmer milk stirring frequently for 30-40 min until reduced to ⅓ volume — no shortcuts|Add sugar, cardamom, saffron; stir 3 min; cool completely|Add rose water and nuts; pour into kulfi moulds|Freeze minimum 6 hours")),

  dict(name="Falooda",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Medium",cook_time=20,cal=295,prot=6,carb=52,fat=7,
       p_min=0.75,p_typ=1,p_max=1.25,role="side",cuisine="north_indian",
       detail=dict(serving="1 tall glass (~300ml)",
         ingredients="Milk 150ml (chilled)|Rose syrup 2 tbsp|Basil seeds (sabja) 1 tsp (soaked in water — they swell to jelly)|Falooda sev/thin vermicelli 20g (cooked)|Kulfi or vanilla ice cream 1 scoop|Rose water ¼ tsp|Tutti frutti 1 tbsp",
         steps="Soak sabja seeds 15 min; they will swell 10× in size|Cook vermicelli 2 min; drain; cool|Layer in glass: rose syrup, milk, vermicelli, sabja seeds|Top with ice cream scoop; drizzle more rose syrup; garnish tutti frutti")),

  dict(name="Gajar Ka Halwa",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Medium",cook_time=45,cal=295,prot=6,carb=38,fat=13,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="1 bowl (~150g) — carrot pudding",
         ingredients="Carrots 250g (finely grated)|Full fat milk 200ml|Ghee 15ml|Sugar 30g|Cardamom ½ tsp|Khoya/mawa 30g (condensed milk solids)|Cashews 10g|Raisins 8g",
         steps="Sauté grated carrots in ghee 5 min|Add milk; cook on medium stirring frequently 20 min until milk absorbed|Add sugar; cook 5 min; add khoya; cook 5 more min until thick|Finish with cardamom; garnish cashews and raisins")),

  dict(name="Gulab Jamun",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Hard",cook_time=45,cal=250,prot=4,carb=40,fat=8,
       p_min=0.5,p_typ=1,p_max=2,role="side",cuisine="north_indian",
       detail=dict(serving="3 pieces (~120g) in syrup",
         ingredients="Khoya/mawa 80g|Maida 15g|Baking soda a pinch|Milk 1 tbsp|Ghee for frying|Sugar syrup (sugar 100g, water 150ml, cardamom 2, rose water ½ tsp)",
         steps="Mix khoya, maida, baking soda; add milk to soft dough — do not over-knead|Shape into smooth balls with no cracks|Deep fry on VERY LOW heat 8-10 min — they must be cooked all the way through|Make hot sugar syrup; add fried jamuns immediately|Soak 30 min before serving; they will double in size")),

  dict(name="Rasmalai",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Hard",cook_time=60,cal=235,prot=8,carb=32,fat=8,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="north_indian",
       detail=dict(serving="2 pieces (~150g) in cream",
         ingredients="Chenna (fresh paneer from 500ml milk)|Milk 400ml (for ras/cream)|Sugar 50g|Saffron 10 strands|Cardamom ½ tsp|Pistachios 10g (for garnish)|Rose water ¼ tsp",
         steps="Make fresh chenna; knead until smooth; shape into flat discs|Cook discs in light sugar syrup 15 min; they will double in size|Meanwhile reduce milk with sugar, saffron, cardamom to thick ras (30 min)|Squeeze excess syrup from cooked rasgullas; soak in chilled ras 2 hr|Serve cold with pistachio garnish")),

  dict(name="Baklava",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Hard",cook_time=60,cal=310,prot=5,carb=36,fat=16,
       p_min=0.5,p_typ=1,p_max=1.5,role="side",cuisine="middle_eastern",
       detail=dict(serving="3 pieces (~120g) — layered pastry with nuts",
         ingredients="Phyllo pastry 8 sheets|Walnuts or pistachios 80g (finely chopped)|Butter 40g (melted)|Sugar syrup (sugar 80g, water 60ml, lemon juice 1 tsp, honey 1 tbsp, orange blossom water ½ tsp)",
         steps="Layer phyllo sheets brushing each with butter; add nut layer; continue layering|Score diamond shapes with sharp knife before baking|Bake 180°C for 30-35 min until golden|Immediately pour cold syrup over hot baklava — this creates the signature soaking|Cool completely 2 hr before serving")),

  dict(name="Knafeh",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Hard",cook_time=45,cal=340,prot=8,carb=44,fat=15,
       p_min=0.5,p_typ=1,p_max=1.25,role="side",cuisine="middle_eastern",
       detail=dict(serving="1 portion (~180g) — cheese pastry with syrup",
         ingredients="Kataifi/shredded pastry 80g|Akkawi or ricotta cheese 100g (unsalted)|Butter 25g (melted)|Sugar syrup 60ml (sugar, water, orange blossom water)|Pistachios 10g (for garnish)",
         steps="Soak cheese in water 1 hr if salty; drain and crumble|Mix kataifi with melted butter thoroughly|Press half into greased pan; layer cheese; press remaining kataifi on top|Bake 180°C for 25-30 min until golden|Immediately pour cold sugar syrup; invert onto plate; garnish pistachios")),

  dict(name="Moong Dal Halwa",meal_type="Snack",food_type="veg",food_group="dessert",
       difficulty="Hard",cook_time=60,cal=380,prot=8,carb=50,fat=16,
       p_min=0.5,p_typ=1,p_max=1.25,role="side",cuisine="north_indian",
       detail=dict(serving="1 portion (~150g) — labour-intensive winter dessert",
         ingredients="Yellow moong dal 80g (soaked 4 hr, drained, ground to paste)|Ghee 20ml|Sugar 40g|Milk 150ml|Cardamom ½ tsp|Saffron 8 strands|Cashews 10g|Raisins 8g",
         steps="Heat ghee; add moong dal paste — it will splutter; cook stirring CONTINUOUSLY on medium 25-30 min until it turns golden and fragrant and leaves ghee|Add warm milk and saffron; cook stirring 10 min until absorbed|Add sugar; cook 5 more min; finish cardamom|Top with cashews and raisins; extremely rich — small portions only")),
]

# ── MISCELLANEOUS ─────────────────────────────────────────────────────────────
RECIPES += [
  dict(name="Turkey Sandwich",meal_type="Breakfast; Lunch; Snack",food_type="non-veg",food_group="toast",
       difficulty="Easy",cook_time=5,cal=295,prot=22,carb=28,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="complete_meal",cuisine="continental",
       detail=dict(serving="1 sandwich (2 slices bread ~180g)",
         ingredients="Whole wheat or multigrain bread 2 slices|Turkey breast slices 60g|Lettuce 1 leaf|Tomato 1 slice|Cheese slice 1|Mustard or mayo 1 tsp|Salt and pepper",
         steps="Toast bread if desired|Spread condiment; layer lettuce, tomato, turkey, cheese|Season; press together")),

  dict(name="Aloo Posto",meal_type="Lunch; Dinner",food_type="vegan",food_group="veg_curry",
       difficulty="Easy",cook_time=20,cal=225,prot=4,carb=28,fat=10,
       p_min=0.5,p_typ=1,p_max=1.5,role="anchor_veg",cuisine="north_indian",
       detail=dict(serving="1 bowl (~200g) — Bengali poppy seed potato",
         ingredients="Potato 200g (cubed)|Poppy seeds (posto) 3 tbsp (soaked 20 min, ground to paste)|Green chilli 2|Mustard oil 12ml|Turmeric ¼ tsp|Salt to taste|Sugar ½ tsp",
         steps="Grind soaked posto with green chilli and a little water to smooth paste|Heat mustard oil until smoking; reduce heat|Add potato; stir; cook covered 8 min|Add posto paste, turmeric, salt, sugar; stir gently|Cook covered 5 min on low — do not let posto burn")),
]

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTION BLOCK
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Diet Tracker — Additional Recipe Seed Script")
    print("=" * 50)
    print(f"Total recipes to process: {len(RECIPES)}")
    print()

    conn = get_connection()
    inserted = 0
    skipped  = 0
    failed   = 0

    for r in RECIPES:
        try:
            if _insert_recipe(conn, r):
                inserted += 1
                print(f"  ✓ {r['name']}")
            else:
                skipped += 1
        except Exception as e:
            print(f"  ✗ {r.get('name','?')} — ERROR: {e}")
            failed += 1

    conn.close()
    print()
    print("=" * 50)
    print(f"Done — Inserted: {inserted}  |  Skipped: {skipped}  |  Failed: {failed}")

    if failed > 0:
        print()
        print("NOTE: Failed inserts are likely due to the cuisine constraint.")
        print("Make sure add_cuisines_v3.sql was run in Supabase before this script.")
