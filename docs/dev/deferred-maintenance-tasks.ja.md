# 先送り保守事項 タスク分解

最終更新: 2026-05-04

関連計画:

- `docs/dev/deferred-maintenance-plan.ja.md`
- `docs/dev/dm08-dm10-security-task-plan.ja.md`

## 1. タスク一覧

| ID | 優先度 | 種別 | 概要 | 推奨 PR 単位 |
| --- | --- | --- | --- | --- |
| `DM-01` | P0 | config | `Settings.DATABASE_URL` 組み立てを復旧する | 単独 |
| `DM-02` | P1 | ORM | `LoginAttemptModel.created_at` alias を `synonym` 化する | 単独 |
| `DM-03` | P2 | Pydantic | `Settings` 周辺を Pydantic v2 style に寄せる | `DM-01` 後 |
| `DM-04` | P2 | Pydantic | schema の `class Config` を `ConfigDict` へ移行する | 分割可 |
| `DM-05` | P2 | Pydantic | `.dict()` 呼び出しを `model_dump()` へ移行する | 分割可 |
| `DM-06` | P3 | Alembic/DB | Alembic / DB host 導線を補強する | 単独 |
| `DM-07` | P4 | IDE/test | VSCode pytest 対象を現行構成と整合させる | 単独 |
| `DM-08` | P5 | security | `pip-audit` 検出依存を更新する | 単独 |
| `DM-09` | P5 | security | Bandit false positive 方針を整理する | 単独 |
| `DM-10` | P5 | security | SAML metadata XML parser を hardening する | 単独 |
| `DM-11` | P5 | security | password hashing backend を `passlib` から `bcrypt` 直利用へ移行する | 単独 |
| `DM-12` | P4 | cleanup/docs | v0.7 新規参加者向けに legacy / compatibility 残骸を棚卸しする | 棚卸し単独、削除は別 PR |

## 2. `DM-01` Settings.DATABASE_URL 組み立て復旧

優先度: `P0`

状態: `完了`

### 目的

`components/libkoiki/src/libkoiki/core/config.py` の `DATABASE_URL` 組み立てが validator として機能していない状態を修正する。

現在の問題箇所:

```python
raise ValueError(v)    @validator("DATABASE_URL", pre=True)
```

### 対象

- `components/libkoiki/src/libkoiki/core/config.py`
- 設定読み込みテスト

### 作業

- `DATABASE_URL` 組み立て処理を Pydantic v2 style の validator へ移行する
- `BACKEND_CORS_ORIGINS` の処理も同じ変更単位で崩れないように確認する
- 不要 import を整理する
- 設定読み込みテストを追加または更新する

### 完了条件

- `DATABASE_URL` 明示指定時に指定値が優先される
- `DATABASE_URL` 未指定時に `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_SERVER` / `POSTGRES_PORT` / `POSTGRES_DB` から URL が構築される
- `BACKEND_CORS_ORIGINS` の comma-separated string が list として扱われる
- import error が発生しない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked python -c "from libkoiki.core.config import Settings; s=Settings(_env_file=None, POSTGRES_USER='u', POSTGRES_PASSWORD='p', POSTGRES_SERVER='h', POSTGRES_DB='d', POSTGRES_PORT=15432); print(s.DATABASE_URL)"
uv run --locked pytest components/libkoiki/tests -k "config or settings"
```

### 実施結果

- `components/libkoiki/src/libkoiki/core/config.py` の `DATABASE_URL` 組み立てを Pydantic v2 style の `model_validator` へ移行した
- `BACKEND_CORS_ORIGINS` の処理を Pydantic v2 style の `field_validator` へ移行した
- `DATABASE_URL` 明示指定時の優先、未指定時の `POSTGRES_*` からの組み立て、comma-separated CORS origin のテストを追加した
- `config.py` 由来の Pydantic v1 `@validator` warning は collect-only の warning summary から消えた

検証結果:

```text
uv lock --check
  成功

uv run --locked python -c "from libkoiki.core.config import Settings; ..."
  postgresql+asyncpg://u:p@h:15432/d

uv run --locked pytest components/libkoiki/tests/unit/core/test_config_settings.py
  3 passed

uv run --locked pytest components/libkoiki/tests -k "config or settings"
  4 passed, 114 deselected

uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
  206/243 tests collected, 37 deselected
```

残 warning:

- `LoginAttemptModel` の SQLAlchemy `SAWarning`: `DM-02` 対象
- Pydantic class-based `Config` deprecation: `DM-04` 対象
- `business_clock.py` の Pydantic v1 `@validator` deprecation: `DM-03` / `DM-04` 周辺で扱う

## 3. `DM-02` LoginAttemptModel.created_at alias 修正

優先度: `P1`

状態: `完了`

### 目的

`LoginAttemptModel` の `created_at = attempted_at` による SQLAlchemy `SAWarning` を、既存利用箇所を極力変えずに解消する。

### 対象

- `components/libkoiki/src/libkoiki/models/login_attempt.py`
- 必要に応じて login security 関連テスト

### 背景

現行実装は、共通 `Base` の `created_at` 契約と、ログイン試行履歴としての `attempted_at` という業務語彙を両立しようとしたものと推定する。

他箇所の変更を避けるため、DB カラム名と正式利用名は `attempted_at` のまま維持し、`created_at` は明示的な alias として扱う。

### 作業

- `sqlalchemy.orm.synonym` を import する
- `created_at = attempted_at` を `created_at = synonym("attempted_at")` に置き換える
- migration は変更しない
- repository / service の `attempted_at` 利用は変更しない

### 完了条件

- model import 時の SQLAlchemy `SAWarning` が消える
- `attempted_at` の既存利用が壊れない
- `created_at` 互換が残る
- Alembic migration 差分を発生させない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest --collect-only components/libkoiki/tests tests/integration/services -m "not db_integration"
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_login_security_service.py
```

