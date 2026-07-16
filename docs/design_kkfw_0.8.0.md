# KOIKI-FW v0.8.0

## 1. 目的

本ドキュメントは、KOIKI-FW v0.8.0 の開発者向けアーキテクチャガイドです。

v0.8.0 では、v0.7.0 で整理した framework layer / reference application layer の分離を維持しつつ、フロントエンドを Next.js BFF から Vite + React SPA へ全面移行し、これに伴う Cookie セッション認証契約・CSRF/CSP 強化、および DB vNext ベースラインへの移行を実施しました。

開発者は、新規実装時に本ドキュメントと `docs/agent/` 配下の shared guidance、および `docs/frontend-spa-implementation-guide.ja.md` を参照し、実装場所、API ownership、認証契約、テスト範囲を判断してください。

## 2. v0.8.0 の位置づけ

v0.8.0 は、フロントエンドの Vite + React SPA 全面移行と、それに伴う認証契約・DB基盤の刷新を反映した開発ラインです。

主な焦点:

- フロントエンドを Next.js BFF から Vite + React SPA へ全面移行し、Next.js サーバーランタイムを撤去
- Cookie ベースのセッション認証契約（`/api/v1/auth/session/*`）を新設し、CSRF double-submit・CSP・セキュリティヘッダーを強化
- SSO / SAML の SPA コールバック対応と、リフレッシュトークン rotation・再利用検知・許可外リダイレクトURIの fail-closed 化
- DB を vNext ベースラインへ移行し、フレームワーク固有の接頭辞テーブル名の設計（`koiki_*`: libkoiki所有、`kkref_*`: koiki_ref_app所有、`kkbiz_*`: downstream業務所有）により owner を明確化した上で、reference bootstrap と development seeds を分離
- Todo API に実務的な version ベースの楽観的ロックを追加
- Agent Skills に `koiki-frontend-work` を新設し、frontend contract routing を整備

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
├── frontend/                         # Vite + React SPA reference frontend
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

`app.main:app` は `DM-12-C` で確認済みであり、v0.8.0 でも引き続き互換維持と判断しています。互換終了は外部利用状況を見て別途判断します。

### 3.4 `apps/`

`apps/` は downstream / customer-specific backend API の予約領域です。

ここに置く候補:

- 特定顧客・案件固有の API
- current reference app へ一般化しない workflow
- reusable framework に戻す前の業務拡張
- project-specific frontend/backend extension

現時点では workspace package としては扱わず、配置方針のみを明確化しています。

### 3.5 `frontend/`

`frontend/` は root 配置の Vite + React SPA reference frontend です。

v0.8.0 で Next.js BFF から全面移行し、Next.js サーバーランタイムは撤去されました。backend の Cookie セッション認証契約（`/api/v1/auth/session/*`）を `credentials: "include"` で利用し、CSRF・CSP・セキュリティヘッダーの契約に従います。本番では非特権 nginx が SPA を静的配信します（詳細はセクション9）。

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

- API: リクエストの検証、依存性の配線（DI）、レスポンスの整形
- Service: ユースケースの調整、ビジネスルールの実行、トランザクション境界の管理
- Repository: 永続化とクエリ処理
- Model: DBテーブルとリレーションの定義
- Schema: 検証済みの入出力契約の定義
- Core: 設定、認証、ミドルウェア、ロギング、DBセッション、セキュリティ関連ユーティリティ

下位 layer から上位 layer へ依存させないことを基本とします。

## 5. API Ownership Policy

API の配置は次の基準で判断します。

| API type | Primary location | 判断基準 |
| --- | --- | --- |
| reusable framework API | `components/libkoiki/` | 複数の application で同じ contract として使い回せるか |
| reference app API | `components/koiki_ref_app/` | current reference app の workflow・integration・UI contract に属するか |
| downstream customer API | `apps/` | 特定顧客・案件・業務に閉じているか |
| compatibility API | root `app/` | legacy import・entrypoint 互換のみを目的とするか |

