# LOG-02 共通ログ Sanitizer 基盤追加 作業計画

最終更新: 2026-04-08

## 1. 目的

本書は、[`BACKEND_LOGGING_SECURITY_POLICY_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md)
を前提として、`LOG-02 共通ログ sanitizer 基盤追加` を実装可能な作業単位へ分割した計画書である。

本タスクの目的は、個別の logger 呼び出し修正に先立ち、`libkoiki/` と `app/` の双方で
共通に効く最終防御ラインを `structlog` 基盤へ組み込むことにある。

## 2. 対象範囲

### 2.1 対象

- `libkoiki/core/logging.py`
- `libkoiki/core/security_logger.py`
- `libkoiki/core/middleware.py`
- `app/main.py`
- `tests/unit/`
- 必要に応じて `tests/integration/` の logging 関連確認

### 2.2 本タスクで直接は完了させないもの

- 個別 endpoint の危険ログ文言の全面是正
- repository / service ごとの allowlist 化
- DB 例外ログの最終整備
- audit log 項目設計の完成

これらは `LOG-03` 以降で扱う。本タスクでは、それらの修正が安全に載る共通基盤を整える。

## 3. 現状整理

## 3.1 現行実装の観察

- [`logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py) の processor は
  `add_timestamp -> add_app_info -> add_request_info -> rename_event_key -> renderer` の最小構成で、
  機密情報を除去する処理が存在しない。
- `get_logger()` を通さず `structlog.get_logger(__name__)` を直接使うコードが広く存在する。
  そのため、共通防御は `structlog.configure()` の processor で効かせる必要がある。
- `security_logger` は `structlog.get_logger("security")` を利用しており、
  ここにも同じ sanitizer を適用する設計が必要である。
- `audit_logger` も `structlog.get_logger("audit")` を利用しているため、
  通常ログと同じ禁止項目は共通で防ぎつつ、`email` や `ip_address` の扱いは
  logger 種別または event 属性で分岐できる余地を残す必要がある。
- `setup_audit_logging()` は標準 logging の `FileHandler` を直接設定しており、
  今回は大規模な logger 再設計までは行わず、既存構成を壊さず sanitizer を優先適用する。

## 3.2 LOG-02 で満たすべき要件

- `password`, `token`, `secret`, `authorization`, `cookie`, `session id` を共通でマスクできること
- dict / list / tuple / set を含むネスト構造を再帰的に処理できること
- logger 呼び出し側が危険キーを渡しても、最終的な出力では平文が残らないこと
- 通常ログ、security log、audit log のうち、少なくとも禁止項目は全種別で共通に防御できること
- 今後 `LOG-03` から `LOG-07` で event 単位制御を追加できる拡張性を残すこと

## 4. 実装方針

## 4.1 基本方針

- 共通 sanitizer は `structlog` processor として実装する。
- 処理順は `request context` などの付与後、`renderer` の直前とする。
- `logger.bind()` や `logger.info(..., payload=...)` など、呼び出し形式に依存せず効く形にする。
- 値の完全削除ではなく、原則はマスク文字列へ置換する。
- logger 名が `security` または `audit` の場合に備えて、将来のポリシー分岐用フックを残す。

## 4.2 マスク方式

- 禁止項目: 固定文字列 `"[REDACTED]"`
- 通常ログの `email`: 部分マスク
- 通常ログの `ip_address`: 部分マスク
- 通常ログの `user_agent`: 可能であれば簡易化、最低でも全文保持を避ける
- `security` / `audit` での `email`, `ip_address`, `user_agent` の詳細制御は、
  本タスクではフックだけ用意し、詳細運用は `LOG-06`, `LOG-07` で仕上げる

## 4.3 キー判定の方針

初期対象はキー名ベースで判定する。以下を最低限の禁止キー候補とする。

