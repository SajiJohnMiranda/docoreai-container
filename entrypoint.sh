#!/bin/sh
docoreai init
docoreai start &
exec python gemini.py shopease_single_shot_prompts-10000.csv 100
