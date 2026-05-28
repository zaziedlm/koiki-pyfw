# Starlette / FastAPI セキュリティ依存更新計画

作成日: 2026-05-28

関連:

- `docs/dev/dm08-dm10-security-task-plan.ja.md`
- `docs/dev/deferred-maintenance-tasks.ja.md`
- `docs/security/SECURITY_AUDIT_COMMANDS.md`
- `pyproject.toml`
- `components/libkoiki/pyproject.toml`

## 1. 目的

`pip-audit` で検出された `starlette 0.52.1 / PYSEC-2026-161` を解消するため、Starlette を `1.1.0` へ更新する。

あわせて FastAPI は `0.136.3` を前提に更新する。

今回の主目的は Starlette の脆弱性解消であり、Prometheus 連携は現状 optional として扱う。

## 2. 現状

監査結果:

```text
starlette 0.52.1 PYSEC-2026-161 1.0.1
```

確認済みの依存関係:

- `fastapi==0.136.3` は `starlette>=0.46.0` を要求し、Starlette 1.1.0 と依存制約上は両立する。
- `starlette==1.1.0` は Python `>=3.10` を要求し、本プロジェクトの `>=3.11.7,<4.0` と両立する。
- `prometheus-fastapi-instrumentator==7.1.0` は `starlette<1.0.0,>=0.30.0` を要求するため、Starlette 1.1.0 と両立しない。
- 2026-05-28 時点で `prometheus-fastapi-instrumentator` の PyPI 最新は `7.1.0` であり、Starlette 1.x 対応版は未確認。

コード確認結果:

- `components/libkoiki/src/libkoiki/core/monitoring.py` は `prometheus_fastapi_instrumentator` / `prometheus_client` の import 失敗時に dummy 実装へ fallback する。
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` は `setup_monitoring` を import しているが、現状 `create_app()` 内で呼び出していない。
- Prometheus package 不在を模擬した import と `setup_monitoring(app)` 実行は成功し、`/metrics` が登録されないだけで runtime error にはならない。

## 3. 方針

Starlette 1.1.0 を優先する。

そのため、短期対応として `prometheus-fastapi-instrumentator` を direct dependency から外す。

理由:

- `PYSEC-2026-161` は runtime web framework 側の脆弱性であり、優先度が高い。
- 現状の Prometheus 連携は app startup で有効化されていない。
- `monitoring.py` に package 不在時の fallback が実装済みである。
- `prometheus-fastapi-instrumentator` の現行最新版は Starlette 1.x と依存制約上衝突する。

## 4. 変更対象

### root dependency

`pyproject.toml`:

- `fastapi>=0.136.1,<0.137.0` を `fastapi>=0.136.3,<0.137.0` へ更新する。
- `starlette>=1.1.0,<1.2.0` を direct dependency として追加する。
- `prometheus-fastapi-instrumentator>=7.1.0,<7.2.0` を削除する。

### libkoiki dependency

`components/libkoiki/pyproject.toml`:

- `fastapi>=0.136.1,<0.137.0` を `fastapi>=0.136.3,<0.137.0` へ更新する。
- `starlette>=1.1.0,<1.2.0` を direct dependency として追加する。

理由:

- `components/libkoiki/src/libkoiki/core/middleware.py` は `starlette.middleware.base` / `starlette.responses` / `starlette.types` を直接 import している。
- Starlette は FastAPI の transitive dependency ではなく、`libkoiki` の direct dependency として明示するのが妥当である。

### lockfile

`uv.lock`:

- `fastapi` を `0.136.3` へ更新する。
- `starlette` を `1.1.0` へ更新する。
- `prometheus-fastapi-instrumentator` が不要になっていることを確認する。
- `prometheus-client` が他の direct/transitive dependency から必要か確認する。

## 5. 実施手順

1. 変更前の監査結果を保存する。

```powershell
uv run --locked pip-audit --format=json --output=pip-audit-starlette-before.json
uv run --locked pip-audit
uv tree
```

2. `pyproject.toml` と `components/libkoiki/pyproject.toml` を更新する。

3. lockfile を更新する。

```powershell
uv lock --upgrade-package fastapi --upgrade-package starlette
uv sync --locked --group dev --group test --group security
uv lock --check
```

4. 解決後のバージョンを確認する。

```powershell
uv run --locked python -c "import fastapi, starlette; print(fastapi.__version__, starlette.__version__)"
uv tree | Select-String -Pattern "fastapi|starlette|prometheus"
```

期待値:

```text
fastapi 0.136.3
starlette 1.1.0
```

5. 変更後の監査結果を取得する。

```powershell
uv run --locked pip-audit --format=json --output=pip-audit-starlette-after.json
uv run --locked pip-audit
```

## 6. 検証範囲

### 最小確認

```powershell
$env:DEBUG='False'
uv lock --check
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.version)"
uv run --locked pytest components/libkoiki/tests/unit/core/test_audit_middleware.py
```

### FastAPI / Starlette 回帰確認

```powershell
$env:DEBUG='False'
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
```

### auth / SSO / SAML 重点確認

```powershell
$env:DEBUG='False'
uv run --locked pytest components/koiki_ref_app/tests/integration/app/api/test_auth_api.py
uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_sso_service.py
uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
uv run --locked pytest components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py
uv run --locked pytest components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py
```

### Prometheus optional fallback 確認

`prometheus-fastapi-instrumentator` を外した後、次が失敗しないことを確認する。

```powershell
$env:DEBUG='False'
uv run --locked python -c "from libkoiki.core.monitoring import PROMETHEUS_AVAILABLE, increment_user_registration; print(PROMETHEUS_AVAILABLE); increment_user_registration(); print('ok')"
uv run --locked python -c "from fastapi import FastAPI; from libkoiki.core.monitoring import setup_monitoring; app=FastAPI(); setup_monitoring(app); print([r.path for r in app.routes])"
```

期待値:

- `PROMETHEUS_AVAILABLE` は `False`
- import / counter increment / `setup_monitoring(app)` は成功する
- `/metrics` は登録されない

## 7. 完了条件

- `fastapi` が `0.136.3` に更新されている。
- `starlette` が `1.1.0` に更新されている。
- `prometheus-fastapi-instrumentator` が runtime dependency から外れている。
- `uv lock --check` が成功する。
- `PYSEC-2026-161` が `pip-audit` 結果から消えている。
- Prometheus package 不在時も `libkoiki.core.monitoring` の import と fallback が機能する。
- middleware / auth / SSO / SAML の主要テストが通っている。

## 8. 残件の扱い

Starlette 更新後も、監査結果には他 package の検出が残る可能性がある。

現時点の既知候補:

- `idna 3.13 -> 3.15`
- `mako 1.3.11 -> 1.3.12`
- `pip 26.0.1 -> 26.1`
- `python-multipart 0.0.26 -> 0.0.27`
- `urllib3 2.6.3 -> 2.7.0`

今回の PR で扱うかは、Starlette / FastAPI 更新の差分が安定した後に判断する。

原則:

- Starlette 脆弱性解消を最優先にする。
- 追加更新が lockfile のみで済み、回帰範囲が広がらないものは同時対応を検討する。
- FastAPI / Starlette と無関係な残件は、別 PR または別タスクとして記録してもよい。
- `pip` は runtime dependency か、監査実行環境側 dependency かを切り分けて記録する。

## 9. 後続判断

### Prometheus 連携

`prometheus-fastapi-instrumentator` の Starlette 1.x 対応版が公開されたら、再導入を検討する。

再導入時の条件:

- Starlette 1.x と依存制約上両立する。
- `setup_monitoring(app)` を有効化するかどうかを明示する。
- `/metrics` endpoint の公開要否、OpenAPI schema への含有要否、production exposure policy を決める。
- monitoring endpoint のテストを追加する。

### 代替 monitoring

`prometheus-fastapi-instrumentator` の対応が遅い場合は、次を比較する。

- `prometheus_client` 直利用
- ASGI middleware 自作
- OpenTelemetry metrics への移行

この判断は Starlette 脆弱性対応 PR には含めない。

## 10. 注意事項

- `components/libkoiki/` の reusable framework behavior と `components/koiki_ref_app/` の reference app composition を混ぜない。
- Prometheus 連携を外す変更は、monitoring capability の削除ではなく、Starlette 1.x 非対応 package の一時除外として扱う。
- `setup_monitoring(app)` を新たに有効化しない。
- root `app/` は compatibility wrapper として扱い、新規実装を追加しない。
- Codex 環境では `DEBUG=release` が混入する場合があるため、検証時は `DEBUG=True` または `DEBUG=False` を明示する。

## 11. 実施結果

実施日: 2026-05-28

実施内容:

- `pyproject.toml`
  - `fastapi>=0.136.3,<0.137.0` へ更新した。
  - `starlette>=1.1.0,<1.2.0` を direct dependency として追加した。
  - `prometheus-fastapi-instrumentator>=7.1.0,<7.2.0` を削除した。
- `components/libkoiki/pyproject.toml`
  - `fastapi>=0.136.3,<0.137.0` へ更新した。
  - `starlette>=1.1.0,<1.2.0` を direct dependency として追加した。
- `uv.lock`
  - `fastapi 0.136.1 -> 0.136.3`
  - `starlette 0.52.1 -> 1.1.0`
  - `prometheus-fastapi-instrumentator 7.1.0` を削除
  - `prometheus-client 0.25.0` を削除

解決確認:

```text
uv lock --check
  Resolved 85 packages

