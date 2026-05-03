# db/recipes.py  — consolidated single-table schema
import pandas as pd
from db.connection import execute

def get_all_recipes(conn) -> pd.DataFrame:
    base = execute(conn,
        """SELECT id, name, category, meal_type, food_type, food_group,
                  difficulty, cook_time_mins, calories, protein, carbohydrate, fat,
                  portion_min, portion_typical, portion_max, role, cuisine
           FROM recipes ORDER BY name""", fetch="all")
    custom = execute(conn,
        """SELECT id, name, category, meal_type, food_type, food_group,
                  difficulty, cook_time_mins, calories, protein, carbohydrate, fat,
                  COALESCE(portion_min,0.5) AS portion_min,
                  COALESCE(portion_typical,1.0) AS portion_typical,
                  COALESCE(portion_max,1.5) AS portion_max,
                  COALESCE(role,'side') AS role,
                  COALESCE(cuisine,'unknown') AS cuisine
           FROM custom_recipes WHERE status='filled' AND calories IS NOT NULL
           ORDER BY name""", fetch="all")
    rows = list(base or []) + list(custom or [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    for col in ["calories","protein","carbohydrate","fat",
                "portion_min","portion_typical","portion_max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_recipe_names(conn) -> list:
    rows = execute(conn,
        "SELECT name FROM recipes UNION SELECT name FROM custom_recipes WHERE status != 'rejected'",
        fetch="all")
    return [r["name"] for r in rows]

def get_recipe_detail(conn, recipe_name: str) -> dict | None:
    row = execute(conn,
        "SELECT name, serving_note, ingredients, steps FROM recipes WHERE name=%s LIMIT 1",
        (recipe_name,), fetch="one")
    if row: return dict(row)
    row = execute(conn,
        "SELECT name, serving_note, ingredients, steps FROM custom_recipes WHERE name=%s AND status='filled' LIMIT 1",
        (recipe_name,), fetch="one")
    return dict(row) if row else None

def get_pending_custom_recipes(conn) -> list:
    rows = execute(conn,
        "SELECT * FROM custom_recipes WHERE status='pending' ORDER BY created_at", fetch="all")
    return [dict(r) for r in rows]

def add_custom_recipe(conn, user_id: int, name: str):
    execute(conn,
        "INSERT INTO custom_recipes (added_by, name, status) VALUES (%s,%s,'pending')",
        (user_id, name.strip()))

def fill_custom_recipe(conn, recipe_id: int, data: dict):
    execute(conn,
        """UPDATE custom_recipes SET status='filled',meal_type=%s,food_type=%s,
             food_group=%s,difficulty=%s,cook_time_mins=%s,calories=%s,protein=%s,
             carbohydrate=%s,fat=%s,portion_min=%s,portion_typical=%s,portion_max=%s,
             role=%s,cuisine=%s,serving_note=%s,ingredients=%s,steps=%s,filled_at=NOW()
           WHERE id=%s""",
        (data.get("meal_type"), data.get("food_type"), data.get("food_group"),
         data.get("difficulty"), data.get("cook_time_mins"),
         data.get("calories"), data.get("protein"), data.get("carbohydrate"), data.get("fat"),
         data.get("portion_min",0.5), data.get("portion_typical",1.0), data.get("portion_max",1.5),
         data.get("role","side"), data.get("cuisine","unknown"),
         data.get("serving_note"), data.get("ingredients"), data.get("steps"),
         recipe_id))

def reject_custom_recipe(conn, recipe_id: int, reason: str):
    execute(conn, "UPDATE custom_recipes SET status='rejected',reject_reason=%s WHERE id=%s",
            (reason, recipe_id))

def get_custom_recipes_for_user(conn, user_id: int) -> list:
    rows = execute(conn,
        "SELECT name,status,reject_reason,created_at,filled_at FROM custom_recipes WHERE added_by=%s ORDER BY created_at DESC",
        (user_id,), fetch="all")
    return [dict(r) for r in rows]

def log_optimizer_run(conn, user_id, k_meals, num_candidates, num_feasible,
                      relaxation_level, runtime_ms, food_pref):
    try:
        execute(conn,
            "INSERT INTO optimizer_log (user_id,k_meals,num_candidates,num_feasible,relaxation_level,runtime_ms,food_pref) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (user_id,k_meals,num_candidates,num_feasible,relaxation_level,runtime_ms,food_pref))
    except Exception:
        pass
