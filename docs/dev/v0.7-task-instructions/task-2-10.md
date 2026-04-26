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

## 実施結果

Task:

- Task 2-10: Stage 2 継続実装の総合検証

変更内容:

- Task 2-6 から Task 2-9 の実装結果を前提に、local / CI の `uv` 標準経路を検証した
- CI 切替後に `poetry.lock` を削除し、lockfile 正本を `uv.lock` に一本化した

検証結果:

- `uv sync --locked --group dev --group test`
  - 成功
  - `components/libkoiki` と `components/koiki_ref_app` が workspace package として build / install された
- `uv run pytest --collect-only`
  - 成功
  - 279 tests collected
- `uv run python -c "import libkoiki, koiki_ref_app"`
  - 成功
  - `libkoiki` と `koiki_ref_app` の import を確認した
- `uv run python -c "from koiki_ref_app.asgi import app; print(app.title)"`
  - `.env` の `DEBUG=release` により失敗
  - これは `uv` 移行ではなく既存の環境変数値が boolean として不正な問題
- `DEBUG=false uv run python -c "from koiki_ref_app.asgi import app; print(app.title)"`
  - 成功
  - `koiki_ref_app.asgi:app` の import を確認した

残課題:

- `.env` の `DEBUG=release` は `libkoiki.core.config.Settings.DEBUG` の bool parsing に失敗する
  - local runtime 確認では `DEBUG=false` など boolean 値で上書きが必要
  - `.env` の値修正は uv 移行とは別タスクとして扱う
- `components/libkoiki/pyproject.toml` には Poetry 固有設定が残っている
  - root dependency workflow からは外れたが、component build backend の整理余地は残る
- GitHub Actions の実行結果は push / PR 後に確認する必要がある

完了判定:

- root workspace metadata、`uv.lock`、local docs、helper script、CI workflow は `uv` 標準経路に切り替わった
- local の `uv sync` / collect / import 検証は成立した
- Stage 2 継続実装は完了扱いにできる

## 次タスク

- Stage 3 以降の実装、または follow-up runtime 検証タスク
