# 先送り保守事項 タスク分解

最終更新: 2026-05-02

関連計画:

- `docs/dev/deferred-maintenance-plan.ja.md`

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

## 10. `DM-09` Bandit false positive 方針整理

優先度: `P5`

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

### 完了条件

- Bandit の残件がレビュー可能な粒度に減る
- `# nosec` を使う場合は理由がコメントまたは文書に残る
- High severity が残らない

### 検証

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
```

## 11. `DM-10` SAML metadata XML parser hardening

優先度: `P5`

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

## 12. 推奨実行順

1. `DM-01`
2. `DM-02`
3. `DM-03`
4. `DM-04`
5. `DM-05`
6. `DM-06`
7. `DM-07`
8. `DM-08`
9. `DM-09`
10. `DM-10`

`DM-01` と `DM-02` は、他タスクの前に小さく処理する。
`DM-03` から `DM-05` は Pydantic v2 互換性としてまとめて扱えるが、差分が大きくなる場合は schema / service / logging に分ける。

## 13. 共通 NG 条件

- import error
- lock mismatch
- `poetry` 不在による実行失敗
- Alembic path 不一致
- ローカル実行時の `db` hostname 解決失敗
- migration 不要な修正で migration 差分を作ること
- security-sensitive な auth / SSO / SAML 挙動を unit test だけで済ませること
