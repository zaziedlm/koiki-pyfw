# Legacy Next.js Frontend

The React/Vite implementation is now built from `frontend/src/react-app`. The preceding Next.js application remains recoverable from Git history and from the parent branch `dev/v0.7-react-only`.

To restore the legacy frontend into this directory for comparison or migration work:

```bash
git checkout dev/v0.7-react-only -- frontend
git mv frontend frontend-old
```

Do not include `frontend-old/` in the Vite TypeScript scope or production image. It is a migration reference only; the active frontend is `frontend/`.
