# アプリケーション稼働状態の開示（application-health）

## Purpose

システムの稼働状態（アプリ識別情報）を外部に開示する業務ドメイン。運用監視・障害対応の起点となる稼働可用性の開示を扱う。監査ログの記録・保持期間・メトリクス収集など、`components/libkoiki` の `security_logger.py`・`security_metrics.py`・`AuditLogMiddleware` 等が持つ横断的な監査機能は対象に含めない。それらが将来capability化される際は、実装内容に見合った別のcapability名で起こす。

## 基本情報

| 項目 | 内容 |
| --- | --- |
| capability名 | application-health |
| 番台対応 | 未定（`.aidx/loop-design/` に本initiative用のSPEC-MAPが未作成のため。正式な番台割当は本番initiative化する時点で行う） |
| 主なレイヤ | `components/koiki_ref_app`（実装）。capability自体はレイヤに直交する |

## Requirements

### Requirement: ヘルスチェック応答の呼び出し契約

適用スコープ：全capability共通で参照される稼働監視用の横断的エンドポイント（`/health`・`/`）。入力なし。出力は下表。

| フィールド | 型 | 内容 |
| --- | --- | --- |
| service | string | `libkoiki` の `Settings.APP_NAME` の値 |
| version | string | FastAPIアプリケーションインスタンスに設定されたversion値 |
| status | string | 稼働状態（`/health`のみ） |
| timestamp | string | UTC ISO8601（`/health`のみ） |

- 【SHALL】システムは、`/health` および `/` への認証なしGETリクエストに対し、アプリケーション識別情報を含むJSONをHTTP 200で返さなければならない。
- 【SHALL】システムは、`service` フィールドの値として `Settings.APP_NAME` の値を返さなければならない。
- 【SHALL】システムは、`version` フィールドの値として、FastAPIアプリケーションインスタンスに設定されたバージョン値を返さなければならない。
- 【SHALL NOT】システムは、`service`・`version` の値を `/health` と `/` とで個別のハードコード文字列として保持してはならない。

#### Scenario: 正常系 - ヘルスチェック応答
- **WHEN** 認証なしでGET /health を呼び出す
- **THEN** service に Settings.APP_NAME の値、version にアプリケーションバージョンを含むJSONをHTTP 200で返す

#### Scenario: 正常系 - サービス情報応答
- **WHEN** 認証なしでGET / を呼び出す
- **THEN** service に Settings.APP_NAME の値、version にアプリケーションバージョンを含むJSONをHTTP 200で返す

#### Scenario: 境界値 - APP_NAME変更時の追従
- **WHEN** `Settings.APP_NAME` の値を実行時に別の値へ変更する
- **THEN** `/health` の `service` は変更後の値を返し、ハードコードされた固定文字列を返さない
