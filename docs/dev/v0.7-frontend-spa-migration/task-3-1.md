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

未実施。