判断が曖昧な場合は、次の順に確認します。

1. その API は他の application でも必要になりそうか
2. business rule を含んでいないか
3. `libkoiki` に置くと project-specific な前提が混ざらないか
4. アプリケーション層が、既存の framework capability を組み合わせるだけで解決できないか

迷う場合は、まず `components/koiki_ref_app/` または `apps/` 側から実装を始め、reusable な抽象化が明確になった段階で `components/libkoiki/` へ引き上げます。

## 6. Todo API の扱い

Todo API は、v0.8.0 時点でも `components/libkoiki/` の framework sample / starter capability として維持します。

理由:

- authenticated owner-scoped CRUD の最小例として機能している
- frontend の Todo sample と結びつき、runtime smoke に使える
- v0.7.0 以前からの migration continuity を保つ
- app layer へ移すと router, model, migration, frontend contract の確認範囲が広がる

v0.8.0 での変更点:

- `version` 列を追加し、実務的な version ベースの楽観的ロックを導入
- 更新は `UPDATE ... WHERE version = ?` による atomic 更新とし、rowcount チェックで競合を検出（read-then-write のレース窓を作らない）
- Todo が見つからない場合は 404、version が古い場合は 409（`ConflictException`）を返し、両者を明確に区別
- frontend のタスク一覧チェックボックス・編集ダイアログに 409 競合時のトースト表示とダイアログクローズを配線し、Query の再取得で最新状態を反映

重要:

- Todo が `libkoiki` にあることは、新規 business API を `libkoiki` に置く前例ではありません。
- 業務固有 rule を Todo に追加する場合は、reference app または downstream `apps/` の ownership を再判断します。
- Todo の optional router 化、app layer 移動、generic base capability 化は別タスクで扱います。

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

- application version: `0.8.0`
- `/health` response version: `0.8.0`
- `/` service info version: `0.8.0`

Production では OpenAPI docs / ReDoc は無効化されます。

v0.8.0 での変更点（Uvicorn worker 構成）:

- unified Compose stack における `UVICORN_WORKERS` のデフォルトを `4` から `1` に変更
- ECS（1コンテナ1プロセス）の運用モデルに合わせ、APIキャパシティは ECS service の task 数でスケールする方針とする
- コンテナ内で複数 worker にする場合は、CPU・メモリ・DBプールの余力、および background job や singleton 処理への影響を検証したうえで、明示的に `UVICORN_WORKERS` を上書きする例外運用とする

## 8. Auth / Security 基本方針

認証・認可の reusable behavior は `components/libkoiki/` が所有します。

主な framework scope:

- password hashing
- JWT token creation / verification
- refresh token handling
- user and RBAC foundation
- login security and audit event support（v0.8.0で、ログイン失敗試行を reject する前に永続化するよう修正し、失敗記録の欠落を防止）
- rate limiting and security middleware

reference app scope:

- SSO / SAML integration
- SAML auth flow state
- current project の IdP / deployment 前提
- app-level logging and frontend flow composition

v0.8.0 では、ブラウザ SPA 向けの Cookie セッション・CSRF・CSP・SSO/SAML コールバックの詳細契約を新設のセクション9で扱います。本節は libkoiki / reference app 間の役割分担の全体方針として維持します。

security-sensitive change では unit test のみで済ませず、request / token / permission / redirect / session の integration 観点を含めます。

## 9. Frontend SPA 認証契約

v0.8.0 で新設した、ブラウザ SPA 向けの Cookie セッション認証契約です。実装は `components/libkoiki/` が所有し、`components/koiki_ref_app/` が SSO/SAML 部分を composition します。

### 9.1 Cookie セッションエンドポイント

`/api/v1/auth/session/` 配下（`libkoiki` の `auth_session.py`）:

