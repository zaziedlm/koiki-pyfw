# vNext DB baseline 再構築 実施計画

作成日: 2026-07-14

対象ブランチ: `topic/db-vnext-baseline`

関連ADR: `docs/dev/db-vnext-baseline-adr.md`

## 1. 目的

開発途上で積み重なったAlembic revisionをvNextで単一baselineへ置き換え、空のPostgreSQL DBから一意に再現できるスキーマを作る。同時に、テーブル名を所有レイヤー別に整理し、制約名とインデックスを現行モデルおよびRepositoryの問い合わせに合わせて再設計する。

## 2. 確定方針

- 現在のDBは削除し、vNext DBを空DBから再作成する。
- 旧revisionからvNextへのupgradeと、vNextから旧スキーマへのdowngradeは提供しない。
- 旧revisionは作業開始前のGitタグで保存する。
- vNextは`down_revision = None`の単一baselineとする。
- baselineのdowngradeは空DBへ戻す用途だけを保証する。
- 旧テーブル名のVIEWやaliasは作らず、参照元を一括更新する。
- baselineはDDLだけを所有し、reference-app bootstrap seed、開発・E2E seed、downstream固有seedを分離する。
- PostgreSQLを正規DBとし、部分インデックスなど固有DDLの意図を明示する。
- `SSO_LINK_BACKEND=user_table`は下流業務DB向け互換アダプターとして維持するが、そのquoted `"user"`テーブルはAlembic baseline、接頭辞変更、管理対象12テーブルのschema contractに含めない。

## 3. 命名規則

### 3.1 所有レイヤー

| 所有レイヤー | 接頭辞 | 配置 |
| --- | --- | --- |
| 共有フレームワーク／starter | `koiki_` | `components/libkoiki/` |
| 参照アプリケーション | `kkref_` | `components/koiki_ref_app/` |
| 業務固有領域 | `kkbiz_` | 現在の`kkbiz`モデルと将来の下流業務モデル |

通常テーブルと関連テーブルは複数形、単一行テーブルだけは単数形とする。

| 現在名 | vNext名 |
| --- | --- |
| `users` | `koiki_users` |
| `roles` | `koiki_roles` |
| `permissions` | `koiki_permissions` |
| `user_roles` | `koiki_user_roles` |
| `role_permissions` | `koiki_role_permissions` |
| `todos` | `koiki_todos` |
| `refresh_tokens` | `koiki_refresh_tokens` |
| `password_reset_tokens` | `koiki_password_reset_tokens` |
| `login_attempts` | `koiki_login_attempts` |
| `user_sso` | `kkref_user_sso_links` |
| `saml_auth_flow` | `kkref_saml_auth_flows` |
| `kkbiz_business_clock` | `kkbiz_business_clock` |

`kkbiz_business_clock`は`CHECK (id = 1)`によって最大一行に制限する。削除禁止トリガーは導入せず、reference-app bootstrap seedとサービス初期化が`id = 1`の存在を保証する。Repositoryは`LIMIT 1`ではなく`id = 1`を対象とし、行が欠落した場合はサービスが同じ固定IDで再作成する。

`SSO_LINK_BACKEND=user_table`が参照するquoted `"user"`は、表中の旧`users`とは別物である。これは下流業務DBが所有する外部テーブルであり、`koiki_users`へ改名せず、baselineの作成・削除対象にも含めない。標準backendの`user_sso`だけを`kkref_user_sso_links`へ改名する。

### 3.2 制約・インデックス名

共有`MetaData`に、SQLAlchemy標準tokenを使う次の命名規則を設定する。

```python
{
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}
```

CHECK制約には`singleton`、`valid_status`、`positive_version`のような目的を表す`constraint_name`を必ず明示する。命名規則から生成した名前がPostgreSQLの識別子長上限を超える場合は、SQLAlchemyによる決定的な短縮へ任せ、手動短縮と混在させない。部分Indexなど、列名だけでは意味を表せないものに限り、上限内の簡潔な明示名を使う。共有Baseの`id`から`index=True`を外し、PKまたはUNIQUEが作る索引と重複する明示Indexを作らない。

### 3.3 default・NULL契約

- DBだけで書き込まれても安全な初期値を持つ真偽値、version、status等は、Python `default`と`server_default`を同じ意味へ揃える。
- ユーザー識別子、メールアドレス、パスワードハッシュ、トークンハッシュ、外部主体IDなどの識別・秘密情報は、defaultなしの`NOT NULL`とする。
- `created_at`はDBの`now()`を正式なserver defaultとする。
- `updated_at`はINSERT時のserver defaultを持てるが、PostgreSQLでは`onupdate`だけによる自動更新を期待しない。更新するサービスまたはRepositoryが更新時刻を明示する。
- optionalな業務情報は意図的にNULLを許可し、欠損を空文字defaultで隠さない。
- 例外が必要な列は、理由と書き込み経路をschema contract表へ記録する。

