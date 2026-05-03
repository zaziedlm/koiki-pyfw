# DM-08からDM-10 セキュリティ改修 実施計画

作成日: 2026-05-03

関連:

- `docs/dev/deferred-maintenance-tasks.ja.md`
- `docs/dev/deferred-maintenance-plan.ja.md`
- `docs/security/SECURITY_AUDIT_COMMANDS.md`

## 1. 結論

`docs/dev/deferred-maintenance-tasks.ja.md` の `DM-08` から `DM-10` は、実施対象の方向性としては妥当だが、セキュリティ改修の実施計画としては不足している。

不足している点:

- 監査結果の記録先と、残件を許容する場合の判断基準が未定義
- direct / transitive / dev tooling / runtime dependency の切り分け基準が弱い
- FastAPI / Starlette など互換性影響が大きい更新の確認範囲が未定義
- Bandit false positive を `# nosec` にする条件と、コード修正に回す条件が未定義
- SAML metadata XML parser hardening の攻撃入力テストが未定義
- セキュリティ修正後に最低限通すべき integration 寄りの検証範囲が弱い

以降の計画は、`DM-08` から `DM-10` をそれぞれ単独 PR に分ける前提で、実装判断・記録・検証の粒度を補う。

## 2. 共通方針

### PR 境界

- `DM-08`: 依存脆弱性対応のみ。`pyproject.toml` / `uv.lock` / 必要な互換修正に限定する。
- `DM-09`: Bandit の分類、false positive 抑制、実リスク修正のみ。依存更新は含めない。
- `DM-10`: SAML metadata XML parser hardening とテストのみ。関連 runtime dependency が不足する場合だけ依存定義を変更する。

### 監査記録

各タスクで、実行時点の結果をタスク本文または専用メモに残す。

記録する内容:

- 実行日
- 実行コマンド
- 検出件数
- 対応した ID
- 残件がある場合の理由
- 次に確認すべき条件

残件を許容できる条件:

- 修正版が存在しない
- transitive dependency で、上流の互換範囲を超える更新が必要
- dev / security tooling のみで runtime impact がない
- 実行環境由来で、アプリケーションの lockfile 変更では直せない

許容する場合でも、CVE / advisory ID、影響範囲、再確認条件を残す。

### 検証環境

PowerShell:

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv lock --check
```

DB integration は、DB 起動済みの場合のみ追加で実行する。

```powershell
.\scripts\run-db-integration-tests.ps1
```

## 3. `DM-08` pip-audit 検出依存更新

### 目的

`pip-audit` が検出する依存脆弱性を、runtime impact を優先して解消する。

### 実施手順

1. 現在の監査結果を JSON と通常出力で取得する。

```powershell
uv run --locked pip-audit --format=json --output=pip-audit-dm08-before.json
uv run --locked pip-audit
uv tree
```

2. 検出結果を分類する。

- runtime direct dependency
- runtime transitive dependency
- dev / test / security group dependency
- 実行環境側 dependency
- 修正版なし

3. 更新方針を決める。

- direct dependency は `pyproject.toml` の上限範囲内で更新できるか確認する。
- transitive dependency は、親 dependency の互換範囲を確認してから更新する。
- FastAPI / Starlette / AnyIO / Pydantic 周辺は API・middleware・auth の回帰範囲を広めに取る。
- `pip` 自体の検出は、プロジェクト lockfile で扱えるか、実行環境更新が必要かを分けて記録する。

4. 依存を更新する。

通常は次の順で進める。

```powershell
uv lock --upgrade-package <package>
uv sync --locked --group dev --group test --group security
uv lock --check
```

`pyproject.toml` の version range 変更が必要な場合のみ、`uv add` または手動編集後に `uv lock` を実行する。

5. 更新後の監査結果を取得する。

```powershell
uv run --locked pip-audit --format=json --output=pip-audit-dm08-after.json
uv run --locked pip-audit
```

### 完了条件

- runtime dependency の修正可能な脆弱性が解消されている
- 残件がある場合、ID・影響範囲・未対応理由・再確認条件が記録されている
- `uv.lock` と `pyproject.toml` の整合性が取れている
- FastAPI / Starlette 周辺を更新した場合、API / auth / middleware の主要テストが通っている

### 最低検証

```powershell
uv lock --check
uv run --locked pytest --collect-only components/libkoiki/tests components/koiki_ref_app/tests tests -m "not db_integration"
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_auth_service_comprehensive.py
uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_service.py components/koiki_ref_app/tests/unit/app/services/test_sso_service.py
```

FastAPI / Starlette / middleware 変更が含まれる場合:

```powershell
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
```

## 4. `DM-09` Bandit false positive 方針整理

### 目的

Bandit の検出結果を、コード修正すべき実リスクと false positive に分ける。

### 実施手順

1. JSON と通常出力で現状を取得する。

```powershell
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o bandit-dm09-before.json
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level low
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
```

2. 検出を分類する。

- High: 原則コード修正。残す場合は明示レビュー必須。
- Medium: 実リスク確認後、コード修正または局所 `# nosec`。
- Low: false positive 方針に従って抑制可。

3. false positive 抑制のルールを適用する。

- `# nosec` は、該当行が定数・テスト専用値・既知の安全な fallback である場合に限定する。
- `# nosec` を使う場合は、同じ行または直前コメントに理由を短く残す。
- 広域除外は、同種の false positive が多数あり、局所抑制よりレビュー性が高い場合だけ検討する。
- 実リスクを隠す恐れがある plugin 全体除外は避ける。

