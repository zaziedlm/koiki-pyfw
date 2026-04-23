# Task 6-6: Stage 6 結果検証

## 目的

Stage 6 で追随した Alembic / CI / Docker / docs / instructions が、新構造の運用経路として一貫しているか確認する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-6-1.md`
- `docs/dev/v0.7-task-instructions/task-6-2.md`
- `docs/dev/v0.7-task-instructions/task-6-3.md`
- `docs/dev/v0.7-task-instructions/task-6-4.md`
- `docs/dev/v0.7-task-instructions/task-6-5.md`
- `.github/workflows/ci.yml`
- `Dockerfile`
- `docker-compose.dev.yml`
- `components/koiki_ref_app/alembic.ini`

## 事前条件

- [Task 6-5](./task-6-5.md) が完了している

## 確認観点

- Alembic の実行経路が `components/koiki_ref_app` 基準に揃っているか
- CI の branch / test path / coverage target が新構造に揃っているか
- Docker / Compose の COPY / mount / Alembic path が新構造に揃っているか
- docs / instructions が新構造と矛盾していないか
- 依存未導入で未実行の検証を、Stage 6 の blocker とするか Stage 7 へ送るか

## 実施手順

1. Task 6-1 から 6-5 の実施結果を横断で確認する
2. Alembic / CI / Docker / docs の旧 path 前提が解消できているか確認する
3. 実行未確認箇所を抽出し、Stage 6 完了判定に影響するか判断する
4. Stage 7 へ送る未解決事項を整理する

## 成果物

- Stage 6 横断検証記録

## 検証

- build / test / run / migrate の各導線が、新構造で説明可能な状態になっている

## 完了条件

- Stage 7 の互換整理へ進める

## 実施結果

Task:

- Task 6-6: Stage 6 結果検証

変更内容:

- Stage 6 の各タスク結果を横断確認した
  - Task 6-1: Alembic path は `components/koiki_ref_app` へ追随済み
  - Task 6-2: CI branch / test path / coverage target は新構造へ追随済み
  - Task 6-3: Docker 更新設計は COPY / mount / Alembic / startup module の観点で整理済み
  - Task 6-4: Dockerfile / Compose / entrypoint は新 path へ追随済み
  - Task 6-5: docs / instructions / local ops path は新構造へ追随済み
- Stage 6 で解決すべき「path 崩れ」は一通り解消したと判断した
- 依存未導入のため未実行の検証は、Stage 6 の blocker ではなく Stage 7 以降で回収する扱いに整理した

未解決事項:

- CI はまだ Poetry ベースで、Stage 2 で定めた `uv` 実移行は未完了
- `docker compose up` / GitHub Actions / Alembic の完全実行確認は未実施
- runtime dependency がローカル未同期のため、`from app.main import app` や Alembic import の完全検証はまだ限定的
- root `README.md` と一部運用文書は Stage 6 時点の最小追随であり、`uv` 実移行後に再整理余地がある

検証結果:

- path / branch / test target / coverage target / Alembic location / Docker COPY・mount は新構造と整合している
- docs と instructions も主要な旧 `libkoiki/` / `app/` / root `alembic/` 前提から新構造へ追随した
- したがって Stage 6 の主目的である「運用系の path 追随」は達成できている
- 完全な runtime / CI / container 実行確認は後続課題だが、構造再編の進行を止める blocker ではない

次タスクへ渡す事項:

- Task 7-1 で互換 wrapper / legacy import / shim の棚卸しに入る
- Stage 7 では、`app` 互換層と旧 import 依存をどこまで除去できるかを重点確認する
- Stage 7 終盤で、依存同期後の実行確認を再度計画する

## 次タスク

- [Task 7-1](./task-7-1.md)
