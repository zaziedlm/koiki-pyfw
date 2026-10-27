# バックエンド Python 脆弱性対応計画

> 実施後の現状は `docs/security/implementation/2026-10-27/README.ja.md` を参照。以下の着手前記録は確認時点の履歴。Keycloakはテスト用の外部IdP代替としてモジュール更新対象と分離し、PRは発行しない。

作成日: 2026-10-26（日本時間）

ブランチ: `security/backend-python-emsign-brotli`。方針・手順・タスクの文書化と採用版の公式情報再照合まで実施。Python、依存定義、ロック、Docker、CIの更新は未着手。

- [最終点検・当初CVEとの対応・T2/F0の実行単位](../security/security-update-entry-check-2026-10-27.ja.md)
- [最新の配布確認・セキュリティ情報・準備状況](../security/reviews/2026-10-27/README.md)
- [フロントエンドの別対応計画](frontend-security-update-plan.ja.md)
- [更新前OSS監査結果と残件](../security/audits/2026-10-26-preupdate/README.md)
- [変更理由・対象](../../openspec/changes/backend-python-security-update/proposal.md)
- [対応方針・採用版判断・進め方・更新前検証結果・戻し方](../../openspec/changes/backend-python-security-update/design.md)
- [採用版・公式根拠・配布待ちの記録](../../openspec/changes/backend-python-security-update/version-selection.md)
- [実施タスクとScenario別検証チェックリスト](../../openspec/changes/backend-python-security-update/tasks.md)
- [今回のデルタ仕様](../../openspec/changes/backend-python-security-update/specs/backend-security-maintenance/spec.md)
- [保守の意図仕様](../../openspec/specs/backend-security-maintenance/spec.md)
- [案件台帳](../../.aidx/loop-design/backend-security-updates/SPEC-MAP.md)

更新前の基準は328成功・1スキップ。取得ツール・CA、Python、アプリ依存を段階的に更新し、各段階で既存検証を比較する。Pythonは3.13系を継続する方針で、CVE-2026-115557の収録を確認した3.13.18を目標版とする。公式Docker／ActionsのLinux配布物は2026-10-27に確認済み。BrotliはPythonパッケージ不在とコンテナOSの判定を分ける。Node.js対応は後続範囲とする。

本書は入口とし、方針の正本はdesign.md、進捗の正本はtasks.md、完了判定の正本はデルタ仕様のScenarioとする。
