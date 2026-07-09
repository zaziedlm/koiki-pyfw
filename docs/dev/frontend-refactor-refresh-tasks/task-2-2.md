# Task 2-2: routing and Next.js residue cleanup

## 目的

Vite + React SPA として routing を整理し、Next.js App Router と誤認させる残骸を削除または改名する。

## 事前条件

- Task 0-1 が完了している
- Task 0-2 で router version baseline が確定している
- Task 2-1 と並行する場合は import 移動の競合に注意する

## 対象

- `frontend/src/App.tsx`
- `frontend/src/app/**`
- `frontend/src/routes/`（新設想定）
- `frontend/.next`
- `frontend/tsconfig.tsbuildinfo`
- `frontend/src/**/*.tsx`

## 実施手順

1. React Router の route 定義を `App.tsx` から `routes` module へ分離する
2. protected layout route を導入し、各 page が `ProtectedRoute` と `DashboardLayout` を個別に重ねる構造を減らす
3. route-level lazy loading を導入する
4. `src/app/**/page.tsx` を React SPA 用の明確な命名へ移すか、`src/app` の意味を文書化する
5. 効果を持たない `'use client'` を削除する。ただし shadcn/ui 由来で再生成される可能性があるものは方針を明記する
6. `src/app/api/**` の空ディレクトリを削除する
7. `.next/`、`tsconfig.tsbuildinfo` など生成物の扱いを `.gitignore` と実ファイルで確認する

## 検証

- `rg "use client|src/app/api|next/" frontend/src frontend/package.json frontend/tsconfig.json`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- deep link refresh が Docker/nginx fallback と矛盾しないことを確認する

## 完了条件

- ルート定義が集約され、画面追加時の入口が明確である
- Next.js App Router の実行規約と誤認される構造が整理されている
- initial bundle の chunk size warning が解消、または明示的な判断付きで残されている

## 実施結果

未実施。
