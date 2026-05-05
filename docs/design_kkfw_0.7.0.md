# KOIKI-FW v0.7.0

## 1. 目的

本ドキュメントは、KOIKI-FW v0.7.0 の開発者向けアーキテクチャガイドです。

v0.7.0 では、v0.6 系で拡張された認証・監査・Todo sample 基盤を維持しつつ、バックエンドを再利用可能な framework layer と reference application layer へ分離しました。

開発者は、新規実装時に本ドキュメントと `docs/agent/` 配下の shared guidance を参照し、実装場所、API ownership、テスト範囲を判断してください。

## 2. v0.7.0 の位置づけ

v0.7.0 は、ディレクトリ再編と ownership 整理を反映した release preparation 版です。

主な焦点:

- `components/libkoiki/` を reusable backend framework として整理
- `components/koiki_ref_app/` を reference application / backend starter として整理
- root `app/` を legacy import / entrypoint 互換 wrapper として限定
- `apps/` を downstream / customer-specific backend API の予約領域として明確化
- Todo API を `libkoiki` の framework sample / starter capability として暫定維持
- `uv` / component package / current test layout を現行開発導線として整理
- Agent Skills / Copilot / Claude wrappers が同じ API ownership 判断を参照できるよう整備

## 3. 正規ディレクトリ構成

```text
project-root/
├── app/                              # compatibility wrapper for legacy app.main:app imports
├── apps/                             # downstream/customer-specific backend API area
├── components/
│   ├── libkoiki/
│   │   ├── src/libkoiki/             # reusable framework implementation
│   │   └── tests/                    # framework-owned tests
│   └── koiki_ref_app/
│       ├── src/koiki_ref_app/        # reference app / backend starter
│       ├── alembic/                  # reference-app-owned migrations
│       └── tests/                    # reference-app-owned tests
├── frontend/                         # starter frontend
├── tests/                            # cross-cutting, e2e, integration, agent guidance tests
├── docs/                             # developer, release, and historical documentation
├── scripts/                          # local validation and development helpers
└── ops/                              # operational and security support assets
```

### 3.1 `components/libkoiki/`

`components/libkoiki/` は reusable backend framework layer です。

ここに置くもの:

- shared auth / token / password / user / RBAC behavior
- shared config / middleware / logging / transaction behavior
- reusable persistence, schema, repository, service patterns
- reusable API contracts
- explicitly documented starter/sample API behavior

ここに置かないもの:

- project-specific business rules
- customer-specific workflow
- reference app の UI contract に閉じた API
- downstream 案件の外部連携や専用 table

### 3.2 `components/koiki_ref_app/`

`components/koiki_ref_app/` は reference application backend layer です。

ここに置くもの:

- reference app 固有の business behavior
- app-level composition of `components/libkoiki/`
- SSO / SAML など current reference app の integration
- frontend と連携する application-level API contract
- reference app / backend starter として一般化できる実装

ここに置かないもの:

- reusable framework behavior の重複実装
- downstream customer-specific API
- root `app/` compatibility wrapper の実装追加

### 3.3 root `app/`

root `app/` は compatibility wrapper です。

現時点では `app.main:app` 互換を維持しますが、実装の正本ではありません。新規実装は `components/libkoiki/` または `components/koiki_ref_app/` に置きます。

`app.main:app` の互換終了判断は、v0.7.0 release preparation 後の `DM-12-C` で扱います。

### 3.4 `apps/`

`apps/` は downstream / customer-specific backend API の予約領域です。

ここに置く候補:

- 特定顧客・案件固有の API
- current reference app へ一般化しない workflow
- reusable framework に戻す前の業務拡張
- project-specific frontend/backend extension

現時点では workspace package としては扱わず、配置方針のみを明確化しています。

### 3.5 `frontend/`

`frontend/` は root 配置の starter frontend です。

v0.7.0 時点では reusable Python framework package には含めません。backend API contract、auth flow、Todo sample の UI 動作確認と組み合わせて reference app の利用例を提供します。

## 4. Layered Architecture

backend 実装では、原則として次の flow を守ります。

```text
API endpoint
  -> Service
    -> Repository
      -> Model / DB session
  -> Schema
  -> Core / Infrastructure
```

責務:

- API: request validation, dependency wiring, response shaping
- Service: use-case orchestration, business rules, transaction boundary
- Repository: persistence and query behavior
- Model: DB table and relationship definition
- Schema: validated input/output contract
- Core: config, auth, middleware, logging, DB session, security utilities

下位 layer から上位 layer へ依存させないことを基本とします。

## 5. API Ownership Policy

API の配置は次の基準で判断します。

| API type | Primary location | 判断基準 |
| --- | --- | --- |
| reusable framework API | `components/libkoiki/` | 複数 application で同じ contract として使える |
| reference app API | `components/koiki_ref_app/` | current reference app の workflow / integration / UI contract に属する |
| downstream customer API | `apps/` | 特定顧客・案件・業務に閉じる |
| compatibility API | root `app/` | legacy import / entrypoint 互換のみ |

判断が曖昧な場合:

