# Legacy Next.js Frontend

The React/Vite implementation is now built from `frontend/src/react-app`. The preceding Next.js application remains recoverable from Git history and from the parent branch `dev/v0.7-react-only`.

For comparison or migration work, retrieve the `frontend/` directory from the parent branch into a separate worktree or temporary directory. Do not overwrite the active `frontend/` directory in this branch.

Do not include `frontend-old/` in the Vite TypeScript scope or production image. It is a migration reference only; the active frontend is `frontend/`.