DB 結合確認が可能な場合:

```powershell
.\scripts\run-db-integration-tests.ps1
```

### 実施結果

- `components/libkoiki/src/libkoiki/models/login_attempt.py` で `created_at = attempted_at` を `created_at = synonym("attempted_at")` に置き換えた
- DB カラム名と既存の正式利用名は `attempted_at` のまま維持した
- repository / service の呼び出し側は変更していない
- migration は変更していない
- `created_at` から読み書きしても `attempted_at` に反映されることをテスト追加した
- mapper 上の `attempted_at` カラムが重複しないことをテスト追加した
- `LoginAttemptModel` の SQLAlchemy `SAWarning` は warning summary から消えた

検証結果:

```text
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/test_login_attempt_model.py components/libkoiki/tests/unit/libkoiki/services/test_login_security_service.py
  10 passed

uv run --locked pytest --collect-only components/libkoiki/tests tests/integration/services -m "not db_integration"
  120/146 tests collected, 26 deselected
```

残 warning:

- Pydantic class-based `Config` deprecation: `DM-04` 対象
- `business_clock.py` の Pydantic v1 `@validator` deprecation: `DM-03` / `DM-04` 周辺で扱う

## 4. `DM-03` Settings 周辺の Pydantic v2 化

優先度: `P2`

状態: `完了`

### 目的

`DM-01` の修正後、`Settings` 周辺の Pydantic deprecation warning を継続的に減らす。

### 対象

- `components/libkoiki/src/libkoiki/core/config.py`
- `components/libkoiki/src/libkoiki/core/security_config.py`

### 作業

- `@validator` を `@field_validator` / `@model_validator` へ移行する
- class-based `Config` があれば `SettingsConfigDict` / `ConfigDict` へ寄せる
- `.dict()` を `model_dump()` へ置き換える

### 完了条件

- `config.py` 由来の Pydantic v1 validator warning が消える
- `security_config.py` 由来の class-based config / `.dict()` warning が解消または明確に後続タスク化される
- 設定読み込みの挙動が維持される

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest --collect-only components/libkoiki/tests -m "not db_integration"
```

### 実施結果

- `Settings` の `@validator` は `DM-01` で `field_validator` / `model_validator` へ移行済み
- `components/libkoiki/src/libkoiki/core/security_config.py` の class-based `Config` を廃止し、`model_config = ConfigDict()` へ移行した
- `security_config.update_config()` の `.dict()` を `.model_dump()` へ移行した
- `security_config.py` import / reload 時に Pydantic class-based config deprecation が出ないことをテスト追加した
- `update_config()` が既存の nested `login_security` 設定を保持しながら上書きできることをテスト追加した

検証結果:

```text
uv run --locked pytest components/libkoiki/tests/unit/core/test_security_config.py components/libkoiki/tests/unit/core/test_config_settings.py
  5 passed

uv run --locked pytest --collect-only components/libkoiki/tests -m "not db_integration"
  122 tests collected
```

残 warning:

- schema 群の Pydantic class-based `Config` deprecation: `DM-04` 対象
- `business_clock.py` の Pydantic v1 `@validator` deprecation: `DM-04` と合わせて扱う

## 5. `DM-04` schema class Config 移行

優先度: `P2`

状態: `完了`

### 目的

Pydantic class-based `Config` deprecation warning を解消する。

### 対象候補

- `components/libkoiki/src/libkoiki/schemas/user.py`
- `components/libkoiki/src/libkoiki/schemas/todo.py`
- `components/libkoiki/src/libkoiki/schemas/role.py`
- `components/libkoiki/src/libkoiki/schemas/permission.py`
- `components/libkoiki/src/libkoiki/schemas/refresh_token.py`
- `components/koiki_ref_app/src/koiki_ref_app/schemas/sso.py`
- `components/koiki_ref_app/src/koiki_ref_app/schemas/saml.py`

### 作業

- `from pydantic import ConfigDict` を追加する
- `class Config: from_attributes = True` などを `model_config = ConfigDict(from_attributes=True)` へ置き換える
- schema ごとに serialization / validation の既存挙動を確認する

### 完了条件

- class-based `Config` warning が減る
- API schema の互換性が維持される
- auth / SSO / SAML の schema validation が壊れない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
```

### 実施結果

- libkoiki schema の class-based `Config` を `ConfigDict(from_attributes=True)` へ移行した
  - `user.py`
  - `todo.py`
  - `role.py`
  - `permission.py`
  - `refresh_token.py`
- koiki_ref_app schema の `json_schema_extra` を `ConfigDict(json_schema_extra=...)` へ移行した
  - `sso.py`
  - `saml.py`
