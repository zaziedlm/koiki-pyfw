---
status: accepted
---

# vNext DBを旧スキーマ互換なしで再ベースライン化する

vNextでは新規作成したPostgreSQL DBを必須とし、既存Alembic履歴を`down_revision = None`の単一baselineへ置き換える。pre-vNext revisionはGitタグから復元可能にするが、旧スキーマとのupgrade／downgrade経路は提供しない。DBを安全に再作成できる開発段階で旧DB互換性を手放し、一貫したスキーマ、所有境界を示すテーブル名、クエリ駆動のインデックスを得るためである。

`libkoiki`、参照アプリ、業務レイヤー所有のテーブルには、それぞれ`koiki_`、`kkref_`、`kkbiz_`を付ける。通常テーブルは複数形とし、singletonの`kkbiz_business_clock`だけは単数形を維持する。DBの`CHECK (id = 1)`は最大一行を保証し、reference-app bootstrap seedとサービス初期化が`id = 1`の存在を保証する。スキーマ作成はDDLだけを扱い、reference-app bootstrap seedと開発・E2Eユーザー投入を分離する。このbootstrap seedは参照アプリの初期運用データであり、再利用可能な`libkoiki`フレームワーク自体の必須データではない。固定パスワードを持つユーザーを本番初期化経路から作成してはならない。

`SSO_LINK_BACKEND=user_table`はvNextでも下流業務DB向け互換アダプターとして維持する。このアダプターが参照するquoted `"user"`テーブルは外部所有であり、KOIKI-FWのAlembic baseline、所有接頭辞への改名、および管理対象12テーブルのschema contractには含めない。標準の`SSO_LINK_BACKEND=user_sso`が使用する`kkref_user_sso_links`は、引き続き参照アプリ所有のbaseline対象とする。

## 帰結

- 旧テーブル名の互換VIEWとaliasは提供しない。
- PK、FK、UNIQUE、CHECK、Index名は共有SQLAlchemy `MetaData`の命名規則から生成する。
- PK／UNIQUE索引と重複する明示Indexを除去し、複合・PostgreSQL部分IndexをRepositoryのクエリパターンへ合わせる。
- baseline downgradeは`vNext baseline -> 空DB`だけを保証し、運用上の復旧にはDB再作成またはバックアップ復元を用いる。
- 下流業務DBのquoted `"user"`テーブルは外部契約として扱い、KOIKI-FW側から作成、改名、削除しない。
- `kkbiz_business_clock`の削除禁止トリガーは導入せず、行が欠落した場合はサービスが固定`id = 1`で再作成する。
- CHECKは壊れた状態では処理が成立しない構造的不変条件に限定し、SQL標準的な式でPostgreSQLとSQLiteの双方から検証する。変更されやすい業務ルールはサービス検証に残す。
- FKの削除動作は、所有データと関連表を`ON DELETE CASCADE`、保持すべき履歴を`ON DELETE SET NULL`に統一する。履歴からユーザー識別子が失われても、履歴自体は保持する。
- 一時・履歴データの保持期間はDDLへ固定せず設定とcleanup処理で管理する。SAML terminal flowはSLOに必要な期間を確保したうえで、既定30日後に物理削除する。
- 可変エンティティは共有Baseの`id`、`created_at`、`updated_at`へ統一し、追記専用履歴と純粋な関連表だけを理由付きの例外とする。
