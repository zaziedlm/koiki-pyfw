# Task 6-2: CI path 更新

## 目的

component 単位の検証に CI を追随させ、旧 `master/develop` と旧 test path 前提を外す。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `.github/workflows/ci.yml`
- `pyproject.toml`

## 事前条件

- [Task 6-1](./task-6-1.md) が完了している

## 確認観点

- CI の branch trigger
- component test path
- coverage source
- Poetry ベースの暫定運用と Stage 2 の `uv` 方針の切り分け

## 実施手順

1. `.github/workflows/ci.yml` の branch trigger を確認する
2. 旧 `master/develop` 前提を新しい長命ブランチへ置き換える
3. 旧 `tests/unit/app` 前提を component test path へ置き換える
4. root shared tests の実行対象を確認する
5. Stage 6 後続へ送る未解決事項を整理する

## 成果物

- 更新済み CI workflow
- CI path 更新の検証記録

## 検証

- CI が新 path 前提で完走できる構成になっている

## 完了条件

- Task 6-3 以降で Docker / docs 追随に進める

## 実施結果

Task:

- Task 6-2: CI path 更新

変更内容:

- `.github/workflows/ci.yml` の branch trigger を新しい長命ブランチ構成へ更新した
  - push:
    - `main`
    - `dev/v0.7`
    - `support/0.6`
    - `topic/*`
    - `feature/*`
  - pull_request:
    - `main`
    - `dev/v0.7`
    - `support/0.6`
- test 実行 path を新構成に合わせて更新した
  - `components/libkoiki/tests/`
  - `components/koiki_ref_app/tests/`
  - `tests/unit/agent_guidance/`
  - `tests/integration/services/`
- coverage target も旧 `app` から `koiki_ref_app` へ追随させた
  - `--cov=koiki_ref_app`
  - `--cov=libkoiki`
- CI はまだ Poetry ベースのまま維持した
  - Stage 2 の `uv` 方針は決定済みだが、実ファイル移行は未完了のため Task 6-2 では path 更新に限定した

未解決事項:

- CI はまだ Poetry install / `.venv` cache / `poetry.lock` 前提
- `uv` 化は Stage 6 後続または依存管理実更新タスクで回収が必要
- `.github/instructions` の applyTo はまだ旧 `app/` / `libkoiki/` path 前提が残っている

検証結果:

- workflow 上の branch trigger は現在の運用モデルへ追随した
- workflow 上の test path は component 配置へ追随した
- 実際の GitHub Actions 実行はまだ行っていないため、完走確認は後続で必要

次タスクへ渡す事項:

- Task 6-3 で Dockerfile 側の copy / command / path を新構成へ更新する
- Task 6-5 で docs / instructions の旧 path 前提を追随させる

## 次タスク

- [Task 6-3](./task-6-3.md)
