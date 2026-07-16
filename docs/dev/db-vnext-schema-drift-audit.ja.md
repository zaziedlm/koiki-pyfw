# vNext DB schema drift監査

作成日: 2026-07-15

対象ブランチ: `topic/db-vnext-baseline`

基準Alembic head: `20260709001`

関連計画: `docs/dev/db-vnext-baseline-implementation-plan.ja.md`

## 1. 結論

DB-01の静的監査では、DB-02のM1を成立させない阻害差異は見つかっていない。M1は予定どおり、旧headの物理スキーマ意味論を維持しながら、管理対象12テーブルの改名と参照更新を行える。

確認された主なdriftは次のとおりで、DB-03～DB-05の対象に分類する。M1へ意味論変更を混入させない。

- Role／Permissionのtimestamp timezone契約
- Users、User SSO、SAML flow、business clockのPython defaultとserver defaultの不一致
- User SSO、SAML flow、business clockのPKと重複するORM側`id` Index
- `user_roles`のORM定義重複と`extend_existing=True`依存
- ORM cascadeとDB `ON DELETE`の責任境界、business clockの`LIMIT 1`参照

PostgreSQLサービスが停止中のため、旧headの物理スキーマはAlembic offline SQLとrevisionソースから確認した。実DB catalogの確認はDB-02の空PostgreSQL upgrade／downgrade／再upgradeで必ず行う。

## 2. 監査方法と判定基準

次の三者を比較した。

1. `db-schema-pre-vnext-202607`タグに保存した19本のAlembic revisionと、`upgrade head --sql`が生成するPostgreSQL DDL
2. `bootstrap_orm()`実行後の共有`Base.metadata`
3. Repository、relationship、fixture、`ops/`直接SQL、Docker／CI／運用文書の参照

差異の分類:

- `M1`: 名称変更と、改名を一意に成立させるための機械的整理
- `DB-03～05`: M1を阻害しない既存driftまたはvNextの意図的schema改善
- `対象外`: DB物理名ではない文字列、またはKOIKI-FW外部所有の契約
- `M1阻害`: M1実装前に独立修正が必要な差異

## 3. 管理対象12テーブルの契約比較

型の`timestamp tz`は`TIMESTAMP WITH TIME ZONE`、`timestamp`は`TIMESTAMP WITHOUT TIME ZONE`を表す。`py`はPython default、`srv`はserver defaultを表す。PK／UNIQUEが作る暗黙の索引と、明示Indexは区別する。

### 3.1 `users` -> `koiki_users`

- 旧head: `id` PK、`username varchar(50) NOT NULL UNIQUE`、`email varchar UNIQUE NULL`、`hashed_password/full_name NULL`、`is_active DEFAULT true NULL`、`is_superuser DEFAULT false NULL`、`created_at/updated_at timestamp tz NOT NULL DEFAULT now()`
- 明示Index: `id`、UNIQUE `username`、UNIQUE `email`、`full_name`
- ORM差異: `is_active/is_superuser`はpy defaultだけでsrv defaultなし。その他の物理契約は一致
- 実利用: `email`、`username`、PK検索、`is_active`filter + `id`order、role／permission eager load
- 分類: 改名は`M1`、default整理は`DB-03～05`

### 3.2 `roles` -> `koiki_roles`

- 旧head: `id` PK、`name varchar(50) NOT NULL UNIQUE`、`description NULL`、`created_at/updated_at timestamp NOT NULL`
- 明示Index: `id`、UNIQUE `name`
- ORM差異: timestampは`timezone=True`かつpy default／onupdateを持つ。旧headはtimezoneなし、defaultなし
- 実利用: role name、user-role関連、role-permission関連、security toolの一覧取得
- 分類: 改名は`M1`、timestamp／共通Base整理は`DB-03～05`

### 3.3 `permissions` -> `koiki_permissions`

- 旧head: `id` PK、`name varchar(100) NOT NULL UNIQUE`、`resource/action varchar(50) NULL`、`description text NULL`、`created_at/updated_at timestamp NOT NULL DEFAULT now()`
- 明示Index: `id`、UNIQUE `name`、`resource`、`action`
- ORM差異: timestampは`timezone=True`、py default／onupdateあり、srv defaultなし。旧headはtimezoneなし、srv default `now()`あり
- 実利用: permission name、resource/action、role-permission関連、security toolの一覧取得
- 分類: 改名は`M1`、timestamp／default／共通Base整理は`DB-03～05`

### 3.4 `user_roles` -> `koiki_user_roles`

