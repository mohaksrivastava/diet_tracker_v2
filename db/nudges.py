# db/nudges.py
from datetime import date
from db.connection import execute


def store_nudge(conn, user_id: int, days_analyzed: int,
                adjusted_cal: float, adjusted_prot: float,
                adjusted_carb: float, adjusted_fat: float,
                nudge_text: str):
    execute(conn,
        """INSERT INTO nudges
             (user_id, generated_on, days_analyzed, adjusted_cal,
              adjusted_prot, adjusted_carb, adjusted_fat, nudge_text)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (user_id, str(date.today()), days_analyzed,
         adjusted_cal, adjusted_prot, adjusted_carb, adjusted_fat,
         nudge_text))


def get_latest_nudge(conn, user_id: int, seen: bool = False) -> dict | None:
    """Return the most recent nudge for a user. Filter by seen status."""
    row = execute(conn,
        """SELECT * FROM nudges
           WHERE user_id = %s AND seen = %s
           ORDER BY created_at DESC LIMIT 1""",
        (user_id, seen), fetch="one")
    return dict(row) if row else None


def get_all_nudges(conn, user_id: int, limit: int = 10) -> list[dict]:
    rows = execute(conn,
        """SELECT * FROM nudges WHERE user_id = %s
           ORDER BY created_at DESC LIMIT %s""",
        (user_id, limit), fetch="all")
    return [dict(r) for r in rows]


def mark_nudge_seen(conn, nudge_id: int):
    execute(conn,
        "UPDATE nudges SET seen = TRUE WHERE id = %s", (nudge_id,))


def nudge_exists_for_today(conn, user_id: int) -> bool:
    row = execute(conn,
        "SELECT id FROM nudges WHERE user_id = %s AND generated_on = %s LIMIT 1",
        (user_id, str(date.today())), fetch="one")
    return row is not None