### 3.4 移植可能な最小CHECK

CHECKは、違反すると処理自体が成立しない構造的不変条件だけに限定する。PostgreSQL固有ENUMや関数は使わず、単純な比較、`IN`、`AND`、`OR`、`IS NULL`で表現する。

DBで強制する初期対象:

- `kkbiz_business_clock.id = 1`
- Todoとbusiness clockの`version >= 1`
- SAML flow statusが`authn_requested`、`acs_verified`、`ticket_consumed`、`expired`のいずれか
- business clock modeが`REALTIME`、`OFFSET`、`FROZEN`のいずれか
- `FROZEN`時はfrozen date/timeが両方非NULL、その他のmodeでは両方NULL

サービス検証に残す対象:

- IANA timezoneの実在確認
- business clock offsetの業務上限
- メール形式とパスワード規則
- 将来変更される可能性が高い入力・業務ポリシー

同じ制約についてPostgreSQLとSQLiteの契約テストを用意する。PostgreSQLを正規DBとしつつ、SQLiteテストでは制約式がdialect固有になっていないことを確認する。

### 3.5 FK削除動作

所有データと関連表は`ON DELETE CASCADE`、保持すべき履歴は`ON DELETE SET NULL`へ統一する。

| 参照元 | 参照先 | 削除動作 |
| --- | --- | --- |
| `koiki_todos.owner_id` | `koiki_users.id` | `CASCADE` |
| `koiki_refresh_tokens.user_id` | `koiki_users.id` | `CASCADE` |
| `koiki_password_reset_tokens.user_id` | `koiki_users.id` | `CASCADE` |
| `kkref_user_sso_links.user_id` | `koiki_users.id` | `CASCADE` |
| `koiki_user_roles.user_id` | `koiki_users.id` | `CASCADE` |
| `koiki_user_roles.role_id` | `koiki_roles.id` | `CASCADE` |
| `koiki_role_permissions.role_id` | `koiki_roles.id` | `CASCADE` |
| `koiki_role_permissions.permission_id` | `koiki_permissions.id` | `CASCADE` |
| `koiki_login_attempts.user_id` | `koiki_users.id` | `SET NULL` |
| `kkref_saml_auth_flows.user_id` | `koiki_users.id` | `SET NULL` |

履歴系の`user_id`はNULL可能とし、ユーザー削除後も履歴行を保持する。CASCADE／SET NULL対象のFK列には、親行削除時の参照行探索を支える先頭列Indexが存在することを確認する。

### 3.6 一時・履歴データの保持期間

保持期間はCHECKやDDLへ埋め込まず、設定値とcleanup処理で管理する。

| データ | 方針 |
| --- | --- |
| Login attempts | 業務テーブルメンテナンスで保持期間後に物理削除 |
| Refresh tokens | 業務テーブルメンテナンスで有効期限到達後に物理削除 |
| Password reset tokens | 業務テーブルメンテナンスで使用済みを含め有効期限到達後に物理削除 |
| SAML `authn_requested` | 業務テーブルメンテナンスで`relay_expires_at`到達時に`expired`へ状態更新 |
| SAML `acs_verified` | 業務テーブルメンテナンスで`login_ticket_expires_at`到達時に`expired`へ状態更新 |
| SAML terminal flows | 業務テーブルメンテナンスで`expired`／`ticket_consumed`を業務決定の保持期間後に物理削除 |

SAML `session_index`はSLOに利用するため、terminal化直後には削除しない。保持期間変更はアプリ設定で行い、schema migrationを要求しない。cleanupは冪等とし、対象件数、実行時刻、失敗を安全なログへ記録する。

### 3.7 共通カラムと例外

通常の可変エンティティは、共有Baseの`id`、`created_at`、`updated_at`をそのまま使用する。

- Role／Permissionは共通カラムの重複定義を削除し、共有Baseへ統一する。
- Refresh tokenはrevokeとlast-used更新を行うため、現在無効化されている`updated_at`を復活させる。
- Login attemptは追記専用履歴として`attempted_at`を正式な記録時刻とし、`updated_at`を持たない明示的例外とする。コード互換に`created_at` aliasが必要かは実装時に確認する。
- `koiki_user_roles`と`koiki_role_permissions`は純粋な関連表として、surrogate `id`とtimestampを持たない。
- 共通カラムを持たないモデルには、その理由と更新可否をschema contract表へ記録する。