- 旧head: PK `(user_id, role_id)`、FK `user_id -> users.id`、FK `role_id -> roles.id`、`ON DELETE`指定なし、追加Indexなし
- ORM差異: 物理契約は一致。`models/user.py`と`models/associations.py`に同一Table定義があり、後者が`extend_existing=True`に依存
- 実利用: User/Role relationship、security toolのJOIN
- 分類: 改名と`models/associations.py`への正本統一は`M1`、`ON DELETE CASCADE`と逆方向Indexは`DB-03～05`

### 3.5 `role_permissions` -> `koiki_role_permissions`

- 旧head: PK `(role_id, permission_id)`、FK `role_id -> roles.id`、FK `permission_id -> permissions.id`、`ON DELETE`指定なし、追加Indexなし
- ORM差異: 物理契約は一致。単一定義に対する`extend_existing=True`は不要
- 実利用: Role/Permission relationship、security toolのJOIN
- 分類: 改名と関連Table参照整理は`M1`、`ON DELETE CASCADE`と逆方向Indexは`DB-03～05`

### 3.6 `todos` -> `koiki_todos`

- 旧head: `id` PK、`title varchar(255) NOT NULL`、`description NULL`、`is_completed NOT NULL DEFAULT false`、`version NOT NULL DEFAULT 1`、`owner_id NOT NULL -> users.id ON DELETE CASCADE`、`created_at/updated_at timestamp tz NOT NULL DEFAULT now()`
- 明示Index: `id`、`title`、`owner_id`
- ORM差異: 物理契約は一致。`is_completed`にpy defaultもある
- 実利用: `(owner_id, created_at DESC)`一覧、`(id, owner_id)`取得、`(id, owner_id, version)`楽観ロックUPDATE、owner別count
- 分類: 改名は`M1`、複合Index判定は`DB-04`

### 3.7 `refresh_tokens` -> `koiki_refresh_tokens`

- 旧head: `id` PK、`user_id NOT NULL -> users.id ON DELETE CASCADE`、`token_hash varchar(255) NOT NULL`、`expires_at timestamp tz NOT NULL`、`is_revoked NOT NULL`、`device_info/last_used_at NULL`、`created_at timestamp tz NOT NULL DEFAULT now()`
- 明示Index: `id`、`user_id`、UNIQUE `token_hash`、`expires_at`、`is_revoked`
- ORM差異: 物理契約は一致。`is_revoked`はpy default false。`updated_at`は旧head／ORMともになし
- 実利用: token hash、`user_id`とactive/expiry、`created_at DESC`、expiry cleanup
- 分類: 改名は`M1`、`updated_at`復活、server default、複合／部分Indexは`DB-03～04`

### 3.8 `password_reset_tokens` -> `koiki_password_reset_tokens`

- 旧head: `id` PK、`user_id NOT NULL -> users.id ON DELETE CASCADE`、`token_hash varchar(255) NOT NULL`、`expires_at timestamp tz NOT NULL`、`is_used NOT NULL`、`used_at/ip_address/user_agent NULL`、`created_at/updated_at timestamp tz NOT NULL DEFAULT now()`
- 明示Index: `id`、`user_id`、UNIQUE `token_hash`、`expires_at`、`is_used`
- ORM差異: 物理契約は一致。`is_used`はpy default false
- 実利用: token hash + unused + expiry、user + unused + expiry、expiry cleanup
- 分類: 改名は`M1`、server defaultと複合／部分Indexは`DB-03～04`

### 3.9 `login_attempts` -> `koiki_login_attempts`

- 旧head: `id` PK、`email varchar(255) NOT NULL`、`user_id NULL -> users.id ON DELETE SET NULL`、`ip_address varchar(45) NOT NULL`、`user_agent/failure_reason NULL`、`is_successful NOT NULL`、`attempted_at timestamp tz NOT NULL DEFAULT now()`
- 明示Index: `id`、`email`、`user_id`、`ip_address`、`is_successful`、`attempted_at`
- ORM差異: 物理契約は一致。`created_at`は`attempted_at`のsynonym、`updated_at`はなし
- 実利用: email／IP + failure + time range + descending order、email + success + descending order、time cutoff delete
- 注意: User relationshipのORM `delete-orphan`とDB `SET NULL`の意図をDB-03／DB-09で照合する
- 分類: 改名は`M1`、cascade契約と複合／部分Indexは`DB-03～04`

### 3.10 `user_sso` -> `kkref_user_sso_links`