- `business_clock.py` の `@validator("base_timezone")` を `@field_validator("base_timezone")` へ移行した
- `business_clock.py` の `model_validator(mode="after")` を Pydantic v2 の instance method style に寄せた
- schema 配下の active な `class Config` / `@validator` は残っていない
- collect-only の warning summary から Pydantic schema config / validator deprecation が消えた

検証結果:

```text
rg -n "class Config|@validator" components/libkoiki/src/libkoiki/schemas components/koiki_ref_app/src/koiki_ref_app/schemas -S
  active definition なし

uv run --locked python -c "import libkoiki.schemas.user, ...; print('schemas ok')"
  schemas ok

uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_business_clock_service.py components/koiki_ref_app/tests/unit/app/services/test_sso_service.py components/koiki_ref_app/tests/unit/app/services/test_saml_service.py components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py
  60 passed

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_user_service.py components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
  27 passed
  既存の transaction mock RuntimeWarning と `user_service.py` の `.dict()` deprecation は残る

uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
  210/247 tests collected, 37 deselected

uv lock --check
  成功
```

残 warning:

- `user_service.py` などの `.dict()` deprecation: `DM-05` 対象
- transaction test mock の coroutine warning: 本タスク外

## 6. `DM-05` .dict() 呼び出し移行

優先度: `P2`

状態: `完了`

### 目的

Pydantic v2 deprecation warning のうち、`.dict()` 呼び出しを `model_dump()` へ移行する。

### 対象候補

- `components/libkoiki/src/libkoiki/repositories/base.py`
- `components/libkoiki/src/libkoiki/services/user_service.py`
- `components/libkoiki/src/libkoiki/services/todo_service.py`
- `components/libkoiki/src/libkoiki/core/logging.py`
- `components/libkoiki/src/libkoiki/core/security_config.py`
- `components/libkoiki/src/libkoiki/api/v1/endpoints/users.py`

### 作業

- Pydantic model であることが明確な箇所は `.model_dump(...)` へ置き換える
- Pydantic v1/v2 両対応を考慮すべき汎用 helper では、互換 helper の導入を検討する
- logging sanitizer では Mapping / 任意 object 対応を壊さない

### 完了条件

- `.dict()` deprecation warning が減る
- create / update 系の payload 変換が従来どおり動く
- logging sanitizer の redaction 挙動が維持される

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/test_input_logging.py components/libkoiki/tests/unit/libkoiki/services/test_user_service.py components/libkoiki/tests/unit/libkoiki/services/test_login_security_service.py
```

### 実施結果

- Pydantic model が明確な `.dict()` 呼び出しを `.model_dump()` へ移行した
  - `components/libkoiki/src/libkoiki/repositories/base.py`
  - `components/libkoiki/src/libkoiki/services/user_service.py`
  - `components/libkoiki/src/libkoiki/services/todo_service.py`
  - `components/libkoiki/src/libkoiki/api/v1/endpoints/users.py`
- `core.logging.get_log_field_names()` の `.dict()` は Pydantic v1 互換 fallback として残した
  - 同 helper はすでに `model_dump()` を優先している
  - `.dict()` fallback は `model_dump()` を持たない旧 Pydantic 互換オブジェクト向け
- 実コード上の残存 `.dict()` は `core.logging.py` の fallback のみに限定された
- 対象テストで Pydantic `.dict()` deprecation は出なくなった

検証結果:

```text
rg -n "\.dict\(" components/libkoiki/src components/koiki_ref_app/src -S
  components/libkoiki/src/libkoiki/core/logging.py の Pydantic v1 fallback のみ

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/test_input_logging.py components/libkoiki/tests/unit/libkoiki/services/test_user_service.py components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py components/koiki_ref_app/tests/unit/app/services/test_todo_service.py
  21 passed, 1 skipped
  既存の transaction mock RuntimeWarning は残る

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
  17 passed
  既存の transaction mock RuntimeWarning は残る

uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
  210/247 tests collected, 37 deselected

uv lock --check
  成功
```

残 warning:

- transaction test mock の coroutine warning: 本タスク外

## 7. `DM-06` Alembic / DB host 導線補強

優先度: `P3`

状態: 完了

### 目的

Alembic path 不一致と、ローカル実行時の `db` hostname 解決失敗を避ける。

### 対象

- `components/koiki_ref_app/alembic.ini`
- `components/koiki_ref_app/alembic/env.py`
- `docs/dev/db-integration-testing.md`
- `docs/saml/SAML_SETUP.md`
- `scripts/start-local-dev.ps1`
- 必要に応じて Docker / compose docs

### 作業

- 現行標準コマンド `uv run --locked alembic -c components/koiki_ref_app/alembic.ini ...` を明示する
- ローカル実行では `localhost`、Docker 内実行では `db` を使うことを明記する
- `env.py` の `DATABASE_URL` 未設定エラーを具体化する
- `alembic.ini` の default URL を変更するかどうか判断する

### 完了条件

- docs / scripts の Alembic path が現行構成と一致する
- ローカル実行で `db` hostname を誤って使う導線が減る
- `DATABASE_URL` 欠落時に原因と対応が分かる

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
$env:DATABASE_URL='postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db'
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
```

### 対応結果

