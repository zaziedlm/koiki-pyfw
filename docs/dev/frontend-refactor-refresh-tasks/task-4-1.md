# Task 4-1: implementation guide and final validation

## 目的

刷新後の frontend 構造を、今後の業務 UI 実装者向けの指針ガイドとして文書化し、最終検証を行う。

## 事前条件

- Task 1-1 から Task 3-2 までが完了している

## 対象

- `docs/dev/frontend-refactor-refresh-plan.ja.md`
- `docs/dev/frontend-refactor-refresh-tasks/`
- `frontend/README.md`
- 新設する frontend implementation guide
- 必要に応じて `docs/agent/app.md`

## 実施手順

1. 実装後の実ディレクトリ構成を棚卸しする
2. frontend の設計思想を記述する
   - backend API 志向の SPA
   - Cookie session / CSRF boundary
   - TanStack Query server state
   - Zustand client state
   - feature-based module structure
3. 新規画面を追加する手順を記述する
4. 新規 API endpoint を frontend から利用する手順を記述する
5. form、validation、mutation、notification の標準パターンを記述する
6. テスト追加基準を記述する
7. 旧 Next.js 時代の stale guide が残っていれば整理対象にする
8. 全検証コマンドを実行し、結果を記録する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm test`
- `npm run build`
- 必要に応じて backend 起動込みの login -> task CRUD -> logout 手動確認

## 完了条件

- frontend implementation guide が作成されている
- 新規業務 UI 実装時の配置・API・Query・テスト方針が明確である
- 既存の stale frontend docs と矛盾がない、または矛盾が明示されている
- 全タスクの `実施結果` が更新されている

## 実施結果

完了。

- 現行 `frontend/src/` の実ディレクトリ構成を棚卸しした。
- `docs/frontend-spa-implementation-guide.ja.md` を新設し、Vite + React SPA としての実装指針を文書化した。
- guide には routing、backend API 利用、Cookie session / CSRF boundary、TanStack Query / Zustand の責務分離、form / validation / mutation / notification、testing、CI 有効化方針を記載した。
- `frontend/README.md` から現行 SPA guide へ誘導し、validation command に `npm ci` / `npm test` を追加した。
- 旧 `docs/frontend-application-development-guide.md` は Next.js 15 / App Router / BFF 前提の historical guide と明示し、現行実装では新 SPA guide を参照するよう注意書きを追加した。
- `docs/dev/frontend-refactor-refresh-plan.ja.md` の完了条件を、frontend CI は dev/v0.8 で有効化する deferred 状態に合わせて更新した。

残タスク整理:

- 実装タスクとしては Task 4-1 で一連の frontend refresh task は完了。
- dev/v0.8 作成時に `.github/workflows/frontend-ci.dev-v0.8.yml.disabled` の frontend job を既存 `.github/workflows/ci.yml` へ統合する。
- Playwright による login -> task CRUD -> logout E2E は後続候補。
- `react-refresh/only-export-components` warning の解消は、必要なら UI helper 分離の小 cleanup として扱う。
- 旧 Next.js guide の削除または historical docs 配下への移動は後続候補。

検証:

- `npm run check-types`
- `npm run lint`
- `npm test`
- `npm run build`

補足:

- `npm run lint` は exit code 0。既存 UI helper export に対する `react-refresh/only-export-components` warning が 3 件残っている。
- `npm test` は 4 files / 8 tests passed。
- `npm run build` は成功し、500k chunk warning は出ていない。最大 chunk は `441.26 kB`。
- `npm test` / `npm run build` は sandbox 通常権限では Vite/esbuild の `spawn EPERM` に当たるため、昇格実行で成功を確認した。
- backend 起動込みの login -> task create/update/delete は Task 2-3 後にコンテナ上で手動確認済み。logout も app log 上で成功を確認済み。