- 旧head: `id` PK、`user_id NOT NULL -> users.id ON DELETE CASCADE`、`sso_subject_id varchar(255) NOT NULL`、`sso_provider varchar(50) NOT NULL DEFAULT 'oidc'`、`sso_email/sso_display_name/last_sso_login NULL`、`created_at/updated_at timestamp tz NOT NULL DEFAULT now()`
- UNIQUE: `(sso_subject_id, sso_provider)`、`(user_id, sso_provider)`
- 明示Index: `sso_subject_id`、`sso_provider`、`user_id`、`last_sso_login`。旧headに`id`明示Indexなし
- ORM差異: `sso_provider`はpy defaultだけでsrv defaultなし。共通Baseの`id index=True`によりORM metadataに`ix_user_sso_id`あり
- 実利用: subject + provider、user + optional provider + `last_sso_login DESC`、optional provider + recent login
- 注意: 初期revisionは`user_id` FKを2回定義するが、後続のusers再構築が参照FKを全削除し、`user_sso_user_id_fkey` 1本を再作成する。M1 baselineに重複FKを写さない
- 分類: 改名は`M1`、default／重複Indexと複合／部分Indexは`DB-03～04`

### 3.11 `saml_auth_flow` -> `kkref_saml_auth_flows`

- 旧head: `id` PK、`request_id NULL`、`relay_nonce NOT NULL`、`sso_provider NOT NULL DEFAULT 'saml'`、`redirect_uri/user_id/subject_id/session_index/ticket_id/relay_expires_at/login_ticket_expires_at/consumed_at NULL`、`user_id -> users.id ON DELETE SET NULL`、`status NOT NULL DEFAULT 'authn_requested'`、`created_at/updated_at timestamp tz NOT NULL DEFAULT now()`
- UNIQUE: `ticket_id`、`relay_nonce`
- 明示Index: `status`、`ticket_id`、`relay_nonce`、`user_id`、`(status, login_ticket_expires_at)`。旧headに`id`明示Indexなし
- ORM差異: `sso_provider/status`はpy defaultだけでsrv defaultなし。共通BaseによりORM metadataに`ix_saml_auth_flow_id`あり
- 実利用: relay nonce、ticket IDの行ロック、`user_id + ticket_consumed + session_index + updated_at DESC`、status別expiry更新
- 分類: 改名は`M1`、default／CHECK／cleanup／Index再設計は`DB-03～04`

### 3.12 `kkbiz_business_clock` -> `kkbiz_business_clock`

- 旧head: `id` PK + `CHECK (id = 1)`、`mode varchar(16) DEFAULT 'REALTIME'`、`base_timezone varchar(64) DEFAULT 'Asia/Tokyo'`、`offset_days/offset_minutes DEFAULT 0`、`version DEFAULT 1`、`updated_by DEFAULT 'system'`、各列NOT NULL、frozen date/time/commentはNULL、`created_at/updated_at timestamp tz DEFAULT now()`
- 明示Index: なし。PK indexのみ
- migration DML: `id=1`、REALTIMEの初期行を`ON CONFLICT DO NOTHING`で投入
- ORM差異: mode/timezone/offset/version/updated_byはpy defaultだけでsrv defaultなし。共通BaseによりORM metadataに`ix_kkbiz_business_clock_id`あり
- 実利用: Repositoryは`LIMIT 1`、更新は`FOR UPDATE`。計画上は`id = 1`へ変更予定
- 分類: テーブル名は変更なし。M1暫定baselineで旧headのsrv default、CHECK、初期行DMLを維持。default／Index／Repository契約とseed移管は`DB-03～06`

## 4. drift一覧と処理先

| ID | 対象 | 差異／論点 | 分類 | 処理 |
| --- | --- | --- | --- | --- |
| D-01 | Users | booleanのsrv defaultは旧headのみ | DB-03～05 | M1は旧headを維持、最終contractでpy/srvを統一 |
| D-02 | Role | ORMはtimezone付き、旧headはtimezoneなし | DB-03～05 | 共通Base統一時に決定 |
| D-03 | Permission | timezoneとpy/srv defaultが不一致 | DB-03～05 | 共通Base統一時に決定 |
| D-04 | `user_roles` | Table定義が2か所 | M1 | `models/associations.py`を正本化 |
| D-05 | `role_permissions` | 不要な`extend_existing=True` | M1 | 関連Table正本化時に除去 |
| D-06 | Refresh token | `updated_at`がない | DB-03～05 | 復活と明示更新契約を実装 |
| D-07 | Login attempt | ORM cascadeとDB `SET NULL`の意図照合 | DB-03／09 | ユーザー削除契約テストで確定 |
| D-08 | User SSO | provider default、PK重複Index | DB-03～04 | srv defaultとIndex整理 |
| D-09 | SAML flow | provider/status default、PK重複Index | DB-03～04 | srv default、CHECK、Index整理 |
| D-10 | Business clock | default、PK重複Index、`LIMIT 1`、migration DML | M1 + DB-03～06 | M1は現行維持、後続で`id=1`とseed責任を最終化 |
| D-11 | FK/index全般 | 関連表の逆方向Indexと保持系FKの検索Index | DB-03～04 | `ON DELETE`と実クエリから判定 |

