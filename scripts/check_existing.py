import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection, execute

conn = get_connection()

base = execute(conn, "SELECT name FROM recipes ORDER BY name", fetch="all")
custom = execute(conn, "SELECT name FROM custom_recipes WHERE status != 'rejected' ORDER BY name", fetch="all")

names = []
for r in base:
    names.append({"name": r["name"], "source": "recipes"})
for r in custom:
    names.append({"name": r["name"], "source": "custom_recipes"})

output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "existing_recipes.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(names, f, indent=2, ensure_ascii=False)

print(f"Found {len(base)} base recipes and {len(custom)} custom recipes")
print(f"Wrote {len(names)} total names to {output_path}")

conn.close()