- `GET /csrf`: CSRF トークンを発行
- `POST /login`: パスワード認証し、access/refresh トークンを Cookie にセット
- `POST /register`: ユーザー登録
- `POST /refresh`: refresh トークンで access トークンを再発行
- `POST /logout`: 認証 Cookie を破棄
- `GET /me`: ログイン中ユーザー情報を取得

Cookie 定義:

| Cookie | 用途 | HttpOnly | Path | 有効期限 |
| --- | --- | --- | --- | --- |
| `koiki_access_token` | access token | ○ | `/` | `ACCESS_TOKEN_EXPIRE_MINUTES`（既定30分） |
| `koiki_refresh_token` | refresh token | ○ | `/api/v1/auth/session`（既定、`AUTH_REFRESH_COOKIE_PATH`で上書き可） | `REFRESH_TOKEN_EXPIRE_DAYS`（既定7日） |
| `koiki_csrf_token` | CSRF double-submit | ×（JS読み取り可） | `AUTH_COOKIE_PATH` | `AUTH_CSRF_COOKIE_MAX_AGE_SECONDS`（既定24時間） |

`SameSite` は既定 `lax`、`Secure` は `AUTH_COOKIE_SECURE`（production では true）に従います。

### 9.2 CSRF（double-submit）

- Cookie 認証によるすべての非安全メソッド（GET/HEAD/OPTIONS/TRACE以外）で CSRF 検証を必須化
- CSRF トークンは `nonce.issued_at.signature` 形式で HMAC 署名し、署名鍵 `AUTH_CSRF_SECRET` は JWT 署名鍵と別に管理
- Cookie とヘッダー（`x-csrf-token`）のトークンを `hmac.compare_digest` で突合し、TTL 超過時は無効
- Bearer 認証には CSRF を要求しない（Cookie 認証時のみ `request.state.auth_method == "cookie"` を条件に強制）

### 9.3 CSP / セキュリティヘッダー / 配信構成