`M1阻害`に分類された項目はない。

## 5. 参照元の追従マトリクス

### 5.1 M1でコード変更が必要

- `components/libkoiki/src/libkoiki/models/`の`__tablename__`、関連Table、FK文字列、relationship `secondary`
- `components/koiki_ref_app/src/koiki_ref_app/models/`の`__tablename__`とFK文字列
- `components/libkoiki/src/libkoiki/models/user.py`と`associations.py`の`user_roles`正本化
- M1暫定Alembic baselineの全物理名、FK、制約、Index、business clock初期行DML

Repositoryの通常クエリはORMモデル参照のため、テーブル名の直接変更は原則不要。

### 5.2 M1で直接SQL変更が必要

- `ops/Makefile`
- `ops/scripts/run_security_test.sh`
- `ops/scripts/security_test_manager.sh`
- `ops/scripts/security_test_manager.ps1`
- `ops/README.md`の現行運用SQL例

対象は`users`、`roles`、`permissions`、`user_roles`、`role_permissions`の直接SQL参照である。

### 5.3 修正ではなく動作確認が必要

- `start-docker.ps1`、`start-docker.sh`、`docker-entrypoint.sh`
- `scripts/start-local-dev.ps1`
- `scripts/run-db-integration-tests.ps1`
- `ops/scripts/setup_security.py`
- PostgreSQL統合テストとCIのDB service
- auth、Todo、標準User SSO、SAML、business clockの代表smoke

これらはORM metadata、Alembic、API経由で動作し、管理対象の旧テーブル名を直接参照しない。

### 5.4 M1の改名対象外

- `user_table_sso_repository.py`のquoted `"user"`
- `scripts/sql/create_user_table_for_sso.sql`
- `scripts/setup-saml-user-table-e2e.ps1`、`.sh`
- API path/resourceの`users`、`todos`
- permission resource値の`users`、`todos`、`security`
- Pythonのclass名、変数名、ログメッセージの`user_sso`等
- `components/libkoiki/tests/unit/libkoiki/test_error_logging.py`のログ整形検証用`INSERT INTO users ...`文字列

quoted `"user"`は下流業務DB所有の外部契約であり、`koiki_users`へ変更しない。ログ検証用SQL文字列は実DBへ実行されず、物理schema参照に含めない。

## 6. M1暫定baselineへの転記規則

1. 旧headの最終物理schemaを正とし、テーブ名、FK参照先、制約／Index名に所有接頭辞を反映する。
2. 列順修正、途中列の追加／削除、データ移し替えなど、空DBの最終schemaに不要な歴史DMLは転記しない。
3. `kkbiz_business_clock(id=1)`の初期行投入だけは、M1の挙動互換のため暫定維持する。
4. ORM側にだけあるPK重複Indexや、旧headと異なるdefault／timezoneをM1で追加しない。
5. `user_sso` revisionの途中状態にある重複FKは転記せず、旧headの最終状態であるFK 1本を定義する。
6. M1のschema一致判定は新テーブル名、列、FK、制約、Index、defaultを旧head契約と比較する。ORMとの既存driftは本文書のD-01～D-11として保留し、DB-05の`alembic check`差分ゼロで解消する。

## 7. DB-01完了判定

- 12テーブルの所有、型、NULL、default、PK、FK／`ON DELETE`、UNIQUE、CHECK、Index、migration DMLを比較済み
- Repository／運用SQLの実利用を対応付け済み
- 変更必要、確認のみ、対象外の参照元を分類済み
- すべてのdriftに処理先があり、M1阻害差異はなし
- PostgreSQL実DB catalogによる最終確認はDB-02のM1検証で実施

以上により、DB-01は文書コミットの確定後に完了とし、DB-02のM1実装へ進行可能と判定する。
