# Task 3-2: Docker / environment migration

## 目的

frontend の Docker、compose、env、README を Vite SPA 構成に合わせる。

## 事前条件

- Task 3-1 が完了している

## 対象

- `frontend/Dockerfile`
- `frontend/Dockerfile.unified`
- `docker-compose.yml`
- `docker-compose.unified.yml`
- `frontend/.env.local.example`
- `frontend/.env.production.example`
- `frontend/.env.docker`
- `frontend/README.md`

## 実施手順

1. production build を `vite build` 前提にする
2. Task 0-2 の same-origin / cross-origin 方針に従って serving 構成を更新する
3. healthcheck を `/api/health` 依存から変更する
4. React Router の deep link / reload に備えて `/index.html` fallback を設定する
5. env mapping 表に従って環境変数を移行する
   - `VITE_*` に残すもの
   - backend setting へ移すもの
   - 削除するもの
6. compose の frontend environment を更新する
7. unified compose の frontend profiles を更新する
8. README を Next.js 初期文面から SPA 実装説明へ更新する

## 検証

- Docker build が成功する
- compose 起動時に frontend healthcheck が通る
- README の起動手順でローカル起動できる
- `/dashboard` などの SPA route を直接開いても `/index.html` fallback により表示できる
- `docker-compose.yml` と `docker-compose.unified.yml` の frontend 設定が矛盾していない

## 完了条件

- ローカルと Docker の frontend 起動方法が Vite SPA と一致している
- env variable の移行先が `VITE_*` / backend setting / removed のいずれかに分類されている

## 実施結果

実施済み。

- `frontend/Dockerfile` と `frontend/Dockerfile.unified` を Vite build + nginx static SPA serving 構成に変更した。
- production runner は `dist/` を `/usr/share/nginx/html` に配置し、nginx で port `3000` を listen する。
- `frontend/docker/nginx.conf` を追加し、`/health` と React Router deep link 用の `/index.html` fallback を設定した。
- Docker healthcheck を Next.js `/api/health` 依存から nginx `/health` へ変更した。
- dev target / compose dev command を Vite dev server 前提の `npm run dev` に変更した。
- `docker-compose.yml` の frontend を build-time `FRONTEND_BUILD_ENV_FILE` 前提に整理し、runtime `NEXT_PUBLIC_*` override を削除した。
- `docker-compose.dev.yml` と `docker-compose.unified.yml` の frontend env / healthcheck / command を Vite 前提へ更新した。
- compose frontend healthcheck は container 内の IPv6 `localhost` 解決差異を避けるため `127.0.0.1` を使う。
- `frontend/.env.local.example`、`frontend/.env.production.example`、`frontend/.env.docker` を `VITE_*` 中心に整理した。
- `frontend/src/lib/config.ts` から `NEXT_PUBLIC_*` fallback と frontend 側 Cookie 設定を削除した。
- local Docker で `localhost` / `127.0.0.1` のどちらから開いても Cookie/CSRF の host がずれないよう、absolute local API URL は browser host に揃える。
- `frontend/README.md` を Vite SPA / Docker / env ownership の説明へ更新した。
- `frontend/.dockerignore` の build output コメントを framework-neutral にした。
- Full-stack browser validation で CORS preflight が 400 になる問題を確認し、`BACKEND_CORS_ORIGINS` を exact origin 文字列として扱うよう backend 設定を修正した。

Env migration:

| Classification | Variables |
| --- | --- |
| `VITE_*` in frontend | `VITE_API_URL`, `VITE_API_PREFIX`, `VITE_API_BASE_URL`, `VITE_SSO_REDIRECT_URI`, `VITE_SAML_REDIRECT_URI`, `VITE_APP_NAME`, `VITE_APP_VERSION` |
| Backend settings | CORS allowed origins, Cookie names, Cookie `SameSite` / `Secure`, CSRF cookie/header names and validation, security headers |
| Removed from frontend runtime | `NEXT_PUBLIC_*`, `BACKEND_API_URL`, `BACKEND_API_PREFIX`, `NEXT_TELEMETRY_DISABLED`, `NODE_ENV` in env files |

検証:

- `npm run check-types`
- `npm run lint`
- `npm run build`
- `docker compose config --quiet`
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet`
- `docker compose -f docker-compose.unified.yml --profile dev config --quiet`
- `docker build --target runner -t koiki-frontend-spa:test ./frontend`
- Built image runtime check:
  - `/health` -> HTTP 200, `ok`
  - `/dashboard` -> HTTP 200 via nginx SPA fallback
  - Docker health status -> `healthy`
- Full-stack container check:
  - backend `app` image rebuild -> success
  - backend startup CORS origins -> `http://localhost:3000`, `http://127.0.0.1:3000`
  - CORS preflight:
    - `OPTIONS /api/v1/auth/session/login` from `http://localhost:3000` -> HTTP 200
    - `OPTIONS /api/v1/auth/session/me` from `http://127.0.0.1:3000` -> HTTP 200
  - frontend `/health` from host -> HTTP 200, `ok`
  - direct CSRF + login request with matching cookie/header -> CSRF passes; invalid credentials returns HTTP 401 instead of CSRF HTTP 403

補足:

- Vite `VITE_*` values are build-time browser configuration. Production container runtime env does not rewrite the already-built SPA.
- Local Docker Compose uses `http://localhost:8000/api/v1` as the browser-facing backend URL because the browser cannot resolve the internal compose service name `app`.
- Same-origin production can set `VITE_API_BASE_URL=/api/v1` at build time when a reverse proxy serves frontend and backend under one origin.
- Docker build showed npm audit warnings inside the container with npm 10, but local `npm audit` and `npm audit --omit=dev` both reported 0 vulnerabilities for the same lockfile.
