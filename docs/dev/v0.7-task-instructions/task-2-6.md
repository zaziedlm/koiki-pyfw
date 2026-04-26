# Task 2-6: root workspace の `uv` メタデータ実装

## 目的

root `pyproject.toml` を Poetry 前提から `uv` workspace 前提へ切り替え、以後の `uv.lock` 生成と CI 切替の土台を作る。

## 推奨ブランチ

- `topic/uv-workspace-activation`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-1](./task-2-1.md)
- [Task 2-2](./task-2-2.md)

## 事前条件

- [Task 2-5](./task-2-5.md) が完了している
- `components/libkoiki` と `components/koiki_ref_app` の現構成が最新状態である

## 確認観点

- root が workspace 実行起点として説明できるか
- `dependency-groups` と `tool.uv.workspace` の責務が衝突していないか
- local package 参照が `tool.uv.sources` に統一できているか
- Poetry 固有設定をどこまで残すかが明示されているか

## 実施手順

1. 現在の root `pyproject.toml` に残っている Poetry 固有設定を棚卸しする
2. `dependency-groups` に移す対象と、`project.optional-dependencies` に残す対象を切り分ける
3. `tool.uv.workspace.members` を現構成に合わせて定義する
4. `tool.uv.sources` で `libkoiki` などの local package 参照を定義する
5. Poetry 固有 group や重複 dependency 記述の整理方針を反映する
6. 変更後の `pyproject.toml` を読み、workspace 起点の説明が通るか確認する

## 成果物

- 更新済み root `pyproject.toml`
- `uv` workspace metadata の反映記録

## 検証

- root `pyproject.toml` に `dependency-groups`、`tool.uv.workspace`、`tool.uv.sources` が入っている
- workspace member が `components/libkoiki` と `components/koiki_ref_app` に一致している
- `uv` 実行起点を root として一貫して説明できる

## 完了条件

- Task 2-7 で `uv lock` を生成できる前提が整っている

## 実施結果

Task:

- Task 2-6: root workspace の `uv` メタデータ実装

変更内容:

- root `pyproject.toml` の Poetry 固有設定を整理した
  - `[tool.poetry]`
  - `[tool.poetry.group.dev]`
  - `[tool.poetry.group.security]`
  - `[tool.poetry.dependencies]`
  - Poetry 用 `[build-system]`
- root の開発 / test / security 依存を `[dependency-groups]` に移した
  - `dev`
  - `test`
  - `security`
- root を `uv` の workspace 実行起点として明示した
  - `[tool.uv] package = false`
  - `[tool.uv.workspace].members`
    - `components/libkoiki`
    - `components/koiki_ref_app`
- local package 参照を `[tool.uv.sources]` に統一した
  - `libkoiki = { workspace = true }`
  - `"koiki-ref-app" = { workspace = true }`
- root runtime dependency に workspace package を明示した
  - `libkoiki`
  - `koiki-ref-app`

未解決事項:

- `components/libkoiki/pyproject.toml` にはまだ Poetry 固有設定が残っている
  - これは Task 2-6 の root workspace metadata 実装範囲外として残した
- `uv.lock` はまだ生成していない
  - Task 2-7 で生成する
- `poetry.lock` はまだ残っている
  - Task 2-7 で `uv.lock` 生成後に扱いを決める
- README、helper script、CI workflow にはまだ Poetry 前提が残っている
  - Task 2-8 / Task 2-9 で更新する

検証結果:

- `uv lock --dry-run` を実行し、root workspace metadata が `uv` に読み取られることを確認した
- dry-run 結果では次の workspace package が解決対象として認識された
  - `koiki-pyfw`
  - `libkoiki`
  - `koiki-ref-app`
- 依存解決は成功し、Task 2-7 で `uv.lock` を生成できる前提が整った
- 実行時に依存先パッケージ由来の invalid version specifier 補正警告が出た
  - root metadata の構文エラーではないため、Task 2-7 の blocker ではない

次タスクへ渡す事項:

- Task 2-7 では `uv lock` を実行し、`uv.lock` を生成する
- Task 2-7 では `poetry.lock` の残置 / 削除方針も合わせて決める
- Task 2-8 / Task 2-9 では、今回導入した `dependency-groups` と `tool.uv.workspace` を標準経路として docs / CI に反映する

## 次タスク

- [Task 2-7](./task-2-7.md)
