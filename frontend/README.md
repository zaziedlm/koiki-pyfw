# KOIKI Frontend

Vite + React SPA for the KOIKI reference application.

The frontend calls the FastAPI backend directly with `credentials: "include"` and uses backend-managed Cookie session endpoints. It does not run a BFF or Next.js server runtime.

See `docs/frontend-spa-implementation-guide.ja.md` for current implementation guidance.

## Local Development

```bash
npm install
npm run dev
```

Open http://localhost:3000.

The default local API endpoint is:

```text
http://localhost:8000/api/v1
```

Override it in `.env.local` when needed:

```env
VITE_API_URL=http://localhost:8000
VITE_API_PREFIX=/api/v1
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Build And Preview

```bash
npm run check-types
npm run lint
npm run build
npm run preview
```

`npm run build` outputs static files to `dist/`.

## Docker

Production Docker builds compile the SPA with Vite and serve `dist/` through unprivileged nginx on container port `8080`.
Docker Compose publishes it as host port `3000`.

```bash
docker compose up --build frontend
```

For local Docker Compose, the browser still reaches the backend through the host-published backend port, so `.env.docker` defaults to:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Choose a different build-time env file with:

```bash
FRONTEND_BUILD_ENV_FILE=.env.production docker compose build frontend
```

React Router deep links are handled by nginx fallback to `/index.html`, so routes such as `/dashboard` can be refreshed directly.

## Environment Ownership

Frontend `VITE_*` variables are public browser configuration and are embedded at build time.

Keep in frontend:

- `VITE_API_URL`
- `VITE_API_PREFIX`
- `VITE_API_BASE_URL`
- `VITE_SSO_REDIRECT_URI`
- `VITE_SAML_REDIRECT_URI`
- `VITE_APP_NAME`
- `VITE_APP_VERSION`

Backend-owned settings:

- CORS allowed origins
- Cookie names
- Cookie `SameSite` / `Secure`
- CSRF cookie/header names and validation
- Security headers

Removed from frontend runtime:

- `NEXT_PUBLIC_*`
- `BACKEND_API_URL`
- `BACKEND_API_PREFIX`
- `NEXT_TELEMETRY_DISABLED`
- `NODE_ENV` in env files

## Validation

Use these checks before committing frontend infrastructure changes:

```bash
npm ci
npm test
npm run check-types
npm run lint
npm run build
```

Frontend CI is staged in `.github/workflows/frontend-ci.dev-v0.8.yml.disabled` and is intentionally disabled until the React SPA refresh is adopted by `dev/v0.8`.
