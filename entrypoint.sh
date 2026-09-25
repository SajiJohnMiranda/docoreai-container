#!/bin/sh
mkdir -p /app/data
docoreai init
python /app/apply_config.py
docoreai start &
exec python gemini.py shopease_single_shot_prompts-10000.csv 100