- `password`
- `current_password`
- `new_password`
- `hashed_password`
- `token`
- `access_token`
- `refresh_token`
- `reset_token`
- `id_token`
- `relay_state`
- `state`
- `login_ticket`
- `authorization`
- `cookie`
- `session`
- `session_id`
- `secret`
- `client_secret`
- `jwt_secret`
- `private_key`
- `signing_key`

補足:

- `token_type` のような安全な派生キーを誤って潰しすぎないよう、完全一致優先で始める。
- `saml_response` や `assertion` のような大型機密ペイロードは、
  後続タスクも見据えて禁止候補に含める。

## 4.4 キー正規化ルール

キー判定は、呼び出し側の表記揺れを吸収するため、以下の正規化を前提に実装する。

- キー比較時は英字を lowercase 化する
- `-`、空白を `_` に正規化する
- `.` 区切りキーは最終要素も判定対象に含める
  - 例: `request.headers.authorization` は `authorization` として判定する
- 比較は「元キー」と「最終要素キー」の両方で行う
- 初期実装では camelCase の自動分解までは行わず、必要なものは明示キーとして追加する

例:

- `Authorization` -> `authorization`
- `request.headers.authorization` -> `authorization`
- `client-secret` -> `client_secret`
- `accessToken` -> 初期実装では自動分解しないため、必要なら後続で明示追加する

この方針により、過剰な推測判定を避けつつ、一般的な表記揺れには対応する。

## 4.5 広すぎる禁止キーの扱い

禁止キーは安全側に倒しすぎると、無関係な業務ログまで広く潰してしまう。
そのため、以下のキーは初期実装では「単独一致で全面禁止」しない。

- `state`
- `session`

理由:

- `state` は一般的な業務状態、処理状態、画面状態などを意味することが多い
- `session` もアプリケーション文脈では広義で使われやすい

代わりに、初期実装では以下のような狭いキーを優先して禁止対象にする。

- `relay_state`
- `oauth_state`
- `sso_state`
- `session_id`
- `session_token`
- `session_key`

運用ルール:

- 単独キー `state` は後続で実例を確認し、必要なら logger 種別または event 種別で限定追加する
- 単独キー `session` は値構造が識別子や secret を持つ場合でも、初期実装では自動 introspection しない
- 誤爆を避けることを優先し、危険箇所は `LOG-03` 以降の個別是正で補完する

## 4.6 再帰処理の境界条件

再帰的 sanitization は必要だが、無制限に辿ると性能劣化や予期しない副作用を招く。
そのため、初期実装では以下の境界条件を明示する。

### 4.6.1 再帰対象

- `dict`
- `list`
- `tuple`
- `set`

### 4.6.2 初期実装で深追いしない対象

- 任意の Python オブジェクトの属性探索
- ORM オブジェクトの `__dict__` 自動展開
- Pydantic モデルの自動 `model_dump()`
- `bytes` / `bytearray` の内容解析

これらは初期実装では文字列化せず、そのまま返すか、必要最小限の安全な置換に留める。

### 4.6.3 打ち切り条件

- 循環参照を検出した場合は、それ以上追跡せず固定文字列に置換する
  - 例: `"[REDACTED:CYCLE]"`
- 最大再帰深度を設ける
  - 初期案: 深度 `5`
- 最大深度を超えた場合は、それ以上のネストを固定文字列に置換する
  - 例: `"[REDACTED:DEPTH_LIMIT]"`

### 4.6.4 戻り値の契約

- 入力オブジェクトを破壊的変更しない
- `dict` は新しい `dict` を返す
- `list` は新しい `list` を返す
- `tuple` は `tuple` のまま返す
- `set` は `set` のまま返す
- `None`, `bool`, `int`, `float`, `datetime` などの非コンテナ値はそのまま返す

### 4.6.5 テストで必ず確認する境界ケース

- 大文字小文字違いのキー
- `.` 区切りキー
- `state` / `session` が誤爆しないこと
- ネストした `dict/list/tuple/set`
- 循環参照が発生しても例外にならないこと
- 深すぎるネストで打ち切られること
- 非文字列値が破壊されないこと

