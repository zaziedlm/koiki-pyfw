# vNext DB schema contract

作成日: 2026-07-15

対象: KOIKI-FW管理対象12テーブル（外部所有のquoted `"user"`は対象外）

関連:

- `docs/dev/db-vnext-baseline-implementation-plan.ja.md` のDB-03
- `docs/dev/db-vnext-schema-drift-audit.ja.md`
- M1コミット `21ded0a`（暫定baseline）

## 1. この文書の位置付け

本書はDB-03で確定する最終schema contractである。M1 baselineは旧headの意味論を保つ暫定物であり、本書との差分はDB-04、DB-06、DB-05でまとめて反映する。M1のテーブル名変更を巻き戻したり、旧schemaとの互換を維持したりするものではない。

`SSO_LINK_BACKEND=user_table`が参照するquoted `"user"`は下流業務DBが所有する外部テーブルであり、本書、Alembic baseline、接頭辞変更の対象外とする。

## 2. 全体契約

### 2.1 命名と共通カラム

- 共有`MetaData`には計画書3.2節の`pk`、`fk`、`uq`、`ix`、`ck`命名規則を設定する。
- 通常エンティティのPKは`id INTEGER`とし、PKと重複する`id`単独Indexは作らない。
- `created_at`は`TIMESTAMP WITH TIME ZONE NOT NULL`、Python defaultなし、`server_default=now()`とする。
- 可変エンティティの`updated_at`は同型・`NOT NULL`・`server_default=now()`とする。更新経路（service/repository）がUTC現在時刻を明示設定し、DB triggerや`onupdate`だけには依存しない。
- `koiki_login_attempts`は追記専用で`attempted_at`を記録時刻とし、`created_at`は互換alias、`updated_at`は持たない。
- 純粋な関連表`koiki_user_roles`と`koiki_role_permissions`はsurrogate PK、timestampを持たない。

### 2.2 defaultとNULL

DB単独のINSERTでも安全な値はPython defaultとserver defaultを同じ意味に揃える。識別子、秘密情報、外部主体ID、トークンhashはdefaultなしの`NOT NULL`である。任意の業務情報は空文字で代用せず`NULL`を使う。

| 種別 | Python default / server default |
| --- | --- |
| `is_active` | `True` / `true` |
| `is_superuser` | `False` / `false` |
| `is_completed` | `False` / `false` |
| `version` | `1` / `1` |
| `is_revoked` | `False` / `false` |
| `is_used` | `False` / `false` |
| SSO provider | `"oidc"` / `'oidc'` |
| SAML provider | `"saml"` / `'saml'` |
| SAML status | `"authn_requested"` / `'authn_requested'` |
| business clock mode/timezone/offset/version/updated_by | `REALTIME`、`Asia/Tokyo`、`0`、`1`、`system` / 同値 |

### 2.3 参照削除と保持

所有データと関連表は`ON DELETE CASCADE`、履歴を保持する参照は`ON DELETE SET NULL`とする。すべてのFK列は、親行削除時の参照探索を支える先頭列Indexを持つ。具体的なIndexの統合・複合化・部分Index化はDB-04で決定する。

| 参照元 | 参照先 | 動作 |
| --- | --- | --- |
| `koiki_todos.owner_id` | `koiki_users.id` | CASCADE |
| `koiki_refresh_tokens.user_id` | `koiki_users.id` | CASCADE |
| `koiki_password_reset_tokens.user_id` | `koiki_users.id` | CASCADE |
| `kkref_user_sso_links.user_id` | `koiki_users.id` | CASCADE |
| `koiki_user_roles.user_id` / `.role_id` | users / roles | CASCADE |
| `koiki_role_permissions.role_id` / `.permission_id` | roles / permissions | CASCADE |
| `koiki_login_attempts.user_id` | `koiki_users.id` | SET NULL |
| `kkref_saml_auth_flows.user_id` | `koiki_users.id` | SET NULL |

## 3. テーブル別契約

時刻型はすべて`TIMESTAMP WITH TIME ZONE`である（date/timeを除く）。`NN`は`NOT NULL`を表す。

