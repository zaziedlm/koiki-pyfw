# apps plugin registration / app composition 設計タスク

## 目的

`apps/` 配下を downstream / 業務アプリチームの編集領域として使えるようにしつつ、`components/` 配下を業務アプリ固有 API のために直接改修しなくてよい構造を定義する。

root `main.py` の削除可否とは独立した設計タスクとして扱う。

## 背景

現行の標準 ASGI entrypoint は `koiki_ref_app.asgi:app` である。

一方で、業務アプリ固有の API を `apps/<project-slug>/...` に置く場合、どこかで FastAPI の `include_router()` を呼び出す必要がある。

この処理を `components/koiki_ref_app` に直接書くと、業務アプリチームが `components/` を改修する流れになりやすい。

既存の `apps/README.md` では、依存方向を `apps/ -> components/` のみにする方針を定義しているため、app composition もこの方針に合わせる。

## 設計原則

- `components/` は reusable framework / starter template として維持する
- `components/` は特定の `apps/<project-slug>` を import しない
- 業務アプリ固有 router / service / model / plugin 登録は `apps/<project-slug>/` に閉じる
- 業務アプリ固有 model の Base 定義は `apps/<project-slug>/backend/db/base.py` で所有する
- 業務アプリの ASGI entrypoint は `apps/<project-slug>/backend/asgi.py` など、業務アプリ側で所有する
- `koiki_ref_app.asgi:app` は reference app / starter の標準 entrypoint として維持する
- downstream 実運用では、Docker / Compose / process manager の ASGI target を業務アプリ entrypoint に差し替えられるようにする

## 推奨アーキテクチャ

### 1. components 側は app factory を提供する

`components/koiki_ref_app` は、reference app の `FastAPI` インスタンスを作る factory を提供する。

既存の `koiki_ref_app.app_factory.create_app()` を、業務アプリ側 composition から再利用できる正規 API として扱う。

### 2. apps 側が router 登録を所有する

例:

```text
apps/
  <project-slug>/
    backend/
      asgi.py
      db/
        base.py
      routes.py
      services/
      models/
```

```python
# apps/<project-slug>/backend/routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/business", tags=["business"])


@router.get("/items")
async def list_items():
    return []
```

```python
# apps/<project-slug>/backend/asgi.py
from koiki_ref_app.app_factory import create_app

from .routes import router as business_router

app = create_app()
app.include_router(business_router)
```

この形なら、業務アプリチームは `apps/<project-slug>/backend/` だけを編集して API を追加できる。

### 3. apps 側が DB Base を所有する

業務アプリ固有 model は、`components/koiki_ref_app.db.base.Base` を直接前提にし続けるのではなく、`apps/<project-slug>/backend/db/base.py` に業務アプリ固有の Base を用意する。

この Base は `libkoiki.db.base.Base` の registry / metadata を共有し、業務アプリ側で必要な共通カラムを定義する。

例:

```python
# apps/<project-slug>/backend/db/base.py
import re

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.orm import declared_attr

from libkoiki.db.base import Base as LibBase


class BusinessCustomBase:
    __abstract__ = True
    __allow_unmapped__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        if name.endswith("_model"):
            name = name[: -len("_model")]
        return name

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


Base = LibBase.registry.generate_base(cls=BusinessCustomBase)
```

この形なら、業務アプリは `koiki_ref_app` の reference app 向け共通カラム設計に縛られず、`tenant_id`、監査カラム、業務固有 ID などを apps 側で設計できる。

### 4. 起動 target は案件ごとに切り替える

reference app:

```bash
uv run --locked uvicorn koiki_ref_app.asgi:app --reload
```

業務アプリ:

```bash
uv run --locked uvicorn apps.<project_slug>.backend.asgi:app --reload
```

Docker / Compose / deployment manifest も同じ考え方で ASGI target を差し替える。

## 代替案と判断

### A. `koiki_ref_app` が環境変数から apps plugin を import する