## 4. インデックス設計の初期仮説

以下はbaselineへ無条件に採用する確定設計ではなく、DB-04でクエリ形状と制約運用から採否を決める初期仮説である。機能baselineでは、現行Repositoryの`WHERE`、`JOIN`、`ORDER BY`、cleanup、FK削除動作を根拠に、明らかな不足・重複を解消する。大規模データでの実行計画と書き込みコストの最終評価は、非ブロッキングな後続タスクDB-PERF-01で行う。複合Indexは原則として等価条件を先、範囲・並び替え条件を後に置く。

| テーブル | インデックス候補 |
| --- | --- |
| `koiki_todos` | `(owner_id, created_at DESC)` |
| `koiki_login_attempts` | `(email, attempted_at DESC) WHERE is_successful = false` |
| `koiki_login_attempts` | `(ip_address, attempted_at DESC) WHERE is_successful = false` |
| `koiki_login_attempts` | 最新成功ログイン用の`(email, attempted_at DESC) WHERE is_successful = true`、または成功・失敗を統合する`(email, is_successful, attempted_at DESC)`を比較 |
| `koiki_login_attempts` | `(user_id)`：`ON DELETE SET NULL`時の参照行探索 |
| `koiki_login_attempts` | `(attempted_at)` |
| `koiki_refresh_tokens` | UNIQUE `(token_hash)` |
| `koiki_refresh_tokens` | `(user_id, created_at DESC)` |
| `koiki_refresh_tokens` | `(user_id, expires_at) WHERE is_revoked = false` |
| `koiki_refresh_tokens` | `(expires_at)` |
| `koiki_password_reset_tokens` | UNIQUE `(token_hash)` |
| `koiki_password_reset_tokens` | `(user_id)`：`ON DELETE CASCADE`時の全参照行探索 |
| `koiki_password_reset_tokens` | `(user_id, expires_at) WHERE is_used = false` |
| `koiki_password_reset_tokens` | `(expires_at)`：使用済みを含む期限切れcleanup |
| `koiki_user_roles` | PK `(user_id, role_id)`、Index `(role_id)` |
| `koiki_role_permissions` | PK `(role_id, permission_id)`、Index `(permission_id)` |
| `kkref_user_sso_links` | UNIQUE `(sso_subject_id, sso_provider)` |
| `kkref_user_sso_links` | UNIQUE `(user_id, sso_provider)` |
| `kkref_user_sso_links` | `(user_id, last_sso_login DESC)` |
| `kkref_user_sso_links` | `(sso_provider, last_sso_login DESC)` |
| `kkref_user_sso_links` | `(last_sso_login DESC) WHERE last_sso_login IS NOT NULL`：provider指定なしのrecent検索 |
| `kkref_saml_auth_flows` | UNIQUE `(ticket_id)`、UNIQUE `(relay_nonce)` |
| `kkref_saml_auth_flows` | `(status, relay_expires_at)`：未完了AuthnRequestの失効処理 |
| `kkref_saml_auth_flows` | `(status, login_ticket_expires_at)` |
| `kkref_saml_auth_flows` | `(status, updated_at)`：terminal flowの保持期限cleanup |
| `kkref_saml_auth_flows` | `(user_id)`：`ON DELETE SET NULL`時の参照行探索 |
| `kkref_saml_auth_flows` | `(user_id, updated_at DESC) WHERE status = 'ticket_consumed' AND session_index IS NOT NULL` |

低選択性の真偽値、`status`、`provider`の単独Index、および利用箇所が確認できない`title`等の単独Indexは原則作らない。ただし、低選択性列を部分Indexの述語または複合Indexの一部として使う案は、機能baselineではクエリとの一致を確認し、性能上の有効性をDB-PERF-01で再評価する。

### 4.1 DB-PERF-01用中規模参照データセット

後続タスクDB-PERF-01の手動PostgreSQL性能検証では、次の中規模データセットを基準にする。このデータ生成と測定は、DB-00～DB-10の機能baseline完了条件には含めない。

| テーブル | 目標行数 |
| --- | ---: |
| `koiki_users` | 100,000 |
| `koiki_todos` | 1,000,000 |
| `koiki_login_attempts` | 5,000,000 |
| `koiki_refresh_tokens` | 500,000 |
| `koiki_password_reset_tokens` | 200,000 |
| `kkref_user_sso_links` | 100,000 |
| `kkref_saml_auth_flows` | 1,000,000 |
| roles／permissions | 各1,000以下 |

