#!/bin/sh
mkdir -p /app/data
docoreai init

# Fix env_path in DB
python -c "
import os
from docore_ai.config.db import get_connection
env_path = os.environ.get('DOCOREAI_ENV_PATH', '/app/data')
conn = get_connection()
conn.execute('UPDATE telemetry_settings SET env_path=? WHERE id=1', (env_path,))
conn.commit()
conn.close()
"

# Apply client config if present
python /app/apply_config.py

docoreai start &
exec python gemini.py shopease_single_shot_prompts-10000.csv 100
