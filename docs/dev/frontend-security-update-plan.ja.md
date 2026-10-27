# React参考アプリのセキュリティ対応計画

> 実施後の現状は `docs/security/implementation/2026-10-27/README.ja.md` を参照。以下の着手前記録は確認時点の履歴。Keycloakはテスト用の外部IdP代替としてモジュール更新対象と分離し、PRは発行しない。

作成日: 2026-10-27（日本時間）。更新実装は未着手。

**対応は必要**。React本体だけでなく、Node.js、npmのruntime／dev依存、NginxとOSを別に扱う。現構成はBrowserRouterのSPAで、RSCサーバーは使っていない。

- [最終点検・当初CVEとの対応・T2/F0の実行単位](../security/security-update-entry-check-2026-10-27.ja.md)
- [対応方針・対象と候補版・実施手順](../../openspec/changes/frontend-security-update/design.md)
- [タスク・検証チェックリスト](../../openspec/changes/frontend-security-update/tasks.md)
- [提案と範囲](../../openspec/changes/frontend-security-update/proposal.md)
- [完了判定のデルタ仕様](../../openspec/changes/frontend-security-update/specs/frontend-security-maintenance/spec.md)
- [直近再確認と更新前監査の差分](../security/reviews/2026-10-27/README.md)

基準テスト取得→Node→runtime依存→dev依存・rootツール→Nginx／OS→API合同確認の順に差分を分ける。既存バックエンド更新計画と同じ案件台帳で管理するが、実装は比較可能な別コミット／PR単位にする。