データ生成手順は固定seed値を使って再現可能にし、状態、期限、provider、ユーザーごとの行数に偏りを持たせて実利用に近づける。この大量データ検証は通常CIへ含めず、明示的な手動性能検証として実行する。CIでは小規模データを使い、schema、制約、Index定義、部分Index述語、クエリ結果の契約を検証する。

### 4.2 DB-PERF-01の性能検証根拠

性能検証はハードウェア依存の絶対時間を一律の合格閾値にせず、通常plannerの実行計画、buffer使用量、Index追加前後の相対比較を根拠にする。

- データ投入後に`ANALYZE`を実行してから測定する。
- 選択性の高い代表クエリが、通常のplanner設定で意図したIndexを利用することを確認する。
- `enable_seqscan = off`等でIndex利用を強制した結果を採用根拠にしない。
- `EXPLAIN (ANALYZE, BUFFERS)`の推定行数、実行行数、execution time、shared buffer hit/readを保存する。
- テーブルとIndexのサイズを記録し、Index追加による容量増加を把握する。
- cleanupのように多数行を処理するクエリではSequential Scanが合理的な場合があるため、一律に不合格としない。
- 認証履歴とトークンテーブルについて、Index追加前後の代表的なINSERT／UPDATE処理を同じ条件で比較し、書き込みコストの極端な悪化がないことを確認する。
- 採用・不採用判断には、実行計画と相対比較の証跡を添付する。

## 5. seedの責任分離

reference-app bootstrap seedは標準permission、標準role、role-permission関連、`kkbiz_business_clock(id=1)`を冪等に投入する。これは参照アプリの初期運用データであり、`components/libkoiki/`を利用する全アプリに必須のフレームワークデータではない。自然キーに基づいて不足分を作成し、無条件削除はしない。

開発・E2E seedだけがテストユーザー、ユーザーとroleの関連、固定パスワードを扱う。本番初期化、アプリ起動、Alembic upgradeからは呼ばず、本番相当環境では環境ガードによりfail closedとする。

downstreamアプリ固有seedは各downstreamアプリが所有し、このvNext baseline計画の実装対象には含めない。

## 6. 実施タスク

### 6.1 最初の実装マイルストーン M1: 管理対象テーブル名の機械的変更

最初の実装目標は、KOIKI-FW管理対象12テーブルの改名だけを一貫して完了し、greenなコミットを作ることである。DB-00とDB-01を前提にDB-02を実施し、次のコミットポイントとする。

```text
refactor(db)!: rename managed tables by ownership
```

M1に含める:

- `__tablename__`、関連Table、FK文字列、`secondary`参照の改名
- Repository、fixture、`ops/`、Docker、CI、現行運用文書にある管理対象テーブル名の更新
- 外部quoted `"user"`を改名対象から除外
- 現行カラム、NULL、default、FK削除動作、制約、Indexを極力維持した暫定vNext baseline
- 現行migrationが行う`kkbiz_business_clock(id=1)`の初期行投入を、M1の改名以外の挙動を変えないための暫定例外として維持
- 空PostgreSQL DBでのupgrade、downgrade base、再upgrade
- ORM metadataとDBテーブル名の一致
- 代表的なauth、Todo、SSO、SAML、business clockのsmoke

M1に含めない:

- 共通Baseとtimestamp契約の整理
- NULL／defaultの厳格化
- CHECK追加
- CASCADE／SET NULL方針の変更
- Index再設計と性能検証
- seed分離
- cleanupと保持期間の変更

M1は「現行スキーマ意味論を保った名前だけのbreaking change」としてレビューする。後続タスクは暫定baselineを更新して最終vNext baselineへ仕上げる。

M1の暫定baselineに限り、旧headの挙動互換のため`kkbiz_business_clock(id=1)`の初期行投入を含める。DB-06でこの投入責任をreference-app bootstrap seedへ移し、DB-05で最終化するbaselineからDMLを除去する。第2節の「baselineはDDLだけを所有」は最終vNext baselineの完了条件であり、M1の暫定例外を常態化しない。

M1コミット作成後は正式なレビューゲートで一度停止する。レビューで改名範囲、外部quoted `"user"`の非変更、暫定baselineの往復、代表smokeのgreenを承認するまで、DB-03以降のスキーマ意味論変更に着手しない。

M1の検証マトリクス:

