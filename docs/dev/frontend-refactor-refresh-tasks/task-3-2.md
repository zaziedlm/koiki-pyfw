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
- `.github/workflows/frontend-ci.dev-v0.8.yml.disabled`

## 実施手順

1. Vitest と Testing Library を導入する
2. API 境界用に MSW を導入する
3. test setup で React Query provider、Router provider、MSW server を扱える helper を作る
4. `ApiError` 正規化と retry 判定の unit test を追加する
5. auth guard の component test を追加する
6. task query / mutation の代表テストを追加する
7. CSRF invalid response 時に token refresh + 1 回 retry することをテストする
8. dev/v0.8 向け frontend CI 定義に test 実行を追加する
9. Playwright を導入するか、別タスクとして明示的に後続化するかを判断する

## 検証

- `npm test`
- `npm run check-types`
- `npm run lint`
- `npm run build`

## 完了条件

- frontend に自動テストスクリプトが存在する
- 認証・CSRF・task mutation の代表リスクがテストされている
- dev/v0.8 で有効化する frontend CI 定義に frontend tests が含まれている

## 実施結果

完了。

- Vitest, Testing Library, jest-dom, jsdom, MSW を導入した。
- `npm test` / `npm run test:watch` を追加した。
- `vite.config.ts` に Vitest の `jsdom` environment と `src/test/setup.ts` を追加した。
- `src/test/server.ts` に MSW server、`src/test/setup.ts` に MSW lifecycle と Testing Library cleanup、`src/test/render.tsx` に React Query / MemoryRouter provider helper を追加した。
- React Query の retry 判定を unit test しやすくするため、QueryClient factory を `src/lib/react-query-client.ts` に分離した。
- `ApiError` 正規化、CSRF invalid 時の token refresh + 1 回 retry、React Query retry 判定、`AuthGuard` の認証あり/なし、task create mutation の代表テストを追加した。
- dev/v0.8 向け無効化 CI テンプレート `.github/workflows/frontend-ci.dev-v0.8.yml.disabled` に `npm test` を追加した。現時点では `.yml.disabled` のため Actions は発火しない。
- Playwright は今回は導入しない判断にした。現時点の目的は unit/component/API boundary の最小自動テスト基盤であり、E2E は dev/v0.8 での実運用 UI flow 固定後に別タスクで扱う。

検証:

- `npm ci`
- `npm test`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- `git diff --check`

補足:

- sandbox 通常権限の `npm test` / `npm run build` は Vite/esbuild 起動時の `spawn EPERM` に当たるため、昇格実行で成功を確認した。
- `npm test` は 4 files / 8 tests passed。
- `npm run lint` は exit code 0。既存 UI helper export に対する `react-refresh/only-export-components` warning が 3 件残っている。
- `npm ci` 後の npm audit は 7 vulnerabilities を報告したが、依存 audit 対応は本タスク外とした。
