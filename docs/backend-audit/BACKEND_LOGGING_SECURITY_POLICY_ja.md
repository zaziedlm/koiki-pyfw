# Backend Logging Security Policy

最終更新: 2026-04-09

## 1. 目的

本書は、`koiki-pyfw` における `LOG-01: ログ保護ポリシー確定` の成果物として、
バックエンドで扱うログの分類、出力ルール、機密情報保護ルール、運用権限を定義する。

本書の目的は以下のとおり。

- 運用に必要な観測性を確保する
- 機密情報、認証情報、個人情報の過剰記録を防ぐ
- 通常ログ、security log、audit log の役割を分離する
- 後続の実装・テストで判断がぶれないようにする

## 2. 適用範囲

本ポリシーは以下に適用する。

- `libkoiki/` の共通バックエンド実装
- `app/` の認証、SSO、SAML を含むアプリケーション実装
- API endpoint、service、repository、middleware、exception handler から出力される全ログ

対象外は以下。

- DB 自体の監査ログ
- インフラ層の OS / container / load balancer ログ
- 外部 SaaS の標準監査ログ

## 3. ログ種別

### 3.1 通常ログ

アプリケーションの動作状況、処理開始・終了、失敗概要、性能情報を記録するログ。

用途:

- 障害解析
- 性能劣化の把握
- 例外の一次切り分け

特徴:

- 原則として機密値を保持しない
- 個人情報は最小化する
- email / ip_address は生値禁止、部分マスクを原則とする

### 3.2 Security Log

セキュリティイベントの検知、攻撃追跡、認証異常の相関分析を目的とするログ。

用途:

- ブルートフォース攻撃の調査
- 不正トークン利用の調査
- アカウントロックアウト、認証失敗傾向の分析

特徴:

- 通常ログより情報粒度が高い
- ただし出力対象イベントは明示的に限定する
- email / ip_address / user_agent の生値保持を許可するが、許可イベントのみ
- 保存先は通常ログと分離する

### 3.3 Audit Log

「誰が」「いつ」「何を」「どの結果で」行ったかを記録する証跡ログ。

用途:

- 内部統制
- 監査対応
- 変更履歴・操作履歴の証跡

特徴:

- 業務・管理操作の証跡を残す
- principal 情報、対象リソース、結果を記録する
- email / ip_address の生値保持を許可する
- 厳格なアクセス権限、保管方針、閲覧手順を要求する

## 4. データ分類

### 4.1 ログ出力禁止データ

以下は、通常ログ、security log、audit log のいずれにも平文で出力してはならない。

- パスワード
- パスワードハッシュ
- アクセストークン
- リフレッシュトークン
- パスワードリセットトークン
- SSO / SAML の state token
- RelayState token
- login ticket
- Authorization header
- Cookie ヘッダ
- Session ID
- client secret
- JWT secret
- SAML private key
- CSRF secret
- API key、secret key、signing key 全般

### 4.2 原則マスク対象データ

以下は通常ログで生値出力してはならない。

- email
- ip_address
- user_agent
- request payload 内の個人情報
- DB 例外詳細に含まれる入力値

### 4.3 条件付きで生値保持を許可するデータ

以下は `security log` または `audit log` に限り、生値保持を許可する。

- email
- ip_address
- user_agent
- user_id
- username
- request_id
- subject_id / sso_subject_id

ただし、許可条件は本書の `6. Security Log の限定イベント` および `7. Audit Log の要件` に従う。

## 5. 通常ログの出力ルール

### 5.1 基本原則

- 通常ログは「処理内容の概要」と「調査に必要な最小情報」に限定する
- 入力値丸ごと出力を禁止する
- ORM `__dict__` や request body 全量出力を禁止する
- 機密情報は共通 sanitizer により最終防御する

### 5.2 マスクルール

#### email

通常ログでは部分マスクを使用する。

例:

- `taro@example.com` -> `t***@example.com`
- `ab@example.com` -> `a*@example.com`

#### ip_address

通常ログでは部分マスクを使用する。

例:

- IPv4: `192.168.1.25` -> `192.168.1.xxx`
- IPv6: 後半セグメントを伏せる

#### user_agent

通常ログでは原則として詳細な全文出力を避ける。

許可例:

- ブラウザ種別やクライアント種別の簡易分類
- 既知パターンの識別子

禁止例:

- 長い user agent 全文をそのまま出すこと

### 5.3 通常ログで記録すべき推奨項目

- timestamp
- log level
- message
- request_id
- endpoint / path
- method
- actor identifier（可能なら user_id、なければ匿名）
- result / status_code
- duration

## 6. Security Log の限定イベント

`security log` は以下のイベントに限定して出力する。
ここに列挙されていないイベントを `security log` に送ってはならない。

### 6.1 許可イベント一覧

1. `authentication_failed_invalid_credentials`
   - メールアドレスまたはパスワード誤りによる認証失敗

2. `authentication_failed_inactive_user`
   - 非アクティブユーザーによる認証失敗

3. `authentication_blocked_lockout`
   - ログイン試行制限またはロックアウトにより拒否されたイベント

4. `authentication_succeeded_after_risk_check`
   - 段階的遅延、試行回数確認などを経て認証成功したイベント

5. `refresh_token_rejected`
   - 不正形式、失効済み、期限切れ、ローテーション不整合などにより refresh token が拒否されたイベント

6. `password_reset_requested_existing_user`
   - 既存ユーザーに対するパスワードリセット要求

7. `password_reset_completed`
   - パスワードリセット完了

8. `password_reset_rejected_invalid_token`
   - パスワードリセット token 不正または期限切れ