`frontend/docker/nginx.conf` で以下を付与:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy`: `default-src 'self'` を基本に、`script-src`/`style-src`/`img-src`/`connect-src` 等を個別指定し、`object-src 'none'`・`frame-ancestors 'none'` を含む

production では frontend と backend を same-origin 構成にすることを明確化し、SPA は非特権 nginx（8080番）で静的配信します。

### 9.4 SSO / SAML SPA コールバック

`components/koiki_ref_app/` の `sso_auth.py` / `saml_auth.py` に session Cookie 発行を統合し、SPA からの SSO/SAML ログインでも 9.1 と同じ Cookie 契約に従います。

- 許可されていないリダイレクト URI は fail-closed（拒否）とし、許可リストにない宛先へのリダイレクトを行わない

### 9.5 トークンライフサイクル

- access token の既定有効期限を60分から30分に短縮
- refresh token の再利用（rotation 済みトークンの再送）を検知した場合、対象ユーザーの refresh token を全て失効
- 期限切れ・存在しない refresh token は通常の無効トークンとして扱い、reuse 検知とは区別
- rate limiter は app 起動時に共有インスタンスとして構成（session login: 10回/分、session register: 5回/分 等）

## 10. Database vNextベースライン

v0.8.0 で、DB スキーマを vNext ベースラインへ移行しました。旧スキーマとの互換は前提とせず、Alembic のマイグレーション履歴を単一のベースラインへリセットしています。

### 10.1 テーブル命名規則と owner 分離

テーブル名に owner を明示する接頭辞を導入しました。

| 接頭辞 | owner | 対象テーブル例 |
| --- | --- | --- |
| `koiki_` | `components/libkoiki/` | `koiki_users`, `koiki_roles`, `koiki_permissions`, `koiki_user_roles`, `koiki_role_permissions`, `koiki_todos`, `koiki_refresh_tokens`, `koiki_password_reset_tokens`, `koiki_login_attempts` |
| `kkref_` | `components/koiki_ref_app/` | `kkref_user_sso_links`, `kkref_saml_auth_flows` |
| `kkbiz_` | downstream / business（`apps/`想定） | `kkbiz_business_clock` |

downstream 側が所有する既存の `user` テーブル（quoted）は、この framework 管理 metadata の対象外として明確に区別します。

### 10.2 Alembic ベースライン再設定

- 従来の migration 履歴（初期マイグレーションから各種 add/rename/fix migration まで）を単一の `vnext_baseline` migration に統合
- 旧スキーマとの互換は目的とせず、vNext を新規の正規スキーマとして再定義
- 詳細な制約・索引設計は `docs/dev/db-vnext-index-design.ja.md`、スキーマ契約は `docs/dev/db-vnext-schema-contract.ja.md` を参照

### 10.3 Reference bootstrap と development seeds の分離

- `koiki_ref_app.bootstrap.reference_seed`: production を含むあらゆる環境で安全に、何度実行しても同じ結果になるデータ投入のみを行う（roles、permissions、これらの関連付け、business-clock singleton）。ユーザーやパスワードは一切作成しない
- `ops/security/dev_users.py`: 開発用管理ユーザー等、dev 環境専用のシードを分離。`ops/tests/test_development_seed_guard.py` で本番環境への混入を防止するガードを検証

### 10.4 認証・SAMLテーブルの運用メンテナンス方針

- Web アプリケーションおよび `libkoiki` は、認証・SAML データの定期 cleanup を起動しない方針に変更（従来 web runtime 内で実行していた `auth_data_cleanup` を撤去）
- ECS では Web コンテナとタスク数を独立にスケールするため、保持・削除処理は EventBridge Scheduler 起動の ECS Scheduled Task 等、業務システム側の単一実行バッチ基盤に集約する
- 対象テーブル: `koiki_login_attempts`（保持期限超過分の削除）、`koiki_refresh_tokens` / `koiki_password_reset_tokens`（`expires_at`超過分の削除）、`kkref_saml_auth_flows`（期限切れ状態遷移後の削除）
- 保持期間の決定はセキュリティ監査・認証運用側の責務とし、フレームワーク側で既定値を持たない。詳細は `docs/dev/auth-table-maintenance.ja.md` を参照

## 11. Database / Migration

v0.8.0 の Alembic 正規導線:

```powershell
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
```

migration ownership:

- reference app DB schema は `components/koiki_ref_app/alembic/`
- v0.8.0 では、migration 履歴は単一の `vnext_baseline` migration から開始する（セクション10.2参照）
- local host 実行では DB host に `localhost` を使う
- Docker 内実行では DB host に `db` を使う

DB table 作成は Alembic migrations で管理します。runtime startup は migration 済み schema を前提に DB connection を検証します。

## 12. Testing Strategy

テスト配置:

- framework behavior: `components/libkoiki/tests/`
- reference app behavior: `components/koiki_ref_app/tests/`
- cross-cutting / integration / e2e / agent guidance: root `tests/`
- frontend SPA behavior: `frontend/src/` 配下（コンポーネントと同居する `*.test.tsx`）、`vitest` を使用

基本コマンド（backend）:

```powershell
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
uv run --locked pytest tests/unit/agent_guidance
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

基本コマンド（frontend）:

```powershell
npm run check-types
npm run lint
npm test
npm run build
```

DB integration は必要なタスクでのみ明示的に実行します。frontend の4コマンドは `.github/workflows/frontend-ci.yml` で `dev/v0.8` への push / PR 時に自動実行されます。

Codex などの agent 環境では、`DEBUG=release` が混入する場合があります。repository validation では `DEBUG=True` または `DEBUG=False` を明示します。

## 13. Agent Guidance

v0.8.0 でも agent-facing guidance は repository boundary と API ownership に追随しています。想定する対応 AI コーディングエージェントは Codex、Claude Code、GitHub Copilot で、それぞれ向けのファイル群を整備しています。

