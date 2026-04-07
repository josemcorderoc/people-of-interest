FROM python:3.14-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
COPY config/ config/
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "uvicorn", "poi_people.infrastructure.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
