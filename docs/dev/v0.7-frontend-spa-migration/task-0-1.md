# Task 0-1: frontend 責務棚卸し

## 目的

現行 `frontend/` の Next.js 実装が担っている UI 責務と server/BFF 責務を分離して、移行漏れを防ぐ。

## 参照ファイル

- `frontend/src/app/`
- `frontend/src/app/api/`
- `frontend/src/middleware.ts`
- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/lib/cookie-utils.ts`
- `frontend/src/lib/csrf-utils.ts`
- `frontend/src/hooks/`
- `frontend/package.json`

## 事前条件

- `docs/dev/frontend-spa-migration-plan.ja.md` を読んでいる

## 実施手順

1. `frontend/src/app/api/**/route.ts` を一覧化する
2. 各 route handler の backend 移管要否を分類する
3. `next/link`、`next/navigation`、`next/server` 依存箇所を一覧化する
4. browser storage 利用箇所を一覧化する
5. Next.js 削除前に backend parity が必要な処理を抽出する

## 推奨成果物

- route handler ごとの移管表
- UI 移植対象ファイル一覧
- Next.js 依存 API の置換表

## 検証

- API route handler 16 件がすべて分類されている
- Cookie / CSRF / refresh / SSO / SAML の移管先が説明できる

## 完了条件

- Task 0-2 の backend contract 設計に必要な現状情報が揃っている

## 実施結果

未実施。