- `components/koiki_ref_app/alembic.ini` の fallback URL を host 側実行で解決できる `localhost` に変更した
- `alembic.ini` に、実行時は `env.py` が `Settings.DATABASE_URL` で上書きすること、Docker 内では `DATABASE_URL` に `db` host を明示することをコメントで補足した
- `components/koiki_ref_app/alembic/env.py` の `DATABASE_URL` 未設定エラーを、現行標準コマンドと host 使い分けが分かる文言へ変更した
- `docs/dev/db-integration-testing.md` に Alembic の標準実行例と host 側 / Docker 内の DB host 使い分けを追加した
- `docs/saml/SAML_SETUP.md` と `docs/saml/saml-env-config-guide.md` の migration 手順を `uv run --locked alembic -c components/koiki_ref_app/alembic.ini ...` と `localhost` 前提へ更新した
- `scripts/start-local-dev.ps1` は既に `localhost` と component 側 `alembic.ini` を使っていたため、変更不要と判断した

### 実施済み検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DATABASE_URL='postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db'
$env:DEBUG='true'
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
  20260228001 (head)

uv lock --check
  Resolved 87 packages in 1ms

uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
  20260228001 (head)
```

## 8. `DM-07` VSCode pytest 導線整合

優先度: `P4`

状態: 完了

### 目的

IDE の pytest 検出対象と CI の検証対象のズレを減らす。

### 対象

- `.vscode/settings.json`
- 必要に応じて `docs/dev/test-guide.md`

### 作業

- `python.testing.pytestArgs` を現行構成に合わせる
- DB integration は既定では除外する
- VSCode 上で重くなりすぎる場合は、軽量 profile と full profile の使い分けを docs に明記する

### 完了条件

- IDE から root `tests` 以外の component tests も見える
- `db_integration` が意図せず常時実行されない
- CI と IDE の検出差分が説明できる

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

### 対応結果

- `.vscode/settings.json` の `python.testing.pytestArgs` を root `tests` のみから、現行の component tests と root 側 agent / service tests を含む範囲へ拡張した
- VSCode の既定収集から `db_integration` を除外するため、pytest args に `-m "not db_integration"` を追加した
- `docs/dev/test-guide.md` に VSCode Test Explorer の既定収集範囲と、同条件の CLI collect-only コマンドを追記した

### 実施済み検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
  210/247 tests collected, 37 deselected

uv lock --check
  Resolved 87 packages in 2ms
```

## 9. `DM-08` pip-audit 検出依存更新

優先度: `P5`

状態: `完了`

詳細実施計画:

- `docs/dev/dm08-dm10-security-task-plan.ja.md`

### 目的

`pip-audit` で検出済みの依存脆弱性を解消する。

### 対象候補

- `pyjwt`
- `pytest`
- `starlette` / `fastapi`
- `pip`

### 作業

- 現時点の `pip-audit` 結果を再取得する
- direct dependency と transitive dependency を分ける
- `uv add` / `uv lock` / `uv sync --locked` で更新する
- FastAPI / Starlette の互換範囲を確認する

### 完了条件

- `uv run --locked pip-audit` の検出件数が減る、または残件の扱いが明文化される
- `uv.lock` が更新される場合、lock mismatch が起きない
- backend tests の主要範囲が通る

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
uv run --locked pip-audit
uv lock --check
uv run --locked pytest --collect-only components/libkoiki/tests components/koiki_ref_app/tests tests -m "not db_integration"
```

### 実施結果

実行日: 2026-05-03

更新前の `pip-audit` 結果:

- `pip 26.0.1`: `CVE-2026-3219`
- `PyJWT 2.11.0`: `CVE-2026-32597`, fixed in `2.12.0`
- `pytest 8.4.2`: `CVE-2025-71176`, fixed in `9.0.3`
- `starlette 0.46.2`: `CVE-2025-54121`, fixed in `0.47.2`
- `starlette 0.46.2`: `CVE-2025-62727`, fixed in `0.49.1`

対応:

- root `pyproject.toml` と `components/libkoiki/pyproject.toml` の dependency range を更新した
  - `fastapi>=0.136.1,<0.137.0`
  - `PyJWT[crypto]>=2.12.0,<2.13.0`
  - `bcrypt>=4.0.1,<4.1.0`
  - `pytest>=9.0.3,<9.1.0`
  - `pytest-asyncio>=1.3.0,<1.4.0`
- `uv.lock` を更新した
  - `fastapi 0.115.14 -> 0.136.1`
  - `starlette 0.46.2 -> 0.52.1`
  - `PyJWT 2.11.0 -> 2.12.1`
  - `bcrypt 4.3.0 -> 4.0.1`
  - `pytest 8.4.2 -> 9.0.3`
  - `pytest-asyncio 1.0.0 -> 1.3.0`
  - `annotated-doc 0.0.4` が `fastapi` の dependency として追加された
- コンテナ操作ログ点検で見つかった `passlib 1.7.4` / `bcrypt 4.1+` 互換 warning に対応した
  - `passlib 1.7.4` は `bcrypt.__about__.__version__` を参照する
  - `bcrypt 4.1+` では `__about__` がなく、ログイン時に `(trapped) error reading bcrypt version` traceback が出る
  - 現行実装を維持し、`bcrypt` を `4.0.1` 系に固定して warning を解消した
  - この対応は DM-08 の脆弱性対応中に見つかったログ品質問題への暫定対応であり、長期方針としては `passlib` 依存を見直す

更新後の `pip-audit` 結果:

- `PyJWT` / `pytest` / `starlette` の検出は解消
- `bcrypt 4.0.1` 固定による新規検出はなし
- 残件は `pip 26.0.1` の `CVE-2026-3219` のみ
- `pip` の `CVE-2026-3219` は `pip-audit` 結果上 `Fix Versions` が空で、アプリケーション runtime dependency ではなく監査実行環境側 dependency として残件扱い
- workspace package の `koiki-ref-app` / `libkoiki` は PyPI 上にないため `pip-audit` の skip reason として表示される

検証結果:

```text
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'

