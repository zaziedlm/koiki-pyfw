# 認証・SAMLテーブルメンテナンス方針

## 方針

Webアプリケーションおよび`libkoiki`は、認証・SAMLデータの定期cleanupを起動しない。ECSではWebコンテナとタスク数を独立にスケールするため、保持・削除処理は業務システムのテーブルメンテナンスジョブに集約する。

ジョブはEventBridge Schedulerから起動するECS Scheduled Task、または業務システムで標準化した単一実行のバッチ基盤に実装する。Web APIのlifespan、リクエスト処理、各ECS Service taskから実行してはならない。

## 対象テーブルと必要な処理

| テーブル | 業務メンテナンスで行う処理 | 保持方針の決定者 |
| --- | --- | --- |
| `koiki_login_attempts` | 保持期限を超えた試行履歴の削除 | セキュリティ監査・業務運用 |
| `koiki_refresh_tokens` | `expires_at`を過ぎたトークンの削除 | 認証運用 |
| `koiki_password_reset_tokens` | `expires_at`を過ぎたリセットトークンの削除 | 認証運用 |
| `kkref_saml_auth_flows` | 期限切れの`authn_requested`／`acs_verified`を`expired`へ遷移し、保持期限を過ぎた`expired`／`ticket_consumed`を削除 | SAML・セキュリティ運用 |

従来の参照実装で用いていた30日という保持値は移行時の検討材料であり、フレームワークの既定契約ではない。法令、監査要件、インシデント調査要件、容量計画に従って業務システム側で決定し、ジョブ設定と運用runbookに記録する。

## 実装・運用要件

- ジョブは同時に1実行だけとし、重複起動時の排他または冪等性を保証する。
- 大量削除はバッチ化し、実行時間、削除件数、失敗件数を監視・記録する。
- SAMLフローの状態遷移と削除は、認証中のレコードを誤って削除しない期限条件を用いる。
- 実行前にバックアップ、復旧方針、保持期間変更時の承認手順を業務運用へ組み込む。
- テーブル名・索引・制約は[`db-vnext-index-design.ja.md`](db-vnext-index-design.ja.md)を正とする。