正本:

- `AGENTS.md`
- `docs/agent/`
- `docs/agent/skills/`

v0.8.0 での変更点:

- `docs/agent/skills/koiki-frontend-work/`: root `frontend/` の Vite + React SPA 実装・レビュー専用スキルを新設し、API contract 変更時に owning backend skill と併用する運用を整備
- `docs/agent/skills/koiki-frontend-work/references/frontend-contract.md`: frontend contract チェックリストの参照資料として追加

adapter / integration（エージェント別）:

- Codex: `AGENTS.md`（root entrypoint）
- Claude Code: `CLAUDE.md`、`.claude/skills/`
- GitHub Copilot: `.github/copilot-instructions.md`、`.github/instructions/*.instructions.md`

共通:

- `tests/unit/agent_guidance/prompt_cases.yaml`
- `docs/dev/agent-skill-checklist.md`

repository-side contract test:

```powershell
uv run --locked pytest tests/unit/agent_guidance
```

実 runtime の skill selection は repository-side test だけでは証明できないため、必要に応じて `agent-skill-results.json` をローカル記録として使います。

## 14. Release / Compatibility Notes

v0.8.0 で履歴資料として残すもの:

- `docs/design_kkfw_0.7.0.md`
- `docs/releases/KOIKI-FW_0.6.0.md`
- `docs/releases/KOIKI-FW_0.6.1.md`
- `docs/releases/KOIKI-FW_0.7.0.md`
- `docs/dev/v0.8-pre-cleanup-inventory.ja.md`（v0.8着手前の整理作業の記録。対象タスクは完了済み）

v0.8.0 で削除したもの（0.7.0時点の「履歴として残す」方針とは異なり、役目を終えたと判断して削除）:

- `docs/dev/v0.7-task-instructions/` ほか、完了済み v0.7 タスク群・フロントエンドSPA移行計画書・v0.7.0リリースチェック文書（削除理由と一覧は `docs/dev/v0.8-pre-cleanup-inventory.ja.md` を参照）

現行作業で優先するもの:

- `docs/design_kkfw_0.8.0.md`
- `docs/agent/`
- `docs/dev/deferred-maintenance-tasks.ja.md`
- component package source under `components/`

`app.main:app` 互換終了判断は `DM-12-C` で確認済みであり、v0.8.0 でも引き続き互換維持とします。

## 15. Developer Checklist

新規 backend change の前に確認すること:

1. 実装場所は `components/libkoiki/`, `components/koiki_ref_app/`, `apps/` のどれか
2. Todo sample を business API 配置の前例として扱っていないか
3. layer flow を守っているか
4. auth / SSO / SAML / RBAC / audit に触れるか
5. migration が必要か
6. frontend contract が変わるか
7. frontend contract が変わる場合、Cookie セッション・CSRF・CSP の契約（セクション9）に影響しないか。影響する場合は `koiki-frontend-work` スキルを owning backend skill と併用したか
8. test scope は unit / integration / e2e のどれが必要か
9. docs / agent guidance の更新が必要か

## 16. 関連文書

- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/app.md`
- `docs/agent/libkoiki.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `docs/agent/skills/koiki-frontend-work/SKILL.md`
- `docs/frontend-spa-implementation-guide.ja.md`
- `docs/dev/db-vnext-baseline-adr.md`
- `docs/dev/db-vnext-schema-contract.ja.md`
- `docs/dev/db-vnext-index-design.ja.md`
- `docs/dev/auth-table-maintenance.ja.md`
- `docs/dev/dm12-legacy-compatibility-inventory.ja.md`
- `docs/dev/dm14-api-ownership-boundary-policy.ja.md`
- `docs/dev/dm15-agent-guidance-skills-consistency.ja.md`
- `docs/dev/v0.8-pre-cleanup-inventory.ja.md`
- `docs/releases/KOIKI-FW_0.7.0.md`