uv run --locked python -c "import fastapi, starlette; print(fastapi.__version__, starlette.__version__)"
  0.136.3 1.1.0
```

Prometheus optional fallback 確認:

```text
from libkoiki.core.monitoring import PROMETHEUS_AVAILABLE, increment_user_registration
  PROMETHEUS_AVAILABLE=False
  increment_user_registration() 成功

setup_monitoring(FastAPI()) 実行
  Prometheus monitoring disabled - package not installed
  /metrics は登録されない
```

`pip-audit` 結果:

```text
Found 7 known vulnerabilities in 5 packages

idna             3.13    CVE-2026-45409 3.15
mako             1.3.11  CVE-2026-44307 1.3.12
pip              26.0.1  CVE-2026-3219  26.1
pip              26.0.1  CVE-2026-6357  26.1
python-multipart 0.0.26  CVE-2026-42561 0.0.27
urllib3          2.6.3   PYSEC-2026-142 2.7.0
urllib3          2.6.3   PYSEC-2026-141 2.7.0
```

`starlette / PYSEC-2026-161` は検出結果から消えた。

検証結果:

```text
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.version)"
  0.7.0

uv run --locked pytest components/libkoiki/tests/unit/core/test_audit_middleware.py
  6 passed

uv run --locked pytest components/koiki_ref_app/tests/integration/app/api/test_auth_api.py
  11 skipped

uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_sso_service.py components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py
  16 passed

uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_service.py components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py
  35 passed

uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
  204 passed, 1 skipped, 11 deselected
```

既知 warning:

- `components/libkoiki/src/libkoiki/core/transaction.py` と `AsyncMock` の組み合わせによる既存 `RuntimeWarning`
- `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning

いずれも今回の Starlette / FastAPI 更新で新規に発生した失敗ではない。
