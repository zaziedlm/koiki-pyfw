# syntax=docker/dockerfile:1.7
# Dockerfile - Multi-stage build for FastAPI backend

# ---------------------
# Base stage with uv and dependencies
# ---------------------
FROM python:3.13.18-slim-bookworm AS base

# Add custom certificate and ensure CA bundle is installed/updated
# Optional organization CA; session proxy roots are supplied separately as BuildKit secrets.
RUN --mount=type=bind,source=docker/certs,target=/run/koiki-ca,readonly \
    if [ -f /run/koiki-ca/nscacert.pem ]; then \
      install -m 0644 /run/koiki-ca/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt; \
    fi
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Explicitly specify certificate path for Python environment
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /usr/local/bin/

ENV UV_CACHE_DIR=/opt/uv-cache \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

RUN uv --version

WORKDIR /app

# uv: Copy dependency files for better Docker layer caching
COPY pyproject.toml uv.lock README.md ./

# アプリケーションコードのコピー (component 構成)
COPY ./app ./app
COPY ./components ./components
COPY ./ops ./ops

# uv: Install all dependencies used by the development image
RUN --mount=type=secret,id=proxy_ca \
    export SSL_CERT_FILE=${SSL_CERT_FILE:-/etc/ssl/certs/ca-certificates.crt}; \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    mkdir -p $UV_CACHE_DIR \
    && uv sync --locked --group dev --group test --no-editable

# docker-entrypoint.shをコピーして実行権限を付与
COPY docker-entrypoint.sh ./
RUN chmod +x /app/docker-entrypoint.sh

# ---------------------
# Development stage
# ---------------------
FROM base AS dev

# セキュリティ強化: 非rootユーザーの作成
RUN adduser --disabled-password --gecos "" appuser

# Alembic versionsディレクトリの作成と所有者変更
# /opt/uv-cache も appuser に chown する (named volume がroot所有で初期化されるのを防ぐ)
RUN mkdir -p /app/components/koiki_ref_app/alembic/versions \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /opt/uv-cache

# 非rootユーザーに切り替え
USER appuser

# エントリポイントとコマンドの設定
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Uvicornのデフォルトポート
EXPOSE 8000

# デフォルトコマンド (docker-compose で上書き可能)
CMD ["uvicorn", "koiki_ref_app.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Install only application dependencies into the final image.
FROM base AS production-deps
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --locked --no-dev --no-editable

# ---------------------
# Production stage
# ---------------------
FROM python:3.13.18-slim-bookworm AS production

# Add custom certificate
# Optional organization CA; session proxy roots are supplied separately as BuildKit secrets.
RUN --mount=type=bind,source=docker/certs,target=/run/koiki-ca,readonly \
    if [ -f /run/koiki-ca/nscacert.pem ]; then \
      install -m 0644 /run/koiki-ca/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt; \
    fi
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Drop unused system installer and its bundled wheel from the runtime.
RUN /usr/local/bin/python -m pip uninstall -y pip && \
    rm -rf /usr/local/lib/python3.13/ensurepip

WORKDIR /app

# セキュリティ強化: 非rootユーザーの作成
RUN adduser --disabled-password --gecos "" appuser

COPY --from=production-deps /app /app

# Alembic versionsディレクトリの作成と所有者変更
RUN mkdir -p /app/components/koiki_ref_app/alembic/versions && chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser

# エントリポイントとコマンドの設定
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Uvicornのデフォルトポート
EXPOSE 8000

# デフォルトコマンド (docker-compose で上書き可能)
CMD ["uvicorn", "koiki_ref_app.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
