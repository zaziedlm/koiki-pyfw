# バックエンド Python セキュリティ更新

## メタ情報

- change-name: `backend-python-security-update`
- 所属機能Spec: `backend-security-maintenance`
- 実装Spec種別: セキュリティ横断
- ブランチ: `security/backend-python-emsign-brotli`
- 作成日: 2026-10-26（日本時間）
- 状態: 計画了承済み。採用版再照合済み。Python実行物の公式配布を2026-10-27に確認済み。バージョン更新は未着手。

## Why

eMudhra／emSign 証明書問題に対して Python、取得ツール、アプリ依存、OS の信頼ストアをそれぞれ更新・確認する必要がある。Brotli の展開処理の脆弱性も、Python パッケージ不在だけでコンテナ全体を非該当とは判定できない。既存機能の確認結果を基準に、更新単位・検証・完了判定を明示して進める。

## What Changes

- 更新前の検証結果と再現条件を記録する。
- 修正版の公式情報を再照合し、Python 3.13 系、pip、uv、certifi、OS CA／Brotli の採用版を確定する。
- 取得ツール、Python、アプリ依存の順に差分を分け、各段階でロック・機能・TLS を検証する。
- Docker／CI／Dev Container と libkoiki の下流利用への反映を確認する。
- 今回の変更は計画・仕様・タスクの文書化のみとする。

## Capabilities

### New Capabilities

- `backend-security-maintenance`: バックエンド更新時の証拠、信頼維持、機能回帰と完了判定。

### Modified Capabilities

なし。

## Impact

後続実装は root／libkoiki の依存定義とロック、バックエンド Dockerfile、CI、Dev Container が対象。業務 API・DB スキーマ変更は想定しない。フロントエンド Node.js の更新と本番デプロイは別作業とする。
