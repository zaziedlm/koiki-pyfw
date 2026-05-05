# Task 5-6: `apps/` 導入

## 目的

案件固有アプリケーションのための予約領域をトップレベルへ導入し、`components/` との責務境界を物理構成でも明示する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-4-3.md`
- `docs/dev/v0.7-task-instructions/task-4-4.md`
- `apps/README.md`

## 事前条件

- [Task 5-5](./task-5-5.md) が完了している

## 確認観点

- `apps/` のトップレベル導入
- `components/` との責務境界
- downstream 向け命名 / 配置ルール
- root `frontend/` と案件固有 frontend の棲み分け

## 実施手順

1. top-level `apps/` を追加する
2. placeholder として `apps/README.md` を作成する
3. `components/` と `apps/` の依存方向を明文化する
4. 推奨レイアウトと運用ルールを記録する

## 成果物

- `apps/` ディレクトリ
- `apps/README.md`

## 検証

- `apps/` がトップレベルに存在する
- `components/` と `apps/` の境界説明が `README` で可能

## 完了条件

- Task 5-7 で test 実移設に進める

## 実施結果

Task:

- Task 5-6: `apps/` 導入

変更内容:

- top-level に `apps/` を追加した
- `apps/README.md` を作成し、次を明文化した
  - `apps/` は downstream の案件固有アプリ配置先
  - `components/` は upstream の reusable framework / starter template 配置先
  - 依存方向は `apps/ -> components/` のみ
  - 推奨レイアウトは `apps/<project-slug>/backend|frontend|shared|ops`
  - root `frontend/` は starter template であり、案件固有 frontend は `apps/<project-slug>/frontend` に置く
  - `apps/` は root Python workspace member に含めない

未解決事項:

- 実案件がまだ存在しないため、`apps/<project-slug>/...` の具体例は placeholder のみ
- `uv workspace` の実導入時に `apps/` を member に含めない設定を Stage 6 以降で実ファイルへ反映する必要がある

検証結果:

- `apps/README.md` により `components/` と `apps/` の境界説明が可能になった
- top-level に `apps/` が存在する状態になった

次タスクへ渡す事項:

- Task 5-7 では `tests/unit/app` と `tests/integration/app` を `components/koiki_ref_app/tests` 側へ実移設する
- Stage 6 では docs / CI / workspace 設定に `apps/` 非member前提を反映する

## 次タスク

- [Task 5-7](./task-5-7.md)
