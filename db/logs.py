# db/logs.py
import pandas as pd
from datetime import date, timedelta
from db.connection import execute


def log_meal(conn, user_id: int, log_date: date, recipe_name: str,
             meal_type: str, calories: int, protein_g: float,
             carb_g: float, fat_g: float):
    execute(conn,
        """INSERT INTO meal_logs
             (user_id, log_date, recipe_name, meal_type, calories,
              protein_g, carb_g, fat_g)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (user_id, str(log_date), recipe_name, meal_type,
         int(calories), float(protein_g), float(carb_g), float(fat_g)))


def get_today_logs(conn, user_id: int) -> pd.DataFrame:
    rows = execute(conn,
        """SELECT recipe_name, meal_type, calories, protein_g, carb_g, fat_g, logged_at
           FROM meal_logs
           WHERE user_id = %s AND log_date = %s
           ORDER BY logged_at""",
        (user_id, str(date.today())), fetch="all")
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_logs_for_date(conn, user_id: int, log_date: date) -> pd.DataFrame:
    rows = execute(conn,
        """SELECT id, recipe_name, meal_type, calories,
                  protein_g, carb_g, fat_g, logged_at
           FROM meal_logs
           WHERE user_id = %s AND log_date = %s
           ORDER BY logged_at""",
        (user_id, str(log_date)), fetch="all")
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_week_summary(conn, user_id: int) -> pd.DataFrame:
    start = str(date.today() - timedelta(days=6))
    rows = execute(conn,
        """SELECT log_date,
                  SUM(calories)  AS total_cal,
                  SUM(protein_g) AS total_prot,
                  SUM(carb_g)    AS total_carb,
                  SUM(fat_g)     AS total_fat
           FROM meal_logs
           WHERE user_id = %s AND log_date BETWEEN %s AND %s
           GROUP BY log_date ORDER BY log_date""",
        (user_id, start, str(date.today())), fetch="all")
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def get_last_n_days_logs(conn, user_id: int, n: int = 5) -> pd.DataFrame:
    """
    Returns per-day macro totals for the last N days that actually have logs
    (days with zero entries are excluded, per spec).
    """
    start = str(date.today() - timedelta(days=30))  # look back 30 days, take last n
    rows = execute(conn,
        """SELECT log_date,
                  SUM(calories)  AS total_cal,
                  SUM(protein_g) AS total_prot,
                  SUM(carb_g)    AS total_carb,
                  SUM(fat_g)     AS total_fat,
                  COUNT(*)       AS n_entries
           FROM meal_logs
           WHERE user_id = %s AND log_date BETWEEN %s AND %s
           GROUP BY log_date
           HAVING COUNT(*) > 0
           ORDER BY log_date DESC
           LIMIT %s""",
        (user_id, start, str(date.today()), n), fetch="all")
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    return df.sort_values("log_date") if not df.empty else df


def delete_log_entry(conn, log_id: int):
    execute(conn, "DELETE FROM meal_logs WHERE id = %s", (log_id,))
