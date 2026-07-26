FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml alembic.ini docker-entrypoint.sh ./
COPY app ./app
COPY tests ./tests
COPY migrations ./migrations

RUN pip install --no-cache-dir -e ".[dev]" && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