## 5. 作業単位

## 5.1 `LOG-02-01` Sanitizer 要件の固定化

- 目的:
  - 実装対象キー、マスク方式、適用 logger 範囲をコード実装前に固定する
- 主な変更対象:
  - [`docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md)
  - 本計画書
- 対応内容:
  - 初期禁止キー一覧を文書で固定
  - 通常ログ向けの `email`, `ip_address`, `user_agent` の暫定マスクルールを確定
  - `security` / `audit` 向けの将来拡張点を明記
- テスト:
  - 文書レビュー
- 完了条件:
  - 実装者がキー判定とマスク方式で迷わない状態になっている

## 5.2 `LOG-02-02` マスクユーティリティ追加

- 目的:
  - ログ processor から再利用できる純粋関数群を用意する
- 主な変更対象:
  - [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
- 対応内容:
  - `mask_email(value)`
  - `mask_ip_address(value)`
  - `mask_user_agent(value)` または `summarize_user_agent(value)`
  - `is_sensitive_key(key)`
  - `sanitize_log_value(key, value, logger_name=None, event_dict=None)`
  - `sanitize_mapping(mapping, logger_name=None)`
- 実装上の注意:
  - `None`, `int`, `bool`, `datetime` など非文字列値を壊さない
  - 元の dict を破壊せず、必要に応じてコピーして返す
  - 文字列中身の推測マスクは最小限に留め、まずはキー名判定を優先する
- テスト:
  - unit test で各関数の個別挙動を検証
- 完了条件:
  - 純粋関数レベルで禁止キーと部分マスクルールが成立している

## 5.3 `LOG-02-03` Structlog Processor 組み込み

- 目的:
  - 既存 logger 呼び出し全体に sanitizer を共通適用する
- 主な変更対象:
  - [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
- 対応内容:
  - `sanitize_event_dict(logger, method_name, event_dict)` processor を追加
  - processor の適用順を整理する
  - renderer 直前で event dict 全体を sanitize する
- 実装上の注意:
  - `rename_event_key` 後に `message` ができるが、`message` 自体は原則 sanitizer 対象外とする
  - ただし `message` に token を埋め込むコードは後続タスクで是正する前提
  - processor 内例外で logging 自体を壊さない
- テスト:
  - unit test で processor 通過後の event dict を検証
  - `structlog` logger 経由での smoke test を追加
- 完了条件:
  - `structlog.get_logger()` を直接使う箇所でも禁止キーがマスクされる

## 5.4 `LOG-02-04` Logger 種別対応の最小フック追加

- 目的:
  - `normal`, `security`, `audit` で将来分岐できる基盤を持たせる
- 主な変更対象:
  - [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  - 必要に応じて [`libkoiki/core/security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_logger.py)
- 対応内容:
  - `logger.name` または `event_dict` 上の種別情報からポリシー分岐可能な受け口を作る
  - 現時点では禁止項目マスクを全 logger 共通に適用
  - `security` / `audit` では `email`, `ip_address` を未加工で通せる将来拡張点をコメントまたは関数境界として残す
- テスト:
  - `audit`, `security`, 通常 logger で processor が安全に動作すること
- 完了条件:
  - 後続タスクで logger 種別制御を足しやすい構造になっている

## 5.5 `LOG-02-05` 回帰防止 Unit Test 追加

- 目的:
  - sanitizer 基盤の今後の退行を防ぐ
- 主な変更対象:
  - `tests/unit/core/`
- 対応内容:
  - 再帰的マスクのテスト
  - list / dict / nested object 風データのテスト
  - `email`, `ip_address` 部分マスクのテスト
  - `security` / `audit` logger 名でも禁止項目は落ちるテスト
- テスト:
  - `pytest` unit
- 完了条件:
  - 共通 sanitizer の代表パターンが自動テストで保護される