1. その API は他 application でも必要か
2. business rule を含むか
3. `libkoiki` に置くと project-specific assumption が混ざるか
4. app layer が framework capability を compose するだけで解けるか

迷う場合は、まず `components/koiki_ref_app/` または `apps/` 側から始め、reusable abstraction が明確になってから `components/libkoiki/` へ戻します。

## 6. Todo API の扱い

Todo API は、v0.7.0 時点では `components/libkoiki/` の framework sample / starter capability として維持します。

理由:

- authenticated owner-scoped CRUD の最小例として機能している
- frontend の Todo sample と結びつき、runtime smoke に使える
- v0.6 系からの migration continuity を保つ
- v0.7.0 前に app layer へ移すと router, model, migration, frontend contract の確認範囲が広がる

重要:

- Todo が `libkoiki` にあることは、新規 business API を `libkoiki` に置く前例ではありません。
- 業務固有 rule を Todo に追加する場合は、reference app または downstream `apps/` の ownership を再判断します。
- Todo の optional router 化、app layer 移動、generic base capability 化は v0.7.0 後の別タスクで扱います。

## 7. Application Startup

標準 ASGI entrypoint:

```text
koiki_ref_app.asgi:app
```

compatibility entrypoint:

```text
app.main:app
```

Docker / compose / local dev script は `koiki_ref_app.asgi:app` を標準導線として扱います。`app.main:app` は legacy compatibility のために残します。

FastAPI metadata:

- application version: `0.7.0`
- `/health` response version: `0.7.0`
- `/` service info version: `0.7.0`

Production では OpenAPI docs / ReDoc は無効化されます。

## 8. Auth / Security / SSO / SAML

認証・認可の reusable behavior は `components/libkoiki/` が所有します。

主な framework scope:

- password hashing
- JWT token creation / verification
- refresh token handling
- user and RBAC foundation
- login security and audit event support
- rate limiting and security middleware

reference app scope:

- SSO / SAML integration
- SAML auth flow state
- current project の IdP / deployment 前提
- app-level logging and frontend flow composition

security-sensitive change では unit test のみで済ませず、request / token / permission / redirect / session の integration 観点を含めます。

## 9. Database / Migration

v0.7.0 の Alembic 正規導線:

```powershell
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
```

migration ownership:

- reference app DB schema は `components/koiki_ref_app/alembic/`
- local host 実行では DB host に `localhost` を使う
- Docker 内実行では DB host に `db` を使う

DB table 作成は Alembic migrations で管理します。runtime startup は migration 済み schema を前提に DB connection を検証します。

## 10. Testing Strategy

テスト配置:

- framework behavior: `components/libkoiki/tests/`
- reference app behavior: `components/koiki_ref_app/tests/`
- cross-cutting / integration / e2e / agent guidance: root `tests/`

基本コマンド:

```powershell
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
uv run --locked pytest tests/unit/agent_guidance
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

DB integration は必要なタスクでのみ明示的に実行します。

Codex などの agent 環境では、`DEBUG=release` が混入する場合があります。repository validation では `DEBUG=True` または `DEBUG=False` を明示します。

## 11. Agent Guidance

v0.7.0 では agent-facing guidance も repository boundary と API ownership に追随しています。

正本:

- `AGENTS.md`
- `docs/agent/`
- `docs/agent/skills/`

adapter / integration:

- `.claude/skills/`
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `tests/unit/agent_guidance/prompt_cases.yaml`
- `docs/dev/agent-skill-checklist.md`

repository-side contract test:

```powershell
uv run --locked pytest tests/unit/agent_guidance
```

実 runtime の skill selection は repository-side test だけでは証明できないため、必要に応じて `agent-skill-results.json` をローカル記録として使います。

## 12. Release / Compatibility Notes

v0.7.0 で履歴資料として残すもの:

- `docs/design_kkfw_0.6.0.md`
- `docs/releases/KOIKI-FW_0.6.0.md`
- `docs/releases/KOIKI-FW_0.6.1.md`
- `docs/dev/v0.7-*`
- `docs/dev/v0.7-task-instructions/`

現行作業で優先するもの:

- `docs/design_kkfw_0.7.0.md`
- `docs/agent/`
- `docs/dev/deferred-maintenance-tasks.ja.md`
- component package source under `components/`

`app.main:app` 互換終了判断は v0.7.0 release preparation 後に別タスクとして扱います。

## 13. Developer Checklist

新規 backend change の前に確認すること:

1. 実装場所は `components/libkoiki/`, `components/koiki_ref_app/`, `apps/` のどれか
2. Todo sample を business API 配置の前例として扱っていないか
3. layer flow を守っているか
4. auth / SSO / SAML / RBAC / audit に触れるか
5. migration が必要か
6. frontend contract が変わるか
7. test scope は unit / integration / e2e のどれが必要か
8. docs / agent guidance の更新が必要か

## 14. 関連文書

- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/app.md`
- `docs/agent/libkoiki.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `docs/dev/dm12-legacy-compatibility-inventory.ja.md`
- `docs/dev/dm14-api-ownership-boundary-policy.ja.md`
- `docs/dev/dm15-agent-guidance-skills-consistency.ja.md`
- `docs/releases/KOIKI-FW_0.7.0.md`
