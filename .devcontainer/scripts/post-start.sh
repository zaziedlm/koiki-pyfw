#!/bin/sh

set -u

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"
DB_WAIT_INTERVAL="${DB_WAIT_INTERVAL:-2}"
MIGRATION_MAX_ATTEMPTS="${MIGRATION_MAX_ATTEMPTS:-3}"
MIGRATION_RETRY_DELAY="${MIGRATION_RETRY_DELAY:-3}"
DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://koiki_user:koiki_password@${DB_HOST}:${DB_PORT}/koiki_todo_db}"

wait_for_db() {
  deadline=$(( $(date +%s) + DB_WAIT_TIMEOUT ))
  attempt=1

  while ! python3 -c \
    'import socket, sys; socket.create_connection((sys.argv[1], int(sys.argv[2])), 2).close()' \
    "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "ERROR: database ${DB_HOST}:${DB_PORT} is unreachable after ${DB_WAIT_TIMEOUT}s" >&2
      return 1
    fi

    echo "Waiting for database ${DB_HOST}:${DB_PORT} (attempt ${attempt})..."
    attempt=$((attempt + 1))
    sleep "$DB_WAIT_INTERVAL"
  done

  echo "Database ${DB_HOST}:${DB_PORT} is reachable."
}

run_migrations() {
  attempt=1

  while [ "$attempt" -le "$MIGRATION_MAX_ATTEMPTS" ]; do
    echo "Running database migrations (attempt ${attempt}/${MIGRATION_MAX_ATTEMPTS})..."

    if DATABASE_URL="$DATABASE_URL" uv run --directory /workspace \
      alembic -c components/koiki_ref_app/alembic.ini upgrade head; then
      echo "Database migrations completed."
      return 0
    else
      status=$?
    fi

    if [ "$attempt" -eq "$MIGRATION_MAX_ATTEMPTS" ]; then
      echo "ERROR: database migrations failed after ${MIGRATION_MAX_ATTEMPTS} attempts" >&2
      return "$status"
    fi

    echo "Migration attempt ${attempt} failed; retrying in ${MIGRATION_RETRY_DELAY}s..." >&2
    attempt=$((attempt + 1))
    sleep "$MIGRATION_RETRY_DELAY"
  done
}

wait_for_db && run_migrations
