# db/users.py
import bcrypt
from db.connection import execute


# ── Auth ──────────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def get_user_by_name(conn, name: str):
    return execute(conn,
        "SELECT * FROM users WHERE name = %s LIMIT 1",
        (name,), fetch="one")


def get_all_users(conn):
    return execute(conn,
        "SELECT id, name, daily_cal, num_meals, food_pref FROM users ORDER BY name",
        fetch="all")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_user(conn, name: str, plain_password: str,
                daily_cal: int = 1800, num_meals: int = 3,
                food_pref: str = "veg"):
    pw_hash = hash_password(plain_password)
    execute(conn,
        """INSERT INTO users (name, password_hash, daily_cal, num_meals, food_pref)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (name) DO NOTHING""",
        (name.strip(), pw_hash, daily_cal, num_meals, food_pref))


def update_user_settings(conn, user_id: int, daily_cal: int,
                         num_meals: int, food_pref: str):
    execute(conn,
        """UPDATE users
           SET daily_cal = %s, num_meals = %s, food_pref = %s
           WHERE id = %s""",
        (daily_cal, num_meals, food_pref, user_id))


def update_password(conn, user_id: int, plain_password: str):
    pw_hash = hash_password(plain_password)
    execute(conn,
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (pw_hash, user_id))
