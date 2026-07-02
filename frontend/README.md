# KOIKI React Frontend

`frontend/` is a small React 19 + TypeScript + Vite application. It deliberately uses React state, hooks, browser `fetch`, and native HTML controls rather than Next.js, React Query, an application state store, or a UI component framework.

## Important architecture decision

React Server Components require an RSC-capable server/runtime. A standalone Vite SPA does not provide that runtime, so this frontend intentionally uses ordinary client-side React components. Server-side security work remains in FastAPI.

## Authentication boundary

The browser does **not** receive a JWT or refresh token in JavaScript.

1. React calls `/api/v1/auth/browser/csrf` to receive the readable half of a double-submit CSRF token.
2. Password, OIDC SSO, or SAML completion calls `/api/v1/auth/browser/*`.
3. FastAPI reuses the existing authentication services and writes access/refresh tokens only as HttpOnly cookies.
4. Todo requests use the same origin and include a matching CSRF header for every unsafe request.
5. Bearer-token APIs stay available unchanged for API clients and integrations.

During development Vite proxies `/api` to `http://app:8000`. In optimized/production Compose profiles nginx serves static assets and proxies `/api` to the FastAPI service. This keeps browser requests same-origin and avoids exposing internal tokens to the React bundle.

## Commands

```bash
npm install
npm run dev
npm run check-types
npm run build
```

The old Next.js sources remain outside this build's TypeScript include path. They are retained in Git history; see `../frontend-old/README.md` for recovery guidance.
