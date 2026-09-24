FROM python:3.13-slim
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
RUN pip install docoreai 
RUN pip install google-genai
ENV DOCOREAI_ENV_PATH=/app/data
COPY entrypoint.sh /entrypoint.sh
COPY apply_config.py /app/apply_config.py

# Testing only
COPY gemini.py /app/gemini.py
# Testing only
COPY shopease_single_shot_prompts-10000.csv /app/shopease_single_shot_prompts-10000.csv

RUN chmod +x /entrypoint.sh
WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