uv lock --check
  成功

uv sync --locked --group dev --group test --group security
  成功

uv run --locked pip-audit
  pip 26.0.1 CVE-2026-3219 の 1 件のみ残存

uv run --locked python -c "from libkoiki.core.security import get_password_hash, verify_password; ..."
  hash / verify 成功
  passlib / bcrypt 由来 traceback なし

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_user_service.py components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
  27 passed
  既存の transaction mock RuntimeWarning は残る

uv run --locked pytest --collect-only components/libkoiki/tests components/koiki_ref_app/tests tests -m "not db_integration"
  249/286 tests collected, 37 deselected

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
  17 passed
  既存の transaction mock RuntimeWarning は残る

uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_service.py components/koiki_ref_app/tests/unit/app/services/test_sso_service.py
  38 passed

uv run --locked pytest tests/unit/test_pyjwt_migration.py
  33 passed
  PyJWT 2.12.1 の短い HMAC test key に対する InsecureKeyLengthWarning は残る

uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
  196 passed, 1 skipped, 11 deselected
  既存の transaction mock RuntimeWarning と FastAPI / Starlette 更新に伴う HTTP_422_UNPROCESSABLE_ENTITY deprecation warning は残る
```

### 後続タスク

- `DM-11`: `passlib 1.7.4` が古く、`bcrypt 4.1+` 以降の API 変更に追従していないため、v0.7.0 の土台整備として password hashing backend を `bcrypt` 直利用へ移行する

## 10. `DM-09` Bandit false positive 方針整理

優先度: `P5`

状態: `実装・ローカル検証済み`

詳細実施計画:

- `docs/dev/dm08-dm10-security-task-plan.ja.md`

### 目的

`bandit` の検出結果について、修正対象と false positive を分離する。

### 対象候補

- OAuth2 token type 定数に対する `B106`
- security event name 定数に対する `B105`
- logging fallback の `B110`

### 作業

- 最新の Bandit 結果を再取得する
- false positive は理由を明記して `# nosec` または設定除外を検討する
- 実リスクがあるものはコード修正に回す

### 実施結果

実行日: 2026-05-04

更新前の Bandit 結果:

- `High`: 0
- `Medium`: 0
- `Low`: 12

Low 検出の分類:

- `B106 hardcoded_password_funcarg`: OAuth2 `token_type="bearer"` 4 件
  - secret ではなく token type 定数
  - `TokenWithRefresh` schema に `token_type = "bearer"` の default があるため、endpoint 側の明示指定を削除して解消した
- `B105 hardcoded_password_string`: security event name 定数 5 件
  - secret ではなく security log の event type label
  - 対象行へ局所 `# nosec B105` を付与し、直前コメントで理由を記録した
- `B110 try_except_pass`: logging fallback 3 件
  - `request_context.get()` 周辺は broad `try/except/pass` を外し、`dict` 判定で安全に扱う形へ変更した
  - timezone fallback は `Exception` ではなく `ValueError` / `ZoneInfoNotFoundError` に絞った

更新後の Bandit 結果:

- `High`: 0
- `Medium`: 0
- `Low`: 0
- 局所 `# nosec B105`: 5 件

広域除外や plugin 全体除外は行っていない。
`# nosec` は security event name の false positive に限定した。

### 完了条件

- Bandit の残件がレビュー可能な粒度に減る
- `# nosec` を使う場合は理由がコメントまたは文書に残る
- High severity が残らない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
```

実施済み結果:

```text
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level low
  No issues identified.
  Low: 0
  Medium: 0
  High: 0
  Total potential issues skipped due to specifically being disabled: 5

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/test_input_logging.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py components/koiki_ref_app/tests/unit/app/services/test_sso_service.py components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
  65 passed, 1 skipped

uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py components/koiki_ref_app/tests/unit/app/services/test_sso_service.py components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
  55 passed

uv run --locked pytest components/libkoiki/tests/unit/core/test_logging_sanitizer.py components/libkoiki/tests/unit/libkoiki/test_input_logging.py
  38 passed, 1 skipped
