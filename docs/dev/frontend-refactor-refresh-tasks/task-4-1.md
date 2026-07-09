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

未実施。

