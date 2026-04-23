# Task 2-10: Stage 2 継続実装の総合検証

## 目的

`uv` 実移行が実際の標準経路として成立しているかを、local / CI 観点で最小限検証する。

## 推奨ブランチ

- `topic/uv-validation`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-8](./task-2-8.md)
- [Task 2-9](./task-2-9.md)

## 事前条件

- [Task 2-8](./task-2-8.md) が完了している
- [Task 2-9](./task-2-9.md) が完了している

## 確認観点

- `uv sync` が成立するか
- `uv run pytest --collect-only` が成立するか
- `import libkoiki` と `import koiki_ref_app` が成立するか
- 例外として残る Poetry 依存が明示されているか

## 実施手順

1. `uv sync` を実行する
2. `uv run pytest --collect-only` を実行する
3. `uv run python -c "import libkoiki, koiki_ref_app"` を実行する
4. 必要に応じて代表的な `uv run uvicorn ...` 経路を確認する
5. local と CI のコマンド差分が残っていないか確認する
6. 例外として残る運用があれば、意図的な残置か未回収かを記録する

## 成果物

- Stage 2 継続実装の検証記録
- 残課題一覧

## 検証

- `uv sync` と `uv run` が実際の標準経路として成立している
- import / collect / CI の最小検証が揃っている
- Stage 3 以降を Poetry 前提なしで進められる

## 完了条件

- `uv` 実移行を完了扱いにしてよい判断材料が揃っている

## 次タスク

- Stage 3 以降の実装、または follow-up runtime 検証タスク
