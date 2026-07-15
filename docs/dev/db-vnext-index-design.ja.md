# vNext DB 制約・Index設計

作成日: 2026-07-15

対象: DB-04。最終反映先はDB-05のORMと単一Alembic baselineである。

関連: `docs/dev/db-vnext-schema-contract.ja.md`、`docs/dev/db-vnext-baseline-implementation-plan.ja.md`

## 1. 判断基準

- PKとUNIQUEが作るIndexと同じ列・順序の明示Indexは作らない。
- すべてのFK列は、親行削除時に参照行を探索できるIndexの先頭列にする。
- 複合Indexは等価条件を先、範囲・並び順を後に置く。
- PostgreSQLの部分Indexは、repositoryの固定述語と一致する場合だけ採用する。`now()`のようなvolatile式を述語に含めない。
- 選択性の低い真偽値、status、providerだけのIndexは作らない。部分Indexの述語・複合Indexの一部として利用する。
- これは機能baselineの設計であり、数百万行での実行計画・書込みコストはDB-PERF-01で再評価する。

## 2. 採用する制約とIndex

| テーブル | 制約／Index | 根拠クエリ・目的 |
| --- | --- | --- |
| `koiki_users` | UNIQUE `(username)`、UNIQUE `(email)` | 認証・登録時の完全一致検索。NULL emailは複数可 |
| `koiki_roles` | UNIQUE `(name)` | security setupの完全一致検索 |
| `koiki_permissions` | UNIQUE `(name)` | security setupの完全一致検索 |
| `koiki_user_roles` | PK `(user_id, role_id)`、Index `(role_id)` | user起点JOIN、role削除時CASCADE探索 |
| `koiki_role_permissions` | PK `(role_id, permission_id)`、Index `(permission_id)` | role起点JOIN、permission削除時CASCADE探索 |
| `koiki_todos` | `(owner_id, created_at DESC)` | owner別一覧・count、owner削除時CASCADE探索 |
| `koiki_refresh_tokens` | UNIQUE `(token_hash)` | token hashの一点検索 |
|  | `(user_id, created_at DESC)` | ユーザー別トークン一覧と並び順、CASCADE探索 |
|  | `(user_id, expires_at) WHERE is_revoked = false` | 有効トークンのユーザー別検索 |
|  | `(expires_at)` | 期限切れcleanup |
| `koiki_password_reset_tokens` | UNIQUE `(token_hash)` | token hashの一点検索 |
|  | `(user_id)` | 使用済み行を含むCASCADE探索 |
|  | `(user_id, expires_at) WHERE is_used = false` | ユーザー別の有効token検索 |
|  | `(expires_at)` | 期限切れcleanup |
| `koiki_login_attempts` | `(email, attempted_at DESC) WHERE is_successful = false` | email別の失敗履歴・count |
|  | `(ip_address, attempted_at DESC) WHERE is_successful = false` | IP別の失敗履歴・count |
|  | `(email, attempted_at DESC) WHERE is_successful = true` | 最終成功ログイン検索 |
|  | `(user_id)` | user削除時SET NULL探索 |
|  | `(attempted_at)` | 保持期間cleanup |
| `kkref_user_sso_links` | UNIQUE `(sso_subject_id, sso_provider)` | 外部subject/provider検索と重複防止 |
|  | UNIQUE `(user_id, sso_provider)` | user/provider検索と一人一providerの保証 |
|  | `(user_id, last_sso_login DESC)` | provider未指定のuser別一覧、CASCADE探索 |
|  | `(sso_provider, last_sso_login DESC)` | provider指定のrecent一覧 |
|  | `(last_sso_login DESC) WHERE last_sso_login IS NOT NULL` | provider未指定のrecent一覧 |
| `kkref_saml_auth_flows` | UNIQUE `(relay_nonce)` | AuthnRequestフロー検索 |
|  | UNIQUE `(ticket_id)` | ticketの一点検索・`FOR UPDATE` |
|  | `(relay_expires_at) WHERE status = 'authn_requested'` | AuthnRequest expiry更新 |
|  | `(login_ticket_expires_at) WHERE status = 'acs_verified'` | ACS verified expiry更新 |
|  | `(updated_at) WHERE status IN ('expired', 'ticket_consumed')` | terminal flow保持期限cleanup |
|  | `(user_id)` | user削除時SET NULL探索 |
|  | `(user_id, updated_at DESC) WHERE status = 'ticket_consumed' AND session_index IS NOT NULL` | SLO用の最新session index検索 |
| `kkbiz_business_clock` | PK `(id)` | singletonの`id = 1`検索・ロック |

## 3. 不採用・削除するIndex

| 対象 | 不採用／削除 | 理由 |
| --- | --- | --- |
| 全テーブル | `id`単独Index | PKが同じ探索を担うため重複 |
| `koiki_users` | `full_name`、`is_active`単独Index | full name検索はなく、activeは低選択性。active user一覧は通常のPK順走査で十分 |
| `koiki_permissions` | `resource`、`action`単独Index | 現行Repository／運用経路に検索根拠がない |
| `koiki_todos` | `title`単独Index | 現行検索根拠がない。PK `(id)`でID+owner更新・取得は足りる |
| token／reset／login attempt | `is_revoked`、`is_used`、`is_successful`単独Index | 低選択性。採用済み部分Indexの述語にする |
| `kkref_user_sso_links` | subject/provider/user/last-loginの単独Index | UNIQUEまたは採用済み複合・部分Indexに包含される |
| `kkref_saml_auth_flows` | relay nonce、ticket ID、status単独Index | UNIQUEまたは状態別部分Indexに包含される |
| `kkbiz_business_clock` | `id`単独Index | PKと重複 |

## 4. 制約の確定

DB-03契約の次のCHECKを最終baselineへ実装する。名前は共有`MetaData`の命名規則で、目的名を明示して生成する。

| テーブル | CHECK |
| --- | --- |
| `koiki_todos` | `version >= 1` (`positive_version`) |
| `kkbiz_business_clock` | `id = 1` (`singleton`) |
| `kkbiz_business_clock` | `version >= 1` (`positive_version`) |
| `kkbiz_business_clock` | `mode IN ('REALTIME', 'OFFSET', 'FROZEN')` (`valid_mode`) |
| `kkbiz_business_clock` | `mode = 'FROZEN'`ではfrozen date/timeがともに非NULL、その他ではともにNULL (`frozen_value_pair`) |
| `kkref_saml_auth_flows` | `status IN ('authn_requested', 'acs_verified', 'ticket_consumed', 'expired')` (`valid_status`) |

IANA timezoneの実在性、offsetの業務上限、メール形式、パスワード規則は可変の業務規則であるためCHECKに入れずserviceで検証する。

## 5. 実装時の注意

- `koiki_users.email`などのUNIQUEは、明示Indexではなく`UniqueConstraint`で表す。
- `kkref_saml_auth_flows.ticket_id`はNULLを許す。PostgreSQLとSQLiteでUNIQUEのNULL許可契約をDB-08で確認する。
- SAML cleanupは`authn_requested`では`relay_expires_at`、`acs_verified`では`login_ticket_expires_at`を使う。現行repositoryは後者だけを条件にしているため、DB-07で状態別に修正する。
- `updated_at`を使うIndexの正しさは、DB-05で明示更新契約を実装した後にDB-08で検証する。
- DB-PERF-01で、部分Indexの実行計画、write amplification、table/index sizeを比較し、追加・削除・列順変更を再判断する。
