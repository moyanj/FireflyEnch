FROM node:24-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/moyan/.venv \
    PATH="/moyan/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /moyan

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
COPY --from=frontend-build /frontend/dist ./files

RUN chmod +x /moyan/entrypoint.sh \
    && mkdir -p /moyan/data/uploads /moyan/data/thumbs /moyan/data/temp \
    && adduser --system --group moyan \
    && chown -R moyan:moyan /moyan

VOLUME ["/moyan/data"]

EXPOSE 8896

ENTRYPOINT ["/moyan/entrypoint.sh"]
CMD ["python", "app.py"]
