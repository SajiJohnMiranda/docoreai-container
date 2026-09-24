#!/bin/sh
mkdir -p /app/data
docoreai init

# Apply client config if present
python /app/apply_config.py

docoreai start &
exec python gemini.py shopease_single_spot_prompts-10000.csv 100
