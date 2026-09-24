FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libegl1 \
    libfontconfig1 \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

RUN pip install docoreai==2.3.6
RUN pip install google-genai

ENV DOCOREAI_ENV_PATH=/app/data

COPY entrypoint.sh /entrypoint.sh
COPY apply_config.py /app/apply_config.py
RUN mkdir -p /app/data
COPY client_config.csv /app/data/client_config.csv

# Testing Only - Goes to volumes in Prod
COPY gemini.py /app/gemini.py
COPY shopease_single_shot_prompts-10000.csv /app/shopease_single_shot_prompts-10000.csv

RUN chmod +x /entrypoint.sh
WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
