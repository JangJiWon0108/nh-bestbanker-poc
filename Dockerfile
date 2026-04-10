# Cloud Run: gcloud run deploy ... --source .
# Python 3.13 + uv (의존성은 uv.lock 기준 고정)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PORT=8080
EXPOSE 8080

# Cloud Run이 PORT를 주입함
CMD ["sh", "-c", "uv run uvicorn cloud_run_server:app --host 0.0.0.0 --port ${PORT:-8080}"]
