# LOG-12 残課題管理（ハンドラ分離 / 固定コード化）

最終更新: 2026-04-10

## 1. 目的

本書は、以下2件を「要対応残タスク」として明示管理するための文書である。

- `TASK-02`: security/audit/normal のハンドラ分離と保存先分離
- `TASK-03`: SSO(OIDC) エラー detail の固定コード化と通常ログ最小化

現時点では、外部 IdP（特に SAML）接続の品質確認フェーズを優先し、
一時的に詳細エラー観測を許容する。
接続品質が安定したタイミングで、本書の残タスクを実施する。

## 2. 現在の運用方針（暫定）

- 外部 IdP 連携の初期安定化を優先する
- 調査目的で必要な範囲のエラー詳細観測を許容する
- ただし、以下は禁止を維持する
  - token 本体（access_token, refresh_token, id_token）
  - RelayState / login ticket 本文
  - password / secret / private key 類
- 詳細エラーを含むログ閲覧者は最小権限に限定する

## 3. 残タスク一覧

| ID | タスク | 優先度 | 状態 | 着手条件 |
| --- | --- | --- | --- | --- |
| `TASK-02` | ログハンドラ分離（security/audit/normal）と保存先分離 | High | Deferred | IdP接続品質が安定し、運用切替可能な時点 |
| `TASK-03` | SSOエラー detail の固定コード化と通常ログ最小化 | High | Deferred | IdP側エラー傾向が把握でき、調査フェーズを抜けた時点 |

## 4. TASK-02 詳細

### 4.1 目的

通常ログ / security log / audit log を論理・物理両面で分離し、
機微情報の露出面積を最小化する。

### 4.2 実施内容

- logger 名ごとに handler を分割する
  - `normal`（アプリ通常ログ）
  - `security`（セキュリティイベント）
  - `audit`（監査証跡）
- 出力先（ファイル/転送先）を分離する
- 保存期間・閲覧権限をログ種別ごとに定義する
- 既存運用との互換性（収集基盤、監視設定）を確認する

### 4.3 完了条件

- `security` と `audit` が通常ログと別保存先へ出力される
- 運用手順書に閲覧権限・保管方針が反映される
- 回帰テストまたは運用テストで分離を確認できる

## 5. TASK-03 詳細

### 5.1 目的

外部 IdP 応答の可変文字列（error_description 等）を
通常ログや API 応答へそのまま流さない設計にする。

### 5.2 実施内容

- `app/services/sso_service.py` の token 交換失敗時 detail を固定コード化
  - 例: `SSO_TOKEN_EXCHANGE_FAILED`
  - 例: `SSO_PROVIDER_RESPONSE_INVALID`
  - 例: `SSO_PROVIDER_ID_TOKEN_MISSING`
- 通常ログには `error_type` と `status_code` のみ記録する
- endpoint 側で `error=e.detail` を通常ログに出さない
- フロント側は固定コードをキーに表示文言を管理する

### 5.3 完了条件

- 通常ログに外部 IdP の可変詳細文字列が出ない
- API 応答 detail は固定コードのみになる
- 単体テストで「可変 detail 非露出」を検証できる

## 6. 着手トリガー（安定化判定）

以下を満たした時点で、`TASK-02` と `TASK-03` に着手する。

- SAML/OIDC の主要フロー（ログイン成功・失敗）が連続して安定動作
- 接続異常時の主要エラーパターンが把握済み
- 運用チームで「詳細エラー常時観測」フェーズ終了を合意

## 7. 関連文書

- `docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md`
- `docs/backend-audit/LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md`
- `docs/backend-audit/LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md`
- `docs/backend-audit/LOG-09_LOGGING_OPERATIONS_RUNBOOK_ja.md`

## 8. メモ

本書は「未対応を明確化して管理する」ための残課題台帳であり、
暫定運用を恒久化しないことを前提とする。