### 3.1 `koiki_users`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id` | INTEGER, PK | 共通PK |
| `username` | VARCHAR(50), NN | UNIQUE、識別子 |
| `email` | VARCHAR, NULL | UNIQUE（NULLは複数可）、任意の連絡先 |
| `hashed_password` | VARCHAR, NULL | パスワード認証を使う場合のみ設定。平文は保存しない |
| `full_name` | VARCHAR, NULL | 任意の表示情報 |
| `is_active`, `is_superuser` | BOOLEAN, NN, §2.2 | 状態フラグ |
| `created_at`, `updated_at` | 共通可変列 | 監査時刻 |

`email`のNULL許可は、username主体の登録とSSOによるユーザー作成を許容する意図的な例外である。メールアドレスを識別子として受け取る書込み経路では、アプリケーションが非NULLを要求する。

### 3.2 `koiki_roles` と `koiki_permissions`

| テーブル | 列 | 型・NULL・default | 不変条件 |
| --- | --- | --- | --- |
| roles | `id`, `created_at`, `updated_at` | 共通可変列 | 共通Baseを使用 |
| roles | `name` | VARCHAR(50), NN | UNIQUE、識別子 |
| roles | `description` | VARCHAR(255), NULL | 任意の説明 |
| permissions | `id`, `created_at`, `updated_at` | 共通可変列 | 共通Baseを使用 |
| permissions | `name` | VARCHAR(100), NN | UNIQUE、識別子 |
| permissions | `resource`, `action` | VARCHAR(50), NULL | API resource値であり物理テーブル名とは独立 |
| permissions | `description` | TEXT, NULL | 任意の説明 |

### 3.3 `koiki_user_roles` と `koiki_role_permissions`

| テーブル | 列 | 制約 |
| --- | --- | --- |
| `koiki_user_roles` | `user_id`, `role_id` | INTEGER, NN, 複合PK。各FKはCASCADE。`role_id`先頭Indexを持つ |
| `koiki_role_permissions` | `role_id`, `permission_id` | INTEGER, NN, 複合PK。各FKはCASCADE。`permission_id`先頭Indexを持つ |

### 3.4 `koiki_todos`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | 共通可変列 | `updated_at`は更新時に明示更新 |
| `title` | VARCHAR(255), NN | 内容識別の必須入力 |
| `description` | TEXT, NULL | 任意 |
| `is_completed` | BOOLEAN, NN, §2.2 | 完了状態 |
| `version` | INTEGER, NN, §2.2 | CHECK `version >= 1`、楽観ロック |
| `owner_id` | INTEGER, NN | FK users、CASCADE |

### 3.5 `koiki_refresh_tokens`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | 共通可変列 | revoke / last-use時に`updated_at`を明示更新 |
| `user_id` | INTEGER, NN | FK users、CASCADE |
| `token_hash` | VARCHAR(255), NN | UNIQUE、秘密情報。平文tokenを保存しない |
| `expires_at` | timestamptz, NN | 期限後はcleanupで物理削除 |
| `is_revoked` | BOOLEAN, NN, §2.2 | revoke状態 |
| `device_info` | TEXT, NULL | 任意の端末情報 |
| `last_used_at` | timestamptz, NULL | 使用時刻 |

### 3.6 `koiki_password_reset_tokens`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | 共通可変列 | 使用時に`updated_at`を明示更新 |
| `user_id` | INTEGER, NN | FK users、CASCADE |
| `token_hash` | VARCHAR(255), NN | UNIQUE、秘密情報 |
| `expires_at` | timestamptz, NN | 期限後は使用済みを含めcleanupで物理削除 |
| `is_used` | BOOLEAN, NN, §2.2 | 使用済み状態 |
| `used_at` | timestamptz, NULL | 使用時刻 |
| `ip_address`, `user_agent` | VARCHAR(45), TEXT, NULL | 監査補助情報 |

