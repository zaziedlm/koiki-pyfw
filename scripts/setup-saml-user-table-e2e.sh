#!/bin/bash
set -euo pipefail

SKIP_VOLUME_RESET="${SKIP_VOLUME_RESET:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"

echo "[INFO] Preparing SAML user-table E2E environment..."

if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[INFO] .env created from .env.example (base settings)"
  else
    echo "[ERROR] .env and templates are missing."
    exit 1
  fi

  if [ -f ".env.saml.example" ]; then
    echo "[INFO] Merging SAML-related settings from .env.saml.example"
    while IFS= read -r line; do
      case "$line" in
        SAML_*=*|SSO_LINK_BACKEND=*)
          key="${line%%=*}"
          value="${line#*=}"
          case "$key" in
            SAML_IDP_X509_CERT|SAML_SP_X509_CERT|SAML_SP_PRIVATE_KEY)
              # Skip multiline certificate placeholders
              continue
              ;;
          esac

          if grep -q "^${key}=" .env; then
            sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
          else
            echo "${key}=${value}" >> .env
          fi
          ;;
      esac
    done < .env.saml.example
  fi
fi

ensure_env_value() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" .env; then
    echo "${key}=${value}" >> .env
    return
  fi
  local current
  current="$(grep -E "^${key}=" .env | head -n1 | cut -d'=' -f2- || true)"
  if [ -z "$current" ]; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
  fi
}

ensure_env_value POSTGRES_SERVER db
ensure_env_value POSTGRES_USER koiki_user
ensure_env_value POSTGRES_PASSWORD koiki_password
ensure_env_value POSTGRES_DB koiki_todo_db
ensure_env_value POSTGRES_PORT 5432
ensure_env_value DATABASE_URL postgresql+asyncpg://koiki_user:koiki_password@db:5432/koiki_todo_db

if grep -q '^SSO_LINK_BACKEND=' .env; then
  sed -i.bak 's/^SSO_LINK_BACKEND=.*/SSO_LINK_BACKEND=user_table/' .env
else
  echo 'SSO_LINK_BACKEND=user_table' >> .env
fi
echo "[INFO] Set SSO_LINK_BACKEND=user_table in .env"

POSTGRES_USER_VALUE="$(grep -E '^POSTGRES_USER=' .env | head -n1 | cut -d'=' -f2- || true)"
POSTGRES_DB_VALUE="$(grep -E '^POSTGRES_DB=' .env | head -n1 | cut -d'=' -f2- || true)"
POSTGRES_USER_VALUE="${POSTGRES_USER_VALUE:-koiki_user}"
POSTGRES_DB_VALUE="${POSTGRES_DB_VALUE:-koiki_todo_db}"

if [ "$SKIP_VOLUME_RESET" != "true" ]; then
  echo "[INFO] Stopping containers and removing volumes..."
  docker compose down -v --remove-orphans
fi

UP_ARGS=(compose up -d)
if [ "$SKIP_BUILD" != "true" ]; then
  UP_ARGS+=(--build)
fi
UP_ARGS+=(db keycloak app frontend)

echo "[INFO] Starting stack: docker ${UP_ARGS[*]}"
docker "${UP_ARGS[@]}"

echo "[INFO] Waiting for PostgreSQL readiness..."
for i in $(seq 1 90); do
  if docker compose exec -T db pg_isready -U "$POSTGRES_USER_VALUE" -d "$POSTGRES_DB_VALUE" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" -eq 90 ]; then
    echo "[ERROR] PostgreSQL did not become ready in time."
    exit 1
  fi
done

echo "[INFO] Running Alembic migrations inside app container..."
docker compose exec -T app alembic upgrade head

echo "[INFO] Verifying migration state (alembic_version)..."
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER_VALUE" -d "$POSTGRES_DB_VALUE" -c "SELECT version_num FROM alembic_version;"

echo "[INFO] Creating temporary \"user\" table for user_table backend..."
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER_VALUE" -d "$POSTGRES_DB_VALUE" < scripts/sql/create_user_table_for_sso.sql

echo "[INFO] Verifying \"user\" table columns..."
docker compose exec -T db psql -U "$POSTGRES_USER_VALUE" -d "$POSTGRES_DB_VALUE" -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='user' ORDER BY ordinal_position;"

echo
echo "[DONE] E2E setup completed."
echo "  - Frontend: http://localhost:3000"
echo "  - Backend : http://localhost:8000"
echo "  - Keycloak: http://localhost:8090 (admin/admin)"
echo
echo "SAML test users (realm-saml.json):"
echo "  - saml-user / Passw0rd!"
echo "  - saml-admin / AdminPass123!"
echo "  - saml-test / TestPass123!"
