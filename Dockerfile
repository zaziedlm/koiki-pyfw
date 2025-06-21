# Dockerfile
FROM python:3.11.7-slim

# 環境変数の設定
ENV POETRY_VERSION=2.1.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
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

# 依存関係のインストール
COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

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