### 3.7 `koiki_login_attempts`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id` | INTEGER, PK | 追記専用履歴 |
| `email` | VARCHAR(255), NN | 試行対象の識別子 |
| `user_id` | INTEGER, NULL | FK users、SET NULL。削除後も履歴保持 |
| `ip_address` | VARCHAR(45), NN | IPv4/IPv6文字列 |
| `user_agent`, `failure_reason` | TEXT / VARCHAR(100), NULL | 任意の監査情報 |
| `is_successful` | BOOLEAN, NN | 成否は書込み側が必ず指定。defaultなし |
| `attempted_at` | timestamptz, NN, srv `now()` | 公式の記録時刻。既定30日後に設定値でcleanup |

### 3.8 `kkref_user_sso_links`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | 共通可変列 | ログイン／メタデータ更新時に明示更新 |
| `user_id` | INTEGER, NN | FK users、CASCADE |
| `sso_subject_id` | VARCHAR(255), NN | providerと組でUNIQUE。外部主体識別子 |
| `sso_provider` | VARCHAR(50), NN, §2.2 | subjectおよびuserと組でUNIQUE |
| `sso_email` | VARCHAR(255), NULL | 外部属性。連絡先の正本にはしない |
| `sso_display_name` | VARCHAR(100), NULL | 外部表示属性 |
| `last_sso_login` | timestamptz, NULL | 最新SSOログイン時刻 |

### 3.9 `kkref_saml_auth_flows`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | 共通可変列 | 状態遷移時に明示更新 |
| `request_id` | VARCHAR(255), NULL | AuthnRequest ID |
| `relay_nonce` | VARCHAR(255), NN | UNIQUE、フロー識別子 |
| `sso_provider` | VARCHAR(50), NN, §2.2 | SAML provider |
| `redirect_uri` | VARCHAR(2048), NULL | 許可済みURIだけを書込み側で受入 |
| `user_id` | INTEGER, NULL | FK users、SET NULL。履歴保持 |
| `subject_id`, `session_index`, `ticket_id` | VARCHAR(255) / VARCHAR(512) / VARCHAR(255), NULL | `ticket_id`はUNIQUE。session indexはSLO用途 |
| `relay_expires_at`, `login_ticket_expires_at`, `consumed_at` | timestamptz, NULL | 状態別期限／消費時刻 |
| `status` | VARCHAR(30), NN, §2.2 | CHECK: `authn_requested`、`acs_verified`、`ticket_consumed`、`expired` |

`authn_requested`は`relay_expires_at`で、`acs_verified`は`login_ticket_expires_at`で`expired`へ遷移する。`ticket_consumed`と`expired`は設定可能な保持期間（既定30日）後にcleanupする。

### 3.10 `kkbiz_business_clock`

| 列 | 型・NULL・default | 不変条件・保持 |
| --- | --- | --- |
| `id` | INTEGER, PK | CHECK `id = 1`。Repositoryは常に`id = 1`で取得・ロックする |
| `mode` | VARCHAR(16), NN, §2.2 | CHECK: `REALTIME`、`OFFSET`、`FROZEN` |
| `base_timezone` | VARCHAR(64), NN, §2.2 | IANA timezone実在性はserviceで検証 |
| `frozen_business_date`, `frozen_business_time` | DATE / TIME, NULL | `FROZEN`では両方NN、その他では両方NULL |
| `offset_days`, `offset_minutes` | INTEGER, NN, §2.2 | 業務上限はserviceで検証 |
| `comment` | TEXT, NULL | 任意の操作説明 |
| `version` | INTEGER, NN, §2.2 | CHECK `version >= 1`、楽観ロック |
| `updated_by` | VARCHAR(255), NN, §2.2 | 更新主体 |
| `created_at`, `updated_at` | 共通可変列 | 更新時に明示更新 |

初期行`id = 1`の責務はDB-06でreference-app bootstrap seedへ移す。最終baselineはDMLを含めない。

## 4. 実装への引継ぎ

- DB-04: 本書のFK探索要件とRepositoryのクエリ形状から、単独・複合・部分Indexを確定する。
- DB-06: business clock初期行、role/permission等のreference-app bootstrap seedを実装する。
- DB-05: 本書の共通`MetaData`、default、CHECK、FK、共通カラムをORMと単一baselineへ反映し、`alembic check`を差分ゼロにする。
- DB-07～09: cleanup設定・実行経路、制約と削除動作のPostgreSQL/SQLite契約テスト、主要統合回帰を追加する。