```

既存の `AsyncMock` と transaction helper の組み合わせによる `RuntimeWarning` は残るが、DM-09 の Bandit false positive 整理による失敗ではない。

コンテナ確認:

```text
unified prod container build / run: 成功
ブラウザ password login: 成功
ブラウザ OIDC SSO login: 成功
ブラウザ SAML login: 成功
タスク管理操作: 成功
アプリコンテナログ点検: Traceback / ResponseValidationError / ValidationError / Internal Server Error / Invalid token response / Password verification failed なし
```

残る `InsecureKeyLengthWarning` は `JWT_SECRET` が HS256 推奨長 32 bytes 未満であることによる既知警告であり、DM-09 の Bandit false positive 整理とは別件として扱う。

## 11. `DM-10` SAML metadata XML parser hardening

優先度: `P5`

状態: `実装・ローカル検証済み`

詳細実施計画:

- `docs/dev/dm08-dm10-security-task-plan.ja.md`

### 目的

外部 SAML metadata XML を扱う箇所を、標準 `xml.etree.ElementTree` からより安全な parser に寄せる。

### 対象

- `components/koiki_ref_app/src/koiki_ref_app/services/saml_metadata_loader.py`
- `components/koiki_ref_app/tests/unit/app/services/test_saml_support_logging.py`
- 必要に応じて dependency 定義

### 作業

- `defusedxml` 採用要否を判断する
- 採用する場合は dependency group ではなく runtime dependency に入れるかを検討する
- `ET.fromstring` と XML parse error handling を置き換える
- 既存 logging の `error_type` 方針を維持する

### 実施結果

- `defusedxml.ElementTree` を採用し、SAML metadata XML parse を hardening した
- `koiki_ref_app` の runtime dependency として `defusedxml>=0.7.1,<0.8.0` を明示した
- DOCTYPE / external entity declaration を含む metadata が `EntitiesForbidden` として拒否されるテストを追加した
- Keycloak コンテナを SAML IdP とした unified prod 構成で、metadata 取得、証明書抽出、SAML ログイン、タスク管理操作が成功することを確認した

### 完了条件

- 外部 XML parse が hardening される
- SAML metadata loader の既存テストが通る
- logging sanitizer / error logging 方針が維持される

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_support_logging.py components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
uv run --locked bandit -r components/koiki_ref_app/src/koiki_ref_app/services/saml_metadata_loader.py
```

実施済み結果:

- `uv lock --check`: 成功
- 対象 pytest: `31 passed`
- 対象 Bandit: `No issues identified`
- ローカル Keycloak SAML IdP によるブラウザログイン確認: 成功
- `Invalid XML in SAML metadata`、`EntitiesForbidden`、`ParseError`、`No signing certificates found`、`Traceback`: なし

## 12. `DM-11` password hashing backend の passlib 脱却

優先度: `P5`

状態: `実装・コンテナ検証済み`

### 目的

`libkoiki.core.security` の password hashing backend を `passlib` 依存から `bcrypt` 直利用へ移行し、古い `passlib 1.7.4` と `bcrypt` の互換問題を根本解消する。

### 判断経緯

`DM-08` の依存脆弱性対応後、コンテナ実行ログでログイン時に次の warning / traceback が確認された。

```text
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

原因:

- 現行実装は `libkoiki.core.security` で `passlib.context.CryptContext(schemes=["bcrypt"])` を使っている
- `passlib 1.7.4` は `2020` 年リリースで止まっている
- `passlib 1.7.4` は bcrypt backend 初期化時に `bcrypt.__about__.__version__` を参照する
- `bcrypt 4.1+` では `__about__` が削除されているため、ログイン時に traceback が出る

`DM-08` ではセキュリティ依存更新の差分を広げすぎないため、暫定的に `bcrypt>=4.0.1,<4.1.0` へ固定し、warning を解消した。

ただし、この固定は根本対応ではない。`bcrypt` を古い互換範囲に留めるより、password hashing の薄い境界である `get_password_hash()` / `verify_password()` を `bcrypt` 直利用へ置き換える方が、v0.7.0 以降の保守性が高い。

### 対象

- `components/libkoiki/src/libkoiki/core/security.py`
- `components/libkoiki/src/libkoiki/services/user_service.py`
- `components/libkoiki/tests/unit/core/test_security_password_hashing.py`
- `components/libkoiki/tests/unit/libkoiki/services/test_user_service.py`
- `components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py`
- 必要に応じて auth / login security 関連テスト
- root `pyproject.toml`
- `components/libkoiki/pyproject.toml`
- `uv.lock`

### 作業

- `libkoiki.core.security.get_password_hash()` を `bcrypt.hashpw()` / `bcrypt.gensalt()` ベースへ置き換える
- `libkoiki.core.security.verify_password()` を `bcrypt.checkpw()` ベースへ置き換える
- 既存の `$2b$...` bcrypt hash が検証できることを確認する
- invalid hash / 破損 hash で例外が外へ漏れず、認証失敗として扱われることを確認する
- `user_service.authenticate_user()` の存在しないユーザー向け dummy hash による timing protection を維持する
- `passlib[bcrypt]` dependency を削除する
- `bcrypt` dependency は `4.x` の現行互換範囲へ戻す

### 実施結果

- `libkoiki.core.security` の password hashing backend を `passlib.context.CryptContext` から `bcrypt` 直利用へ移行した
  - `get_password_hash()` は `bcrypt.hashpw()` / `bcrypt.gensalt(rounds=12)` を使用する
  - `verify_password()` は `bcrypt.checkpw()` を使用する
  - invalid hash / 破損 hash は例外を外へ漏らさず `False` を返す
- `user_service.authenticate_user()` の存在しないユーザー向け dummy hash timing protection を維持するテストを追加した
- `components/libkoiki/tests/unit/core/test_security_password_hashing.py` を追加し、次を確認した
  - `$2b$` bcrypt hash の生成
  - 正しい password の検証成功
  - 誤った password の検証失敗
  - 既存 `$2b$` hash の検証互換
  - invalid hash / 破損 hash で `False` を返すこと
- root `pyproject.toml` と `components/libkoiki/pyproject.toml` から `passlib[bcrypt]` を削除した
- `bcrypt` dependency を `bcrypt>=4.3.0,<5.0.0` に更新した
  - `5.0.0` は 72 bytes 超過 password の扱いが変わるため、今回の移行では自動採用しない
- `uv.lock` を更新し、`passlib 1.7.4` が削除され、`bcrypt 4.3.0` が解決された

### 完了条件

- `passlib` が runtime dependency から消えている
- `get_password_hash()` が `$2b$` 形式の bcrypt hash を生成する
- `verify_password()` が既存 `$2b$` hash を検証できる
- ユーザー作成 / パスワード更新 / ログインの既存挙動が維持される
- 存在しないユーザーや invalid hash の認証失敗時にも timing protection が維持される
- コンテナログで `passlib/handlers/bcrypt.py` 由来 traceback が発生しない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv lock --check
uv run --locked python -c "from libkoiki.core.security import get_password_hash, verify_password; h=get_password_hash('TestPass123@'); print(h.startswith('$2b$'), verify_password('TestPass123@', h))"
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_user_service.py components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
uv run --locked pip-audit
```