- Alembic: `heads`、空PostgreSQL DBへの`upgrade head`、`downgrade base`、再`upgrade head`
- Schema: 管理対象12テーブルの新名、旧名不在、ORM metadataとDBのテーブル名一致、外部quoted `"user"`の非管理対象性
- Runtime: auth、Todo、標準`user_sso` backend、SAML、business clockの代表smoke
- Tooling: security setupと直接SQLを持つ`ops/`ツール、Docker起動経路、DB統合テスト実行経路
- Static audit: 実行コード、fixture、CI、現行運用文書の管理対象旧DBオブジェクト参照がゼロ。API resource名、Python変数名、ログ用のSQL文字列などDB物理参照でない同名語は判定根拠を残して除外

現行の`scripts/run-db-integration-tests.ps1`は認証APIとサービス統合テストが中心であり、Todo、SSO、SAML、business clockのM1検証を単独では網羅しない。M1では不足領域の既存テストを明示的に追加実行し、必要なら同スクリプトまたはM1専用検証入口へ統合する。

### DB-00: 作業境界の固定と旧履歴タグ

- 本計画とADRを確定する。
- 旧Alembic履歴の基準commitを`382920e4559150059f38160250aa04544c331101`、旧Alembic headを`20260709001`として確認する。
- 文書レビュー完了後、旧revisionを削除する前に、基準commitへannotated tag `db-schema-pre-vnext-202607`を作成する。
- annotated tag `db-schema-pre-vnext-202607`を`origin`へpushし、remoteから基準commitと旧revision一式を参照できることを確認する。
- タグから旧Alembic revision一式と旧head `20260709001`を参照できることを確認する。
- タグ名、commit、旧headを移行ノートへ記録する。

完了条件: `origin`上の`db-schema-pre-vnext-202607`から旧revision一式を復元でき、タグ対象commitと旧headが記録され、vNextの旧DB非互換が明記されている。remote tagの存在確認が終わるまでDB-02へ進まない。

### DB-01: スキーマと参照箇所の完全棚卸し

- ORM、関連Table、FK文字列、SQLAlchemy Core、生SQLを一覧化する。
- tests、`ops/`、seed、Docker、CI、現行文書の旧名参照を検索する。
- 各モデルを`koiki_`、`kkref_`、`kkbiz_`へ分類する。
- 旧Alembic head `20260709001`が生成する物理スキーマ、現行ORM metadata、Repository／運用SQLの実利用を12テーブルごとに比較し、schema drift監査表を作成する。
- schema drift監査表は`docs/dev/db-vnext-schema-drift-audit.ja.md`に記録し、M1実装と分離した文書専用コミットで固定する。
- schema drift監査表に型、NULL、Python／server default、PK、FKと削除動作、UNIQUE、CHECK、Index、migration内DMLを記録する。
- 各差異を「名称のみでM1対象」「M1を阻害しない既存driftでDB-03～DB-05対象」「M1を成立させない阻害差異」に分類し、判定根拠と対応タスクを記録する。
- `models/user.py`と`models/associations.py`にある`user_roles`重複定義を特定し、DB-02で単一の正本へ整理する方針と影響importを記録する。
- `user_table_sso_repository.py`のquoted `"user"`を外部所有テーブルとして棚卸しし、改名対象から除外する。

完了条件: 旧名ごとの変更対象が追跡され、同一テーブル定義の曖昧さがなく、外部quoted `"user"`がKOIKI-FW管理テーブルと明確に区別されている。12テーブルのschema drift監査表が完成し、すべての差異に分類、根拠、対応タスクがある。監査表がM1実装と分離した文書専用コミットで固定されている。M1阻害差異がある場合はDB-02へ進まず、独立修正の要否とコミット境界をレビューで決定する。

### DB-02: M1 管理対象テーブル名の変更と暫定baseline

- 全`__tablename__`、関連Table、FK参照を新名称へ変更する。
- `user_roles`は`models/associations.py`の関連Table定義を正本とし、`models/user.py`の重複定義と`extend_existing=True`への依存を解消する。`role_permissions`と同じ定義元からrelationshipが参照する。
- relationshipの文字列`secondary`と、管理対象テーブルを参照するSQLAlchemy Core定義を新名称へ変更する。
- Repository、fixture、metadata assertion、`ops/`、Docker、CI、現行運用文書の管理対象テーブル名を一括更新する。
- API resource名などDB名ではない文字列を機械的に変更しない。
- `SSO_LINK_BACKEND=user_table`の外部quoted `"user"`と下流向けセットアップSQLは変更しない。
- bootstrap後の共有metadataがKOIKI-FW管理対象の想定12テーブルを持つことを検証する。独立した`MetaData`を使う外部quoted `"user"`はこの件数に含めない。
- DB-00のタグ作成後に旧revision群をvNextの`versions/`から外し、`down_revision = None`の暫定vNext baselineを作成する。
- 暫定baselineは現行カラム、NULL、Python／server default、FK削除動作、制約、Indexを極力維持し、テーブル名変更以外の意味論変更を混入させない。
- 旧headの`kkbiz_business_clock(id=1)`初期行投入は暫定baselineに限って維持し、DB-06でreference-app bootstrap seedへ移管した後、最終baselineから除去する。
- 暫定baselineの`upgrade()`は空DBへ全DDLを作成し、`downgrade()`は依存関係の逆順で空DBへ戻す。
- 空PostgreSQL DBでupgrade、downgrade base、再upgradeを行い、ORM metadataとのテーブル名一致を確認する。
- 代表的なauth、Todo、SSO、SAML、business clockのsmokeを実行する。

