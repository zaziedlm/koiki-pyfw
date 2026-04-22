# Task 7-4: リリース前最終検証

## 目的

`v0.7` のディレクトリ再編と互換整理について、構造面の最終横断確認を行い、完了扱いにできる範囲と後続へ送る範囲を明確にする。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-7-1.md`
- `docs/dev/v0.7-task-instructions/task-7-2.md`
- `docs/dev/v0.7-task-instructions/task-7-3.md`
- `app/__init__.py`
- `app/main.py`
- `main.py`
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`
- `components/koiki_ref_app/src/koiki_ref_app/bootstrap/orm.py`
- `components/koiki_ref_app/alembic/env.py`

## 事前条件

- [Task 7-3](./task-7-3.md) が完了している

## 確認観点

- `components/libkoiki` / `components/koiki_ref_app` / `apps/` の構造が揃っているか
- `koiki_ref_app` 実装と test から旧 `app` import 依存が外れているか
- ORM bootstrap が import 副作用でなく明示 API へ寄っているか
- 互換 wrapper が意図した箇所に限定されているか
- 未実行の runtime / CI / Docker / migration 確認をどこまで後続扱いにするか説明できるか

## 実施手順

1. Stage 5 から Stage 7 までの変更結果を横断確認する
2. `rg` で旧 `app` 依存と互換導線の残件を再確認する
3. docs / CI / Docker / Alembic の主要 path が新構造へ追随済みか確認する
4. 構造面で完了扱いにできる項目と、依存同期後に再確認すべき項目を分離する
5. Stage 7 の完了判定を記録する

## 成果物

- Stage 7 の最終検証記録
- 後続へ送る未解決事項一覧

## 検証

- 構造再編としての完了条件が満たされている
- 未実行の runtime 検証が blocker か follow-up か説明できる

## 完了条件

- Stage 7 完了可否を判断できる

## 実施結果

Task:

- Task 7-4: リリース前最終検証

変更内容:

- Stage 5 から Stage 7 の結果を横断確認し、構造再編トラックとしての最終判定を整理した
- 旧 `app` 依存の残件を検索し、`components/koiki_ref_app` 実装・test からは除去済みであることを再確認した
- 互換導線は次にほぼ限定されていると整理した
  - `app/__init__.py`
  - `app/main.py`
  - root `main.py`
  - Docker / Compose / docs 上の `app.main:app` 記述
- ORM bootstrap は次の明示経路へ整理済みと確認した
  - `components/koiki_ref_app/src/koiki_ref_app/bootstrap/orm.py`
  - `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`
  - `components/koiki_ref_app/alembic/env.py`
- Stage 6 までで docs / CI / Docker / Alembic path は新構造へ追随済みであることを再確認した

未解決事項:

- dependency 未同期のため、以下の完全実行確認は未実施
  - `poetry run pytest`
  - Alembic 実行
  - Docker / Compose 起動
  - GitHub Actions 実行結果
- CI は path 更新済みだが、まだ Poetry ベースであり `uv` 実移行は未完了
- Docker / docs には互換上の理由で `app.main:app` が意図的に残っている
- `task-7-1.md` は記録ファイルとして未コミットのまま残っている

検証結果:

- `components/libkoiki` / `components/koiki_ref_app` / `apps/` の責務分離は成立している
- `koiki_ref_app` 実装・test の内部参照は `koiki_ref_app...` へ寄せられている
- ORM 拡張は import 副作用ではなく明示 bootstrap に整理されている
- 互換 wrapper は意図的に残した境界へ限定されている
- したがって、**ディレクトリ再編トラックとしての Stage 7 は完了** と判断できる
- 一方で、**実行環境を伴う最終出荷判定は dependency 同期後の follow-up** が必要

次タスクへ渡す事項:

- この再編トラック完了後は、`uv` 実移行と dependency 同期を進めたうえで runtime / CI / Docker / Alembic の実行確認を別途行う
- `app.main:app` 互換を外す最終タイミングは、実行確認と運用告知を伴う別タスクとして切り出す
- `task-7-1.md` の扱いは、Stage 7 の docs コミット時に併せて整理する