例:

```text
KOIKI_APP_PLUGINS=apps.foo.backend.plugin:register
```

メリット:

- reference app の ASGI target を変えずに業務 router を追加できる

デメリット:

- `components/` が runtime config 経由で `apps/` を import する構図になる
- `components/` から `apps/` を参照しないという既存方針と説明が難しくなる
- plugin loader の障害が reference app 起動にも影響しやすい

判断:

- 初期案としては採用しない
- 将来必要になった場合も、loader は `libkoiki` の汎用 utility として提供し、呼び出しは apps 側 ASGI entrypoint が所有する

### B. root `main.py` で apps router を登録する

メリット:

- root の起動入口を使って合成しやすい

デメリット:

- root `main.py` の削除方針と衝突する
- root に業務アプリ固有 composition が集まりやすい
- 複数 downstream の分離が弱くなる

判断:

- 採用しない

## 実装タスク案

### AC-1: apps 側 ASGI entrypoint 方針を文書化する

対象:

- `apps/README.md`
- `docs/dev/local_setup.md`
- 必要に応じて `README.md`

完了条件:

- `apps/<project-slug>/backend/asgi.py` が業務アプリ composition の所有場所であると説明されている
- `components/` を業務 API 追加のために直接編集しない方針が明記されている

### AC-2: サンプル業務アプリ skeleton を追加する

対象候補:

- `apps/example_business_app/backend/asgi.py`
- `apps/example_business_app/backend/db/base.py`
- `apps/example_business_app/backend/routes.py`
- `apps/example_business_app/README.md`

完了条件:

- `create_app()` を使って reference app を生成し、apps 側 router を `include_router()` する最小サンプルがある
- `libkoiki.db.base.Base` の registry / metadata を共有する業務アプリ固有 Base のひな形がある
- サンプルは production 目的ではなく、downstream 実装の型として説明されている

### AC-3: import / 起動確認を追加する

検証候補:

```powershell
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.title)"
uv run --locked python -c "from apps.example_business_app.backend.asgi import app; print(app.title)"
```

必要なら最小 smoke test を `tests/` 配下へ追加する。

完了条件:

- reference app と example business app の両方が import できる
- `components/` から `apps/` への直接 import がない

### AC-4: Docker / Compose 差し替え方針を整理する

対象:

- `DOCKER_SETUP.md`
- `docs/dev/deploy.md`
- 必要に応じて compose override の例

完了条件:

- downstream が ASGI target を `apps.<project_slug>.backend.asgi:app` に差し替える方法が説明されている
- reference app の Dockerfile を業務アプリ固有コードで改修し続ける前提になっていない

### AC-5: 業務アプリ DB Base / migration 方針を整理する

対象:

- `apps/README.md`
- `docs/dev/local_setup.md`
- 必要に応じて Alembic 方針文書

完了条件:

- 業務アプリ固有 model は `apps/<project-slug>/backend/db/base.py` の `Base` を import する方針が説明されている
- `koiki_ref_app.db.base.Base` は reference app 用 Base として扱い、downstream の既定 Base にはしない
- 業務アプリ固有 migration をどこで管理するかは別タスクとして明示されている

## 非対象

- root `main.py` の削除
- `app.main:app` 互換 wrapper の削除
- 業務アプリ固有 DB migration の最終設計
- 複数 apps を同時に mount する plugin marketplace 的な仕組み

## root cleanup との関係

Root Cleanup RC-3 では、root `main.py` を削除しても業務アプリ API 実装能力が失われないことを確認する。

その根拠は、業務アプリの composition を root `main.py` ではなく `apps/<project-slug>/backend/asgi.py` が所有する、という本設計タスクである。

## 推奨順序

1. AC-1: 方針文書化
2. AC-2: サンプル skeleton
3. AC-3: import / smoke test
4. AC-4: Docker / Compose 差し替え方針
5. AC-5: 業務アプリ DB Base / migration 方針