完了条件: KOIKI-FW管理対象に旧テーブル名が残らず、外部quoted `"user"`が維持され、暫定baselineが単一headとして空PostgreSQL DBを往復できる。代表smokeが成功し、`kkbiz_business_clock(id=1)`の暫定投入を除いてテーブル名以外の意図的なschema／runtime挙動変更が差分に含まれていない。M1コミット`refactor(db)!: rename managed tables by ownership`をgreenな状態で作成できる。

### DB-03: 全管理テーブルのスキーマ契約監査

- 共有Baseへ制約命名規則付き`MetaData`を設定する設計を確定する。
- CHECK制約の`constraint_name`と標準tokenから期待名が生成されることを確認する。
- 共有PK `id`から重複する`index=True`を外す判断をschema contractへ反映する。
- Role／Permissionの共通カラム再定義を削除し、共有Baseへ統一する。
- Refresh tokenの`updated_at`復活と、Login attempt／関連表の例外契約を確定する。
- KOIKI-FW管理対象12テーブルについて、カラム型、NULL可否、Python default、server defaultを一覧化する。
- 第3.7節に基づき、可変エンティティの共通カラムと例外モデルを一覧化する。
- DB安全値についてPython defaultとserver defaultが同じ意味になっていることを確認する。
- 識別・秘密情報がdefaultなしの`NOT NULL`であることを確認し、例外があれば理由を記録する。
- PK、FK、`ON DELETE`、UNIQUE、CHECKが表すデータ不変条件を確認する。
- FK削除動作が第3.5節の所有・履歴方針と一致し、親行削除を支えるIndexがあることを確認する。
- status、mode、version、真偽値など、現在任意値を許す列へDB制約が必要か判断する。
- 第3.4節の最小CHECKをschema contractへ反映し、変更されやすい業務ルールを追加していないことを確認する。
- 各テーブルの保持期間、cleanup方法、削除時の参照整合性を確認する。
- 第3.6節の保持期間設定、terminal判定、物理削除条件をschema contractへ記録する。
- 認証トークン、ログイン履歴、SSO識別子など、機微データの保存目的と保持期間を記録する。
- ORM経由の書き込みだけでなく、seed、運用SQL、将来のバッチ処理でも成立するserver defaultを決める。
- 現在の定義を維持する項目と、vNextで意図的に厳格化する項目を区別して記録する。

完了条件: 全12テーブルのschema contract表が完成し、型、NULL、Python／server default、参照動作、制約、保持・削除方針に未決定項目がない。defaultの不一致と、理由のない識別・秘密情報のNULL許可が残っていない。CHECKが構造的不変条件に限定され、PostgreSQLとSQLiteで同じ許可・拒否結果になる。FKのCASCADE／SET NULLが所有・履歴方針と一致し、削除時探索用Indexが不足していない。外部quoted `"user"`は表の対象外であることが明記されている。

### DB-04: 制約・インデックスの確定

- Repositoryの`WHERE`、`JOIN`、`ORDER BY`、cleanup処理を再棚卸しする。
- PK・UNIQUEと重複する索引を除去し、第4節の複合・部分索引を定義する。
- 複合Indexの先頭列、部分Indexの述語、並び順が対象クエリと論理的に一致することを確認する。
- CASCADE／SET NULL対象のFK列を親行削除時に探索できるIndexがあることを確認する。
- 第4節の各候補について、機能baselineへの暫定採用または不採用を決め、対応クエリと判断理由を記録する。
- 性能実測前の暫定設計であることと、DB-PERF-01で追加・削除・列順変更があり得ることを記録する。

完了条件: 採用する各Indexに根拠クエリがあり、完全重複がなく、複合列順と部分Index述語が実クエリに一致する。不採用候補にも判断理由があり、性能最適化済みとは扱わないことが明記されている。中規模データ生成と性能測定は完了条件に含めない。

### DB-05: 暫定vNext baselineの最終化

