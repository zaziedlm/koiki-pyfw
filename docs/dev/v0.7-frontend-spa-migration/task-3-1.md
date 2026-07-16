# Task 3-1: Next.js server surface removal

## 目的

backend parity と SPA 移行が完了した後、Next.js 固有の server surface を削除する。

## 事前条件

- Task 1-4 が完了している
- Task 2-4 が完了している

## 対象

- `frontend/src/app/api/`
- `frontend/src/middleware.ts`
- `frontend/next.config.ts`
- `frontend/next-env.d.ts`
- `next`, `eslint-config-next`, `next-themes` など不要依存
- `next/link`, `next/navigation`, `next/server` import

## 実施手順

1. Next.js route handler が呼ばれていないことを `rg` で確認する
2. `src/app/api/` を削除する
3. `middleware.ts` を削除する
4. Next.js config と env 型ファイルを削除する
5. package dependencies から Next.js 関連を削除する
6. lockfile を更新する
7. ESLint / TypeScript 設定から Next.js plugin を削除する

## 検証

- `rg "next/" frontend/src` が migration 対象外を除き 0 件
- `npm run check-types`
- `npm run build`

## 完了条件

- `frontend/` が Next.js runtime を必要としない

## 実施結果

実施済み。

- SPA 側が Next.js route handler を呼んでいないことを `rg` で確認した。
- `frontend/src/app/api/` 配下の Next.js route handler を削除した。
- `frontend/src/middleware.ts` を削除した。
- `frontend/next.config.ts` を削除した。
- Next.js server helper だった `frontend/src/lib/cookie-utils.ts` と `frontend/src/lib/csrf-utils.ts` を削除した。
- Next.js App Router root layout だった `frontend/src/app/layout.tsx` を削除した。
- `next`、`next-themes`、`eslint-config-next` を package dependencies から削除し、lockfile を更新した。
- `frontend/tsconfig.json` から Next.js plugin / `.next` 型 include / `next-env.d.ts` include を削除した。
- `frontend/eslint.config.mjs` から Next.js ESLint preset を削除した。
- `frontend/src/components/ui/sonner.tsx` を `next-themes` 依存から既存 UI store の theme 参照へ変更した。

検証:

- `rg "next/|NextRequest|NextResponse|next-themes|eslint-config-next|next/core-web-vitals|next/typescript" frontend/src frontend/package.json frontend/tsconfig.json frontend/eslint.config.mjs`
- `rg "src/app/api|/api/auth|/api/sso|/api/saml|/api/todos|/api/users" frontend/src`
- `rg '"next"|next-themes|eslint-config-next|@next/' frontend/package-lock.json frontend/package.json`
- `npm run check-types`
- `npm run lint`
- `npm run build`

補足:

- `frontend/README.md` と Dockerfile 類には Next.js 時代の記述や build 前提が残っている。Docker / environment 移行は Task 3-2 で扱う。
- Vite build は sandbox 内では esbuild の `spawn EPERM` で失敗するため、昇格実行で確認した。
