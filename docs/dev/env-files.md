# Environment File Inventory

This project keeps real environment files out of Git and tracks only templates
or CI-safe files.

## Backend / Root Files

| File | Tracked | Role | Create from / Used by | Status |
|---|---:|---|---|---|
| `.env` | no | Local Docker/development runtime settings | Copy from `.env.example`; used by `docker-compose.yml`, `docker-compose.dev.yml`, and unified dev/optimized profiles | Active local file |
| `.env.example` | yes | Local development template | Source for `.env` | Active template |
| `.env.production` | no | Backend production runtime settings for local production-profile checks | Copy from `.env.production.example`; used by unified `prod` and `prod-external` via `ENV_FILE=.env.production` | Active local file |
| `.env.production.example` | yes | Backend production/AWS-oriented template with placeholders only | Source for `.env.production`; values should usually become ECS task env/secrets in AWS | Active template |
| `.env.ci` | yes | CI-safe backend test settings | Referenced by GitHub Actions and DB integration helper as `ENV_FILE=.env.ci` | Active CI file |
| `.env.saml.example` | yes | SAML-specific overlay/template | Copy or merge into `.env` when testing SAML settings | Active feature template |
| `.env.test` | no | Local ad-hoc test env file, if needed | Copy from `.env.test.example` | Local-only |
| `.env.test.example` | yes | Optional file-based test template | Source for local `.env.test`; current pytest fixtures mostly set test env directly | Optional template |

## Frontend Files

| File | Tracked | Role | Create from / Used by | Status |
|---|---:|---|---|---|
| `frontend/.env.local` | no | Local Vite SPA build-time settings | Copy from `frontend/.env.local.example` | Active local file |
| `frontend/.env.local.example` | yes | Local frontend development template | Source for `frontend/.env.local` | Active template |
| `frontend/.env.docker` | yes | Local Docker SPA build defaults | Used as the default frontend Docker build env | Active local-Docker template |
| `frontend/.env.production` | no | Frontend production build settings | Copy from `frontend/.env.production.example`; select it with `FRONTEND_BUILD_ENV_FILE` | Active local file |
| `frontend/.env.production.example` | yes | Frontend production/AWS-oriented template | Source for `frontend/.env.production` | Active template |

## Important Notes

- Backend Docker image builds do not require `.env.production`; runtime Compose profiles do.
- Vite exposes only `VITE_*` variables to browser code and embeds their values at build time.
  A running static SPA container does not read or rewrite those values. Use
  `FRONTEND_BUILD_ENV_FILE=.env.production` when building a production frontend image.
- Keep browser-visible API URL and callback-path values in frontend `VITE_*` variables.
  Keep Cookie names, Cookie attributes, CORS, CSRF, and security headers in backend settings.
- In AWS/ECS, prefer task definition environment variables and secrets over copying
  `.env.production` into the image or committing real values.
- `ENV_FILE` is primarily a Docker Compose/script selector. The Pydantic settings
  classes still default to `.env`, while CI passes critical values such as
  `DATABASE_URL` directly through process environment variables.
