FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

COPY src ./src
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev


FROM python:3.13-slim

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv

RUN playwright install --with-deps chromium

COPY . .

CMD ["opentelemetry-instrument", "uvicorn", "task.__main__:app", "--host", "0.0.0.0", "--port", "8000"]
