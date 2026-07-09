# Task 3-2: frontend test baseline

## 目的

frontend の自動テスト基盤を導入し、認証・CSRF・Query・主要 UI 操作を最小スコープで検証できるようにする。

## 事前条件

- Task 1-2 が完了している
- Task 2-1 が完了している
- Task 3-1 が完了していることが望ましい

## 対象

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/src/**/*.test.ts`
- `frontend/src/**/*.test.tsx`
- `frontend/src/test/`（新設想定）
- `.github/workflows/ci.yml`

## 実施手順

1. Vitest と Testing Library を導入する
2. API 境界用に MSW を導入する
3. test setup で React Query provider、Router provider、MSW server を扱える helper を作る
4. `ApiError` 正規化と retry 判定の unit test を追加する
5. auth guard の component test を追加する
6. task query / mutation の代表テストを追加する
7. CSRF invalid response 時に token refresh + 1 回 retry することをテストする
8. CI frontend job に test 実行を追加する
9. Playwright を導入するか、別タスクとして明示的に後続化するかを判断する

## 検証

- `npm test`
- `npm run check-types`
- `npm run lint`
- `npm run build`

## 完了条件

- frontend に自動テストスクリプトが存在する
- 認証・CSRF・task mutation の代表リスクがテストされている
- CI で frontend tests が実行される

## 実施結果

未実施。