- DB-02で作成した`down_revision = None`の暫定baselineを、DB-03とDB-04で確定した最終schemaへ更新する。
- 共有Base、命名規則、NULL／default、CHECK、FK削除動作、Indexの後続変更をbaselineへ反映する。
- DB-06でreference-app bootstrap seedへ移管する`kkbiz_business_clock(id=1)`初期行投入を暫定baselineから除去し、最終baselineをDDL-onlyにする。
- autogenerate結果を手動レビューし、依存順、FK、server default、CHECK、UNIQUE、部分Indexを確認する。
- `upgrade()`は空DBから全DDLを作成し、`downgrade()`は逆順で削除する。
- baselineへ初期データを含めない。

完了条件: 暫定baselineが最終schemaへ更新され、単一headのまま空DBでupgrade、downgrade base、再upgradeが成功する。`alembic check`で最終ORM metadataとの差分がない。

### DB-06: reference-app bootstrap seedと開発・E2E seedの分離

- permission、role、関連、business clockの冪等なreference-app bootstrap seedを用意する。
- reference-app bootstrap seedを`libkoiki`の必須初期データとして公開しない。
- 固定パスワードユーザーを開発・E2E専用seedへ分離する。
- 本番相当環境で開発seedを拒否する環境ガードを追加する。
- `ops/security/roles_permissions.py`の定義と投入処理の責任を整理する。
- downstream固有seedがこの処理へ混入しない所有境界を確認する。

完了条件: reference-app bootstrap seedを2回実行でき、本番経路に固定パスワードがなく、seed完了後のbusiness clockが`id = 1`の一行だけとなる。`libkoiki`単独利用者へ参照アプリ固有データを要求しない。

### DB-07: コード・テスト・運用参照の一括更新

- DB-02後の制約、共通Base、seed、cleanup変更に伴うRepository、fixture、`ops/`、Docker、CIを更新する。
- 最終運用文書を更新し、歴史資料は必要な注記だけを加える。
- DB-02で維持した外部quoted `"user"`契約が後続変更でも保たれていることを再確認する。
- SAML terminal flow保持日数の設定を追加し、既定30日とする。
- Login attempt、token、SAML flowのcleanup処理と定期実行経路を新テーブル名・保持方針へ合わせる。
- SAML cleanupは`authn_requested`で`relay_expires_at`、`acs_verified`で`login_ticket_expires_at`を使用し、状態ごとの期限列を混同しない。

完了条件: 実行コードと現行運用文書に旧DBオブジェクト参照が残らず、一時・履歴データの設定可能なcleanup経路が存在する。

### DB-08: baseline契約テスト

- PostgreSQL空DBへのupgradeテストを追加する。
- inspectorでテーブル、PK、FK、UNIQUE、CHECK、Indexを検証する。
- 最小CHECKの許可値と拒否値をPostgreSQLとSQLiteの両方で検証する。
- 親行削除時のCASCADE／SET NULL結果をPostgreSQLで検証する。
- 小規模fixtureでIndex定義、部分Index述語、代表クエリの結果をCI検証し、中規模性能データ生成は通常CIへ含めない。
- `alembic check`でORMとの差分がないことを確認する。
- upgrade、downgrade base、再upgradeを検証する。
- reference-app bootstrap seedの冪等性と開発seedの環境ガードを検証する。
- SAML active flowの状態別失効と、terminal flowの保持期間後削除を境界時刻の前後で検証する。
- 可変エンティティの更新で`updated_at`が進み、Login attemptと関連表には不要な`updated_at`が存在しないことを検証する。

完了条件: PostgreSQLで空DB再現、schema driftなし、往復migration、seed責任分離が証明される。

### DB-09: 統合・セキュリティ回帰検証

- auth、session、refresh token、password reset、permissionを検証する。
- Todo CRUDと楽観ロックを検証する。
- SSOリンク、SAML ticket排他、最新session index取得を検証する。
- business clockの初期化、更新、排他制御、複数行拒否を検証する。
- business clock行を欠落させた状態から、サービスが`id = 1`を再作成することを検証する。
- PostgreSQL catalogで重複・無効Indexがないことを確認する。

完了条件: 主要DB integrationが成功し、認証・認可が同等で、business clockの二行目をDBが拒否する。

### DB-10: DB再作成runbookと完了判定

- ローカル、CI、Docker ComposeのDB削除、作成、upgrade、seed手順を書く。
- 破壊的操作前の対象DB確認と、固定パスワードseedの許可環境を明記する。
- 最終schema、Alembic head、検証結果を記録する。

完了条件: clean checkoutからvNext DBを再現でき、本番相当DBにテストユーザーが存在しない。

