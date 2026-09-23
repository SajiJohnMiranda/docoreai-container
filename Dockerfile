FROM python:3.13-slim
RUN pip install docoreai google-genai
ENV DOCOREAI_ENV_PATH=/app/data
COPY entrypoint.sh /entrypoint.sh
COPY gemini.py /app/gemini.py
COPY shopease_single_shot_prompts-10000.csv /app/shopease_single_shot_prompts-10000.csv
RUN chmod +x /entrypoint.sh
WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
