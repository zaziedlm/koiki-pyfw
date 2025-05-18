# Dockerfile
FROM python:3.11.7-slim

# poetryのインストール
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV_CREATE=false
ENV POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION \
    && poetry --version

WORKDIR /app

# 依存関係のインストール
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

# アプリケーションコードのコピー
COPY ./app ./app
COPY ./libkoiki ./libkoiki
COPY ./alembic ./alembic
COPY ./alembic.ini ./
COPY ./main.py ./

# Uvicornのデフォルトポート
EXPOSE 8000

# デフォルトコマンド (docker-compose で上書き可能)
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]