# Task 7-3: side-effect bootstrap 完全除去

## 目的

`koiki_ref_app.models.__init__` の副作用 import 依存を除去し、ORM bootstrap を明示 API で管理する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-7-2.md`
- `components/koiki_ref_app/src/koiki_ref_app/models/__init__.py`
- `components/koiki_ref_app/src/koiki_ref_app/bootstrap/__init__.py`
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`
- `components/koiki_ref_app/alembic/env.py`

## 事前条件

- [Task 7-2](./task-7-2.md) が完了している

## 確認観点

- `models.__init__` が relationship patch などの副作用を持っていないか
- app 起動時と Alembic 実行時に、同じ ORM bootstrap 経路を使えるか
- `UserModel.sso_links` の付与が明示的な登録関数へ集約されているか

## 実施手順

1. `models.__init__` の副作用処理を確認する
2. `load_app_models()` / `register_model_extensions()` / `bootstrap_orm()` を実装する
3. `create_app()` で `bootstrap_orm()` を呼ぶ
4. Alembic `env.py` でも `bootstrap_orm()` を呼ぶ
5. relationship patch が bootstrap module にだけ残ることを確認する

## 成果物

- 新しい ORM bootstrap module
- 副作用 import を除去した models 初期化

## 検証

- relationship patch が `bootstrap/orm.py` に集約されている
- app 起動時と Alembic の双方で `bootstrap_orm()` が呼ばれる

## 完了条件

- Task 7-4 の最終検証に進める

## 実施結果

Task:

- Task 7-3: side-effect bootstrap 完全除去

変更内容:

- `components/koiki_ref_app/src/koiki_ref_app/bootstrap/orm.py` を追加した
  - `load_app_models()`
  - `register_model_extensions()`
  - `bootstrap_orm()`
  を実装し、ORM bootstrap を明示 API 化した
- `components/koiki_ref_app/src/koiki_ref_app/bootstrap/__init__.py` から上記関数を export するようにした
- `components/koiki_ref_app/src/koiki_ref_app/models/__init__.py` から `UserModel.sso_links = relationship(...)` の副作用を除去した
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` で `create_app()` 開始時に `bootstrap_orm()` を呼ぶようにした
- `components/koiki_ref_app/alembic/env.py` でも `bootstrap_orm()` を呼び、Alembic 側の model registration を同じ経路へ揃えた

未解決事項:

- runtime dependency 未同期のため、`configure_mappers()` を含む完全な実行確認は未実施
- wrapper 除去と最終起動導線の整理は Task 7-4 側に残る

検証結果:

- `UserModel.sso_links` の relationship patch は `bootstrap/orm.py` にのみ残る状態になった
- `bootstrap_orm()` は `app_factory.py` と Alembic `env.py` の双方から呼ばれる
- したがって、ORM 拡張は import 副作用ではなく明示 bootstrap 経路へ整理できた

次タスクへ渡す事項:

- Task 7-4 で wrapper / import / test / docs を含む最終検証を行う
- dependency 同期後に runtime / mapper / Alembic の実行確認を再度実施する

## 次タスク

- [Task 7-4](./task-7-4.md)
