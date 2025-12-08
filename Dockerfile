# Dockerfile
FROM python:3.14.1-slim

# Poetry 2.x: Optimized environment variables for performance and caching
ENV POETRY_VERSION=2.1.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/opt/poetry-cache \
    POETRY_INSTALLER_PARALLEL=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    PATH="$POETRY_HOME/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# poetryのインストール
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION \
    && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry \
    && poetry --version

WORKDIR /app

# セキュリティ強化: 非rootユーザーの作成
RUN adduser --disabled-password --gecos "" appuser

# アプリケーションコードのコピー
COPY ./app ./app
COPY ./libkoiki ./libkoiki
COPY ./alembic ./alembic
COPY ./alembic.ini ./
COPY ./main.py ./

# Poetry 2.x: Copy dependency files for better Docker layer caching
COPY pyproject.toml poetry.lock README.md ./

# Poetry 2.x: Optimize configuration and installation
RUN mkdir -p $POETRY_CACHE_DIR \
    && poetry config virtualenvs.create false \
    && poetry config installer.parallel true \
    && poetry config installer.max-workers 10 \
    && poetry check --lock \
    && poetry install --no-interaction --no-ansi --no-root \
    && poetry cache clear --all pypi

# docker-entrypoint.shをコピーして実行権限を付与
COPY docker-entrypoint.sh ./
RUN chmod +x /app/docker-entrypoint.sh

# alembic/versionsディレクトリの作成と所有者変更
RUN mkdir -p /app/alembic/versions && chown -R appuser:appuser /app

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]