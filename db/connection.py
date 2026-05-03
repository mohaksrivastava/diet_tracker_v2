# db/connection.py
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Return a psycopg2 connection. Caller is responsible for closing."""
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        dbname="postgres",
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASS"),
        port=5432,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

def execute(conn, sql, params=None, fetch="none"):
    """
    Thin helper to run a query and return results.
    fetch: "none" | "one" | "all"
    """
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        if fetch == "all":
            return cur.fetchall()
        if fetch == "one":
            return cur.fetchone()
        conn.commit()
        return cur.rowcount