実施済み結果:

- `uv lock --check`: 成功
- `uv sync --locked --group dev --group test --group security`: 成功
  - `passlib==1.7.4` が uninstall された
- `uv run --locked python -c "import importlib.util; print(importlib.util.find_spec('passlib'))"`
  - `None`
- `uv run --locked python -c "from libkoiki.core.security import get_password_hash, verify_password; h=get_password_hash('TestPass123@'); print(h.startswith('$2b$'), verify_password('TestPass123@', h), verify_password('WrongPass123@', h))"`
  - `True True False`
- 対象ユニットテスト:
  - `components/libkoiki/tests/unit/core/test_security_password_hashing.py`
  - `components/libkoiki/tests/unit/libkoiki/services/test_user_service.py`
  - `components/libkoiki/tests/unit/libkoiki/services/test_user_service_simple.py`
  - `components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py`
  - `components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py`
  - 結果: `34 passed`
- 非 DB component テスト:
  - `uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"`
  - 結果: `204 passed, 1 skipped, 11 deselected`
- `uv run --locked pip-audit`
  - `pip 26.0.1 / CVE-2026-3219` のみ残存
  - `bcrypt` の新規検出なし

既存テストでは `AsyncMock` と transaction helper の組み合わせによる `RuntimeWarning` が残るが、DM-11 の password hashing 移行による失敗ではない。

### コンテナ確認結果

ローカル unified prod 構成で、次を実行した。

```powershell
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
```

ブラウザ操作で次を確認した。

- 通常 password login: 成功
- タスク管理操作: 成功
- 新規ユーザー登録 -> password login: 成功
- OIDC / SSO login: 成功
- SAML login: 成功

パスワード変更は FastAPI Swagger UI 経由の導線のみで、prod container では Swagger UI が非表示のため未確認。

アプリコンテナログ確認結果:

- `Login successful`
- `User registered successfully`
- `SSO login successful`
- `SAML login successful`
- `/api/v1/auth/me`、`/api/v1/todos`、`/api/v1/todos` 更新系 request が成功

次の DM-11 関連ログは確認されなかった。

- `passlib`
- `error reading bcrypt version`
- `passlib/handlers/bcrypt.py`
- `Traceback`
- `Password verification failed`

残る `InsecureKeyLengthWarning` は `JWT_SECRET` が HS256 推奨長 32 bytes 未満であることによる既知警告であり、DM-11 の password hashing backend 移行とは別件として扱う。

コンテナ確認:

```powershell
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
docker logs koiki_app_prod_unified
```

確認観点:

- password login が成功する
- タスク管理アプリ操作が成功する
- `passlib` / `bcrypt` 互換 traceback が出ない
- `bcrypt` の新規 `pip-audit` 検出がない

## 13. `DM-12` v0.7 legacy / compatibility 棚卸し

優先度: `P4`

状態: `棚卸し作成済み / DM-12-A 実施済み`

棚卸し結果:

- `docs/dev/dm12-legacy-compatibility-inventory.ja.md`

### 目的

v0.7 から初めて開発に参加するメンバーが、現行実装の場所と過去互換のために残っている場所を誤認しないようにする。

過去 v0.6 系のプロジェクト構造や移行経緯から残っている legacy / compatibility 要素を棚卸しし、削除・維持・正規導線への置換を判断できる状態にする。

### 判断経緯

v0.7 では、現行の正規実装は `components/libkoiki/` と `components/koiki_ref_app/` に分離されている。

一方で、ルート `app/` は legacy import / entrypoint の compatibility wrapper として意図的に残っている。さらに、過去構造由来のルート `libkoiki/` など、現行の正規導線と混同されやすいフォルダーや参照が残っている可能性がある。

これらをいきなり削除すると、Docker 起動、既存 import、運用手順、外部参照を壊す恐れがある。そのため、DM-12 では削除から始めず、まず棚卸し表を作成して判断根拠を残す。

