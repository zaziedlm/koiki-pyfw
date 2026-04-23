# Task 6-1: Alembic 配置移設

## 目的

migration を参照アプリ責務へ寄せ、新しい `koiki_ref_app` 配置で実行経路が成立することを確認する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-5.md`
- `components/koiki_ref_app/alembic.ini`
- `components/koiki_ref_app/alembic/env.py`

## 事前条件

- [Task 5-8](./task-5-8.md) が完了している

## 確認観点

- `alembic/` と `alembic.ini` が `koiki_ref_app` 側へ寄っていること
- `script_location` が新配置で成立すること
- `env.py` の import / metadata 解決が新構成前提になっていること
- 旧 root `alembic/` 参照がどこに残っているか

## 実施手順

1. `components/koiki_ref_app/alembic.ini` と `components/koiki_ref_app/alembic/env.py` を確認する
2. `script_location` が component 内で成立することを確認する
3. `env.py` が `koiki_ref_app` / `libkoiki` の `src` path を解決することを確認する
4. root `alembic/` 前提の参照箇所を検索する
5. Stage 6 後続へ送る未追随箇所を整理する

## 成果物

- Alembic 配置移設の検証記録

## 検証

- migration 実行経路が新構造で成立する

## 完了条件

- Task 6-2 以降で CI / Docker / docs の旧 Alembic path を追随させられる

## 実施結果

Task:

- Task 6-1: Alembic 配置移設

変更内容:

- Stage 5 で実施済みの Alembic 移設結果を新責務の観点で確認した
  - `components/koiki_ref_app/alembic/`
  - `components/koiki_ref_app/alembic.ini`
- `components/koiki_ref_app/alembic.ini` の `script_location = alembic` を確認し、component root を基準にした相対パスとして成立することを確認した
- `components/koiki_ref_app/alembic/env.py` が新構成を前提としていることを確認した
  - `components/koiki_ref_app/src`
  - `components/libkoiki/src`
  - repo root
  を `sys.path` に追加
  - app import は `koiki_ref_app.*`
  - `target_metadata` は `AppBase.metadata`
- root `alembic/` 前提の残参照を検索し、後続追随対象を整理した
  - `Dockerfile`
  - `docker-compose*.yml`
  - `README.md`
  - 各種設計 docs / guide
  - `.github/instructions`

未解決事項:

- Docker / Compose はまだ root `alembic/` を bind mount / copy する前提のまま
- docs には root `alembic/` 前提の説明が多数残っている
- dependency 未導入のため `alembic` コマンド自体の完全実行確認はまだ行っていない

検証結果:

- `components/koiki_ref_app/alembic.ini` の `script_location` は component root から見て成立することを確認した
- `components/koiki_ref_app/alembic/versions` には 18 本の migration script が存在し、移設漏れは見当たらない
- したがって Alembic の責務配置自体は `koiki_ref_app` 側へ移せている
- 未追随は実行周辺の path と docs であり、Task 6-2 以降の対象として扱う

次タスクへ渡す事項:

- Task 6-2 では CI path を `components/libkoiki` / `components/koiki_ref_app` / 新 test path 前提へ更新する
- Task 6-4 と 6-5 では Docker / docs の root `alembic/` 参照を新配置へ追随させる

## 次タスク

- [Task 6-2](./task-6-2.md)
