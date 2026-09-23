#!/bin/sh
mkdir -p /app/data
docoreai init
# Overwrite env_path in DB with the correct container path
python -c "
import os
from docore_ai.config.db import get_connection
env_path = os.environ.get('DOCOREAI_ENV_PATH', '/app/data')
conn = get_connection()
conn.execute('UPDATE telemetry_settings SET env_path=? WHERE id=1', (env_path,))
conn.commit()
conn.close()
"
docoreai start &
exec python gemini.py shopease_single_shot_prompts-10000.csv 10