### 対象候補

- ルート `app/`
- ルート `libkoiki/`
- ルート `main.py`
- ルート `apps/`
- ルート `tests/` と component 配下 tests の関係
- legacy import / compatibility shim
- `sys.path` 追加や import path 調整
- Docker / Compose / entrypoint / start script の `app.main` 参照
- README / docs / agent docs / `.github` 内の旧パス参照
- v0.6 系の履歴説明が、現行手順として読めてしまうドキュメント

### 作業

- 現行 v0.7 の正規導線を明文化する
  - framework: `components/libkoiki/`
  - reference app backend: `components/koiki_ref_app/`
  - frontend: `frontend/`
  - local setup: `docs/dev/local_setup.md`
- legacy / compatibility 要素を検索し、棚卸し表を作成する
- 各要素を次の分類へ振り分ける
  - `削除候補`
  - `互換維持`
  - `正規導線へ置換`
  - `履歴資料として残す`
  - `要追加検証`
- `app/` や `app.main` 参照は、compatibility wrapper として維持が必要かを確認する
- ルート `libkoiki/` は、現行 `components/libkoiki/` と混同されるため、参照有無と削除可否を確認する
- README / docs / agent docs で、新規開発者が最初に見るべき正規導線を明確にする

### 実施結果

- legacy / compatibility 要素の棚卸し表を `docs/dev/dm12-legacy-compatibility-inventory.ja.md` に作成した
- root `app/` は `app.main:app` 互換 wrapper として維持する方針を確認した
- root `main.py` は既に存在しないことを確認した
- Git 管理下の root `libkoiki/` は `libkoiki/setup.py` のみであることを確認した
- root `libkoiki/setup.py` は旧 dependency に `passlib[bcrypt]` を含み、現行 `components/libkoiki/` と混同されるため削除候補とした
- root `libkoiki/` 配下の `__pycache__` / `libkoiki.egg-info` は Git 管理外のローカル artifact として扱う方針にした
- `apps/` は downstream 案件固有 backend API 実装の予約領域として維持する方針を確認した
- Docker / Compose / local dev script は `koiki_ref_app.asgi:app` を標準導線としていることを確認した
- `app.main:app` や旧 root `libkoiki/` の docs 参照は、履歴資料と現行手順を分けて後続 docs cleanup で扱う方針にした
- DM-12-A として root `libkoiki/setup.py` を削除し、unified prod コンテナ build / run、password login、タスク管理の作成 / 更新、コンテナログ確認で動作影響がないことを確認した

後続 PR 候補:

1. root `libkoiki/setup.py` 削除: 実施済み
2. 現行 docs の旧導線整理
3. `app.main:app` 互換終了判断
4. ローカル artifact 清掃は Git PR ではなく作業環境側で扱う

### 完了条件

- legacy / compatibility 要素の棚卸し表が作成されている
- `app/`、`libkoiki/`、`main.py`、`apps/`、旧 import、Docker/docs の `app.main` 参照について、削除・維持・置換の暫定判断が記録されている
- いきなり削除しない方針が明記されている
- 削除や entrypoint 変更が必要な場合、別 PR として切り出す方針が記録されている
- 新規メンバー向けに、v0.7 の正規開発対象が `components/libkoiki/` と `components/koiki_ref_app/` であることが明確になっている

### 検証

棚卸し時の確認例:

```powershell
rg -n "app\.main|from app|import app|libkoiki/|components/libkoiki|koiki_ref_app|sys.path|PYTHONPATH" . -S
rg --files app libkoiki apps tests .github docs docker scripts
git ls-files app libkoiki apps tests .github docs
```

削除・entrypoint 変更を別 PR で実施する場合は、少なくとも次を確認する。

```powershell
uv lock --check
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
```

### 注意

- DM-12 の初回 PR では、原則として削除や entrypoint 変更を行わない
- ルート `app/` は現時点で compatibility wrapper として扱われているため、削除判断には Docker / import / docs の横断確認が必要
- 削除判断は棚卸し PR とは分け、別 PR で小さく扱う
- セキュリティ残タスク `DM-09` と混ぜない

## 14. 推奨実行順

1. `DM-01`
2. `DM-02`
3. `DM-03`
4. `DM-04`
5. `DM-05`
6. `DM-06`
7. `DM-07`
8. `DM-08`
9. `DM-10`
10. `DM-11`
11. `DM-09`
12. `DM-12`

`DM-01` と `DM-02` は、他タスクの前に小さく処理する。
`DM-03` から `DM-05` は Pydantic v2 互換性としてまとめて扱えるが、差分が大きくなる場合は schema / service / logging に分ける。
`DM-08` は runtime 依存の脆弱性監査結果を優先して先行対応済み。
`DM-08` 後は `DM-10`、`DM-11`、`DM-09` の順に進める。
`DM-12` は削除系・導線整理系のため、`DM-09` のセキュリティ整理後に棚卸しから開始する。

## 15. 共通 NG 条件

- import error
- lock mismatch
- `poetry` 不在による実行失敗
- Alembic path 不一致
- ローカル実行時の `db` hostname 解決失敗
- migration 不要な修正で migration 差分を作ること
- security-sensitive な auth / SSO / SAML 挙動を unit test だけで済ませること
