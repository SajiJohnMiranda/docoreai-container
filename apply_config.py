import csv, os
from pathlib import Path
from docore_ai.config.db import get_connection, init_db
init_db()
config_path = Path(os.environ.get("DOCOREAI_ENV_PATH", "/app/data")) / "client_config.csv"

if not config_path.exists():
    print("No client_config.csv found — using DB defaults.")
    exit(0)

conn = get_connection()
applied = 0
errors = 0

with open(config_path) as f:
    for row in csv.DictReader(f):
        category  = row["category"].strip()
        key       = row["config_key"].strip()
        value     = row["config_value"].strip()

        # 1. Validate the key exists in DB first
        existing = conn.execute("""
            SELECT value_type FROM phase2_config 
            WHERE category=? AND config_key=?
        """, (category, key)).fetchone()

        if not existing:
            print(f"❌ Unknown config: {category}.{key} — skipping")
            errors += 1
            continue

        # 2. Validate value type
        value_type = existing[0]
        try:
            if value_type == "int":
                int(value)
            elif value_type == "float":
                float(value)
            elif value_type == "bool":
                if value.lower() not in ("true", "false"):
                    raise ValueError()
        except ValueError:
            print(f"❌ Invalid value for {category}.{key}: '{value}' (expected {value_type}) — skipping")
            errors += 1
            continue

        # 3. Apply
        conn.execute("""
            UPDATE phase2_config 
            SET config_value=?
            WHERE category=? AND config_key=?
        """, (value, category, key))
        print(f"✅ {category}.{key} = {value}")
        applied += 1

conn.commit()
conn.close()
print(f"\nDone: {applied} applied, {errors} errors")

if errors > 0:
    exit(1)  # fail loud so entrypoint.sh knows something went wrong
