#!/bin/bash
set -e

ALEMBIC_INI="/app/components/koiki_ref_app/alembic.ini"
ALEMBIC_VERSIONS_DIR="/app/components/koiki_ref_app/alembic/versions"

# リトライ関数定義
function retry {
  local retries=$1
  shift
  local count=0
  until "$@"; do
    exit=$?
    count=$((count + 1))
    if [ $count -lt $retries ]; then
      echo "コマンド '$@' が失敗しました。$count/$retries回目。再試行..."
      sleep 2
    else
      echo "コマンド '$@' が$retries回失敗しました。終了します。"
      return $exit
    fi
  done
  return 0
}

# データベース接続チェック
echo "データベースへの接続を確認中..."
retry 30 python -c "
import psycopg2
import os
from urllib.parse import urlparse
import time

# DATABASE_URLを解析
db_url = os.environ.get('DATABASE_URL', '')
if '+asyncpg' in db_url:
    db_url = db_url.replace('+asyncpg', '')
parts = urlparse(db_url)
user = parts.username
password = parts.password
host = parts.hostname
port = parts.port or 5432
dbname = parts.path[1:]

# 接続を試行
psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)
print('データベース接続成功')
"

# Alembic versionsディレクトリの存在確認と作成
if [ ! -d "$ALEMBIC_VERSIONS_DIR" ]; then
    echo "Alembic versionsディレクトリを作成します..."
    mkdir -p "$ALEMBIC_VERSIONS_DIR"
    chown -R appuser:appuser "$ALEMBIC_VERSIONS_DIR"
fi

# マイグレーション実行
echo "データベースマイグレーションを実行中..."
alembic -c "$ALEMBIC_INI" upgrade head || {
    echo "マイグレーション実行中にエラーが発生しました。"
    echo "alembicリビジョンの状態確認..."
    alembic -c "$ALEMBIC_INI" current
    
    echo "マイグレーションファイルが存在しない場合、初期マイグレーションを作成します..."
    if [ -z "$(ls -A "$ALEMBIC_VERSIONS_DIR")" ]; then
        echo "初期マイグレーションを作成..."
        alembic -c "$ALEMBIC_INI" revision --autogenerate -m "initial_migration"
        echo "マイグレーション実行..."
        alembic -c "$ALEMBIC_INI" upgrade head
    fi
}

echo "マイグレーション完了。アプリケーション起動準備完了。"

# メイン実行コマンドの受け渡し
exec "$@"