4. 実リスクがあるものはコード修正する。

想定例:

- OAuth2 token type 定数に対する `B106`: secret ではない固定 token type なら局所 `# nosec`。
- security event name 定数に対する `B105`: secret ではないログ分類名なら局所 `# nosec`。
- logging fallback の `B110`: 例外握りつぶしが妥当か確認し、可能なら例外型を絞る。握りつぶしが設計上必要な場合は理由付き `# nosec`。

5. 更新後の結果を取得する。

```powershell
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o bandit-dm09-after.json
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
```

### 完了条件

- High severity が残っていない
- Medium severity の残件は理由付きでレビュー可能になっている
- `# nosec` は局所的で、理由が追跡できる
- 実リスクのある logging / exception handling はコード修正されている

### 最低検証

```powershell
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
uv run --locked pytest --collect-only components/libkoiki/tests components/koiki_ref_app/tests tests -m "not db_integration"
```

ログ sanitizer や auth 定数に触れた場合:

```powershell
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/test_input_logging.py
uv run --locked pytest components/libkoiki/tests/unit/libkoiki/services/test_auth_service.py components/libkoiki/tests/unit/libkoiki/services/test_login_security_service.py
```

## 5. `DM-10` SAML metadata XML parser hardening

### 目的

外部 SAML metadata XML の parse を、標準 `xml.etree.ElementTree` から安全な parser に置き換える。

### 実施判断

`defusedxml` を採用する。

理由:

- 対象は外部から取得した XML
- `defusedxml` は既に `uv.lock` に存在する
- runtime import が必要なため、直接 runtime dependency として `pyproject.toml` に追加されているか確認する

`defusedxml` が transitive dependency のみの場合は、偶然の transitive dependency に依存せず、runtime dependency として明示する。

### 実施手順

1. 現状の XML parse 箇所を確認する。

```powershell
rg -n "xml\\.etree|ET\\.fromstring|defusedxml" components/koiki_ref_app/src/koiki_ref_app/services components/koiki_ref_app/tests -S
```

2. parser を置き換える。

- `import xml.etree.ElementTree as ET` を `from defusedxml import ElementTree as ET` へ置き換える。
- `ET.ParseError` に加えて、`defusedxml.common.DefusedXmlException` を logging / error handling の対象にする。
- 複数箇所の `ET.fromstring` は、必要なら helper に集約する。
- 既存の `error_type` logging 方針を維持し、raw exception message を structured log に出さない。

3. 攻撃入力テストを追加する。

追加候補:

- DOCTYPE を含む metadata が拒否される
- 外部 entity を含む metadata が拒否される
- entity expansion 系の入力が拒否される
- 拒否時のログが `error_type` のみで、raw XML や raw exception を含まない

4. SAML metadata の通常処理が維持されることを確認する。

- signing certificate 抽出
- `entityID` 抽出
- redirect / post の SSO URL 抽出
- cache 更新と `force_refresh`

### 完了条件

- 外部 XML parse に標準 `xml.etree.ElementTree` を使っていない
- 悪意ある XML 入力が拒否される
- 既存の SAML metadata loader の正常系が壊れていない
- logging sanitizer / error logging 方針が維持される
- 必要な runtime dependency が明示されている

### 最低検証

```powershell
uv lock --check
uv run --locked pytest components/koiki_ref_app/tests/unit/app/services/test_saml_support_logging.py components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
uv run --locked bandit -r components/koiki_ref_app/src/koiki_ref_app/services/saml_metadata_loader.py
```

SAML metadata loader の通常処理テストが別ファイルにある場合は、それも追加で実行する。

```powershell
rg -n "SAMLMetadataLoader|get_signing_certificates|get_idp_entity_id|get_sso_service_url" components/koiki_ref_app/tests -S
```

## 6. 推奨順序

1. `DM-10`
2. `DM-09`
3. `DM-08`

理由:

- `DM-10` は明確な実装リスクを直接下げられ、依存更新の影響範囲も限定的
- `DM-09` は `DM-10` 後の Bandit 結果も含めて整理できる
- `DM-08` は監査 DB と依存最新版に左右されるため、PR 作成直前の結果で判断するのがよい

ただし、`pip-audit` で runtime の High / Critical が出ている場合は `DM-08` を最優先にする。

## 7. 最終ゲート

`DM-08` から `DM-10` の全完了後に、次を実行する。

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv lock --check
uv run --locked pip-audit
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
uv run --locked pytest --collect-only components/libkoiki/tests components/koiki_ref_app/tests tests -m "not db_integration"
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
```

DB integration 実行環境がある場合:

```powershell
.\scripts\run-db-integration-tests.ps1
```

## 8. DM-08 から発生した後続タスク

### `DM-11` password hashing backend の passlib 脱却

`DM-08` の依存更新とコンテナ実行確認により、`passlib 1.7.4` / `bcrypt 4.1+` の互換 warning が確認された。

`DM-08` では差分を依存脆弱性対応に留めるため、暫定的に `bcrypt>=4.0.1,<4.1.0` へ固定した。

ただし、`passlib 1.7.4` は古く、`bcrypt` の新しい API 変更に追従していない。v0.7.0 の土台整備としては、`libkoiki.core.security.get_password_hash()` / `verify_password()` の境界を維持しつつ、内部実装を `bcrypt` 直利用へ移行するのが望ましい。

詳細は `docs/dev/deferred-maintenance-tasks.ja.md` の `DM-11` を参照する。