9. `sso_login_failed`
   - OIDC / SSO 連携での認証失敗

10. `sso_login_succeeded`
    - OIDC / SSO 連携での認証成功

11. `saml_login_failed`
    - SAML 認証失敗

12. `saml_login_succeeded`
    - SAML 認証成功

13. `token_reuse_or_integrity_violation_detected`
    - login ticket、RelayState、refresh token rotation 等で再利用・整合性違反が検出されたイベント

14. `suspicious_activity_detected`
    - 明示的に suspicious と判定したイベント

15. `rate_limit_exceeded_security_sensitive_endpoint`
    - login、refresh、password reset、SSO、SAML など security sensitive endpoint のレート制限超過

### 6.2 Security Log に含めてよい項目

- timestamp
- event_type
- request_id
- user_id
- email
- ip_address
- user_agent
- endpoint
- auth_method
- failure_reason
- lockout_duration
- count / threshold
- sso_provider / saml_provider
- subject_id（必要時）

### 6.3 Security Log に含めてはならない項目

- token 本体
- token 断片
- password
- password hash
- secret 全般
- 認証ヘッダ全文
- Cookie 全文
- SAMLResponse 本文
- OIDC id_token 本文
- RelayState token 本文
- login ticket 本文

### 6.4 Security Log 運用ルール

- 保存先は通常ログと分離する
- 出力イベントは本節に記載のイベントに限定する
- 生値を保持する場合でも、機密値は禁止対象から除外しない
- 運用上の閲覧権限はセキュリティ担当、認証基盤保守担当、限定された SRE のみとする

## 7. Audit Log の要件

### 7.1 Audit Log に記録すべき対象

以下の操作を audit log 対象とする。

- 認証済みユーザーの重要API操作
- ユーザー情報の更新
- 権限関連の更新
- アカウント状態変更
- トークン全失効
- SSO / SAML ログイン完了
- SAML logout 開始 / 完了
- 管理権限を要する操作

### 7.2 Audit Log に記録すべき項目

- timestamp
- request_id
- actor.user_id
- actor.email
- actor.auth_method
- client.ip_address
- http.method
- http.path
- target.resource_type
- target.resource_id
- action
- outcome
- status_code
- duration_ms

### 7.3 Audit Log に含めてはならない項目

- password
- token 本体
- secret 全般
- request body 全文
- Authorization header
- Cookie
- SAML assertion 本文
- OIDC token 本文

### 7.4 Audit Log の厳格権限

`audit log` は通常ログより厳格に管理する。最低限、以下のルールを適用する。

#### 閲覧可能者

- 監査責任者
- セキュリティ責任者
- 認証基盤の主担当保守者
- 承認を受けた SRE / 運用担当

#### 閲覧不可とする対象

- 一般開発者
- 一般サポート担当
- read-only 運用アカウントのうち監査用途外のもの

#### 権限ルール

- 原則 `need-to-know`
- 恒久権限ではなく、可能な限りロールベースまたは期限付き付与
- 閲覧・検索・エクスポート操作自体も監査対象にする
- 本番 audit log への write 権限と read 権限を分離する
- 削除権限はさらに限定し、通常運用者には付与しない

#### 保管ルール

- 通常ログと保存先を分離する
- 改ざん耐性のある保管先を使用する
- 保持期間を定義する
- バックアップと復元手順を定義する

## 8. 例外ログのルール

- ユーザー向けエラー詳細と、内部ログ詳細は分離する
- 例外ログには stack trace を許可するが、機密値は sanitizer を通す
- DB 例外は SQL 文や入力値の全文を出さない
- validation error は、必要最小限のフィールド名と理由に留める

## 9. 実装ガードレール

以下を実装ルールとする。

- logger 呼び出し時に request body 全量を渡さない
- `obj.__dict__` をそのままログに出さない
- token や secret を含みうる辞書は allowlist で出力する
- 共通 sanitizer を通さない独自 logger を増やさない
- security log と audit log は通常ログと別 logger 名、別 handler、別保存先を前提にする

## 10. テスト方針

### 10.1 必須テスト

- password reset 要求時に token がログへ出ない
- password reset confirm 時に token 断片がログへ出ない
- user create / update 時に password / hashed_password がログへ出ない
- DB exception 時に SQL 詳細や機密入力が露出しない
- sanitizer がネストした dict/list を正しくマスクする
- security log に未許可イベントが流れない
- audit log に禁止項目が含まれない

### 10.2 確認方法

- unit test で sanitizer と formatter を検証する
- integration test で代表 endpoint 呼び出し時のログ出力を検証する
- review では「logger 引数に何を渡しているか」を確認対象にする

## 11. 後続タスクへの接続

本書を前提として、後続は以下の順で進める。

1. `LOG-02` 共通ログ sanitizer 基盤追加
   - 詳細計画: [`LOG-02_COMMON_LOG_SANITIZER_WORK_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-02_COMMON_LOG_SANITIZER_WORK_PLAN_ja.md)
2. `LOG-03` 認証・パスワード系ログの是正
3. `LOG-04` Repository/Service の入力データログ是正
4. `LOG-05` 例外・DB エラーログ是正
5. `LOG-06` security logger の情報粒度再設計
   - 詳細計画: [`LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md)
6. `LOG-07` 監査ログ方針との整合化
   - 詳細計画: [`LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md)
7. `LOG-08` 回帰防止テスト追加
   - 詳細計画: [`LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md)
8. `LOG-09` 運用・保守向け文書更新
   - Runbook: [`LOG-09_LOGGING_OPERATIONS_RUNBOOK_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-09_LOGGING_OPERATIONS_RUNBOOK_ja.md)