### 5.5.1 2026-04-09 時点の進捗

以下は [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py) で実装済み。

- キー正規化の単体テスト
- `state` / `session` の非過剰判定テスト
- `email` / `ip_address` / `user_agent` の通常ログ向けマスクテスト
- `audit` / `security` でも secret 系は禁止されるテスト
- `dict` / `list` / `tuple` / `set` の再帰 sanitization テスト
- 循環参照、深度制限、非文字列 scalar のテスト
- `sanitize_event_dict` の unit test
- `get_logger()` 経由の通常ログ / audit ログの capture test
- 内部 `_log_category` override のテスト

上記により、`LOG-02-05` の unit test 観点は実質的に充足している。

### 5.5.2 `LOG-02-05` に残さないもの

以下は unit test の範囲を超えるため、`LOG-02-06` で扱う。

- `security_logger` の公開メソッド経由でのスモーク確認
- `audit_logger` を実運用に近い payload で通した確認
- request context を bind した状態での logger 出力確認
- 既存 middleware / security logger との接続点の確認

## 5.6 `LOG-02-06` 既存呼び出しパターンへのスモーク確認

- 目的:
  - 実コードの呼び出しスタイルで sanitizer が破綻しないことを確認する
- 主な変更対象:
  - `tests/unit/` または軽量 integration
- 対応内容:
  - `structlog.get_logger(__name__).info(..., token=...)`
  - `security_logger` 経由
  - `audit_logger` 相当
  - request context 付きログ
- テスト:
  - 軽量テストでログ出力内容を捕捉して確認
- 完了条件:
  - 既存の logging 利用パターンで sanitizer が有効である

### 5.6.1 2026-04-09 時点の進捗

以下は [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py) で確認済み。

- `structlog.get_logger(__name__)` 相当の通常 logger 出力
- `audit` logger 出力
- [`security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_logger.py) の公開メソッド経由の出力
- request context を bind した状態での logger 出力

これにより、`LOG-02-06` の軽量スモーク確認は完了とする。

## 6. 推奨実施順

1. `LOG-02-01` Sanitizer 要件の固定化
2. `LOG-02-02` マスクユーティリティ追加
3. `LOG-02-03` Structlog Processor 組み込み
4. `LOG-02-04` Logger 種別対応の最小フック追加
5. `LOG-02-05` 回帰防止 Unit Test 追加
6. `LOG-02-06` 既存呼び出しパターンへのスモーク確認

## 7. タスクごとの確認進行方法

各作業単位は、以下の 1 セットで完了確認する。

1. 実装
2. 当該タスク範囲の unit test または smoke test 追加
3. テスト実行
4. ログ出力例の目視確認
5. 次タスクへ進行

この進め方により、後続の `LOG-03` 以降で問題が出ても、
どの段階で基盤が壊れたかを切り分けやすくする。

## 8. 既知の制約と後続課題への接続

- `message` 文字列そのものに token を埋め込んだログは、本タスクだけでは完全に除去できない。
  これは `LOG-03`, `LOG-05` で個別呼び出し修正が必要である。
- `security log` の限定イベント制御は、本タスクでは仕組みを入れすぎない。
  本格対応は `LOG-06` で行う。
- `audit log` の項目制御と保存先分離も、本タスクでは土台のみを意識し、
  詳細整備は `LOG-07` に委ねる。
- テスト実行時に観測された warning は `LOG-02` 本体とは分離して追跡する。
  - 参照: [`WARNING_FOLLOWUP_TASKS_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md)

## 9. この計画で次に着手する作業

この計画に基づく次の実装着手は `LOG-03 認証・パスワード系ログの是正` とする。

理由:

- `LOG-02-01` から `LOG-02-06` まで完了し、共通 sanitizer 基盤は成立した
- 次のリスクは、既存コードに残っている危険なログ呼び出しそのものにある
- password reset、login、refresh、SSO/SAML 周辺の個別ログ是正へ進む準備が整った
