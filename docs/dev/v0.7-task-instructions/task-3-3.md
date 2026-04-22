# Task 3-3: ORM bootstrap 明示化設計

## 目的

import 副作用で成立している ORM 拡張を、明示的な bootstrap に置き換える設計を定義する。

## 参照ファイル

- `app/db/base.py`
- `app/models/__init__.py`
- `app/models/user_sso.py`
- `alembic/env.py`

## 事前条件

- [Task 3-2](./task-3-2.md) が完了している

## 確認観点

- `register_model_extensions()` の責務
- mapper 構成前に呼ぶ必要がある箇所
- app 起動時と migration 時の呼び出し順

## 実施手順

1. 現在の import 副作用箇所を洗い出す
2. モデル読込とリレーション拡張を分けて整理する
3. 起動時 bootstrap の呼び出し順を定義する
4. migration 時 bootstrap の呼び出し順を定義する
5. 明示 API の形を記録する

## 成果物

- ORM bootstrap 設計メモ
- 起動時 / migration 時の呼び出し順メモ

## 検証

- ORM 拡張の発火点が明示されている
- import 順依存を減らせる設計になっている

## 完了条件

- Task 3-4 以降が ORM bootstrap 前提で判断できる

## 実施結果

Task:

- Task 3-3: ORM bootstrap 明示化設計

変更内容:

- 現在の import 副作用依存を次のように整理した
  - `app.models.__init__`
    - app 側モデルを import
    - `UserModel.sso_links = relationship(...)` を実行
  - `app.models.user_sso`
    - `UserModel` に対して `back_populates="sso_links"` を期待
  - `alembic/env.py`
    - `app.db.base` を import するが、実際の app model 読込と extension 登録は暗黙依存
- 問題の本体を次のように定義した
  - app model 読込
    - `BusinessClock`
    - `SamlAuthFlow`
    - `UserSSO`
  - framework model への extension 登録
    - `UserModel.sso_links = relationship(...)`
  - この2つが `app.models.__init__` へ混在し、import 順が実質の契約になっている
- 明示 API を次の2段階に分ける設計を定義した
  - `load_app_models()`
    - app 側 model class を import して mapper 対象へ登録する
    - 戻り値は不要
    - idempotent に呼べるのが望ましい
  - `register_model_extensions()`
    - framework model に対する relationship 追加や mapper 拡張を行う
    - 例: `UserModel.sso_links`
    - 重複登録を防ぐ guard を持つのが望ましい
- `register_model_extensions()` の責務を次のように定義した
  - framework 側 model に app 固有 relation を追加する
  - app 固有 relation の存在を明示的に保証する
  - mapper 構成前に一度だけ呼ばれる前提とする
  - business logic や DB 接続は持たない
- `load_app_models()` の責務も次のように定義した
  - app 側 SQLAlchemy model を import する
  - metadata / registry に app 側 table を登録する
  - side effect は model class 読込に限定する
  - relationship patch 自体は持たない
- 呼び出し順を次のように整理した
  1. `load_libkoiki_models()` 相当
     - 既存 framework model import
  2. `load_app_models()`
  3. `register_model_extensions()`
  4. 必要なら `configure_mappers()`
- app 起動時の bootstrap 順も次のように定義した
  - `create_app()` の早い段階、router include や DB 利用前に ORM bootstrap を呼ぶ
  - 推奨順:
    1. settings / logging
    2. ORM bootstrap
    3. FastAPI app 生成
    4. middleware / router / lifecycle wiring
  - 理由:
    - 依存解決や service import の途中で model relation が未登録だと壊れやすいため
- migration 時の bootstrap 順も次のように定義した
  - `alembic/env.py` で `target_metadata` 決定前に明示呼び出しする
  - 推奨順:
    1. framework model import
    2. `load_app_models()`
    3. `register_model_extensions()`
    4. `target_metadata = LibBase.metadata` または共有 metadata
  - これにより、autogenerate 時に app 側 table と relation 拡張が確実に見える
- API 配置の叩き台も整理した
  - `app/bootstrap/orm.py`
    - `load_app_models()`
    - `register_model_extensions()`
    - `bootstrap_orm()`
  - `bootstrap_orm()` は上記2つを順に呼ぶ薄い関数とする
- guard 方針も定義した
  - `register_model_extensions()` は、`hasattr(UserModel, "sso_links")` などで二重登録を防ぐ
  - 二重呼び出しに対して破壊的でない設計にする
- `app.db.base.Base` と `libkoiki.db.base.Base` の扱いも整理した
  - registry / metadata は共有でよい
  - ただし `app.models.user_sso` が `libkoiki.db.base.Base` を使っているのは、将来的には `app.db.base.Base` へ揃えるか検討余地がある
  - 現段階では bootstrap 発火点の明示が優先で、Base の全面整理は後続判断
- 現在の `alembic/env.py` への含意も記録した
  - `from app.db.base import Base as AppBase` が未使用に近く、source of truth が曖昧
  - 将来は `bootstrap_orm()` 呼び出しを明示し、その後 shared metadata を `target_metadata` に渡す構成がよい

未解決事項:

- `configure_mappers()` を明示的に呼ぶか、SQLAlchemy の遅延構成に任せるかは実装時に確認が必要
- app model が `app.db.base.Base` と `libkoiki.db.base.Base` のどちらを正本にするかは Stage 5 までに整理したい
- framework 側でも将来 extension point が増える場合、generic registry API を作るかは未決定

検証結果:

- ORM 拡張の発火点を `load_app_models()` / `register_model_extensions()` / `bootstrap_orm()` として明示できた
- app 起動時と migration 時の呼び出し順を説明できる状態になった
- 現在の import 順依存を減らす設計方針が定まった

次タスクへ渡す事項:

- Task 3-4 では、framework router / sample model の境界判断を、この ORM bootstrap 明示化方針と矛盾しないよう進める
- Task 3-5 では、互換 wrapper から `bootstrap_orm()` と `create_app()` をどう呼ぶかも意識する
- 実装時には `app.models.__init__` の副作用を段階的に縮小する方針で進める

## 次タスク

- [Task 3-4](./task-3-4.md)
