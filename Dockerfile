FROM python:3.13-slim
RUN pip install docoreai
ENV DOCOREAI_ENV_PATH=/app/data
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