### DB-PERF-01: 中規模データによるIndex性能再評価（後続・非ブロッキング）

依存: DB-09の統合回帰完了。DB-00～DB-10の機能baseline完了を妨げない。

- 第4.1節の中規模参照データを、固定seed値を使う再現可能な専用手順で生成する。
- データ投入後に`ANALYZE`を実行し、代表クエリを`EXPLAIN (ANALYZE, BUFFERS)`で測定する。
- 第4.2節に従い、通常plannerの実行計画、buffer、テーブル／Indexサイズを保存する。
- 認証履歴とトークンテーブルで、Index変更前後のINSERT／UPDATEコストを同条件で比較する。
- DB-04で暫定採用した各Indexの維持、削除、列順変更、追加を判断し、証跡と理由を記録する。
- 採用した性能変更は、baseline完成後の新しいAlembic revisionとして追加する。

完了条件: 中規模データ生成と測定を再現でき、各Indexの最終判断に実行計画と相対コストの証跡がある。planner設定でIndex利用を強制していない。

## 7. 実行順

```text
DB-00 -> DB-01 -> DB-02 -> [M1レビューゲート]
      -> DB-03 -> DB-04 -> DB-06 -> DB-05
      -> DB-07 -> DB-08 -> DB-09 -> DB-10

DB-09またはDB-10完了後 -> DB-PERF-01（後続、機能baselineの非ブロッキング）
```

DB-02のM1コミットでは、改名、全参照更新、暫定baseline、代表smokeを同時に揃え、参照名が不整合な中間コミットを作らない。M1後のDB-03～DB-07も、共通Base、制約、Index、seed、cleanupなどの挙動変更を可能な限り分離し、各コミットで対象テストをgreenにする。DB-06でbusiness clock初期行の投入責任をbootstrap seedへ移管した後に、DB-05で暫定baselineからDMLを除去して最終化する。DB-08のbaseline契約テストへ進む前に、DB-05の最終baselineとDB-07の後続参照更新を揃える。

DB-01でM1阻害差異が見つかった場合は作業を停止し、独立修正のスコープとコミットを承認するまでDB-02に着手しない。

DB-01の監査表は文書専用コミットで確定する。M1阻害差異がなければ、そのコミット後にDB-02の実装へ進む。

DB-02とM1コミットがgreenになった時点で作業を停止し、M1レビュー承認をDB-03の着手条件とする。

機能baselineの集中作業目安は3～5稼働日、統合修正を含む場合は5～7稼働日とする。DB-PERF-01は別途1～2稼働日を目安とし、機能baselineのリリース判断を待たせない。

## 8. 検証コマンド候補

```powershell
$env:DEBUG = "False"
$env:DATABASE_URL = "postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db"

uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
uv run --locked alembic -c components/koiki_ref_app/alembic.ini upgrade head
uv run --locked alembic -c components/koiki_ref_app/alembic.ini check
uv run --locked alembic -c components/koiki_ref_app/alembic.ini downgrade base
uv run --locked alembic -c components/koiki_ref_app/alembic.ini upgrade head
.\scripts\run-db-integration-tests.ps1
```

旧名検索は部分一致を含むため、新名称、API resource名、履歴文書を機械的に変更せず、DB参照かを個別判定する。

## 9. 非対象

- 旧DB内のデータ移行と橋渡しmigration
- 旧テーブル名の互換VIEW
- `SSO_LINK_BACKEND=user_table`が参照する下流業務DBのquoted `"user"`テーブルのDDL変更
- API URLやresource名の接頭辞変更
- Todo starter/sampleの所有レイヤー変更
- `kkbiz`以外の将来業務テーブルの先行設計
- 実測またはクエリ根拠のない追加Index
- DB-PERF-01で行う数百万行データ生成、詳細な実行計画比較、書き込み性能比較を、機能baselineの完了ゲートにすること

## 10. 完了定義

- pre-vNextタグから旧Alembic履歴を復元できる。
- vNextが単一baseline、単一headである。
- 空PostgreSQL DBから全DDLを再現できる。
- 全テーブル名が所有レイヤーと複数形規則に従う。
- ORM metadataとDB schemaに差分がない。
- reference-app bootstrap seed、開発・E2E seed、downstream固有seedの所有が分離され、本番経路に固定パスワードがない。
- downgrade base、再upgrade、DB integration、主要セキュリティ回帰が成功する。
- DB再作成runbookがclean checkoutから再現可能である。
- DB-PERF-01が未完了でも、性能最適化済みと表示しないことを条件に機能baselineを完了できる。
