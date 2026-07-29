# 共通機能：ヘルスチェック応答へのアプリ識別情報付与（add-aplname-to-healthcheck）

## メタ情報

| 項目 | 内容 |
| --- | --- |
| change-name | add-aplname-to-healthcheck |
| 所属機能Spec | application-health（新設） |
| 実装Spec種別 | 共通機能 |
| Spec番号 | 未定（`.aidx/loop-design/` に本initiative用のSPEC-MAPが未作成のため。本ChangeはOPSXワークフロー検証目的のPOCであり、正式な番台割当は本番initiative化する時点で行う） |
| 対象レイヤ | components/koiki_ref_app（実装）／application-health機能Specは業務ドメイン単位でありレイヤに直交する |
| Harvest候補フラグ | 候補あり（design.md参照：`settings.APP_NAME`・アプリバージョン参照パターンは他アプリでも再利用しうるため、将来 components/libkoiki への一般化を検討する） |

## Why

`/health` と `/`（[app_factory.py:236-258](components/koiki_ref_app/src/koiki_ref_app/app_factory.py#L236-L258)）は、`components/libkoiki` に既にある `Settings.APP_NAME`（値: `"KOIKI Framework"`）を使わず、アプリ名を個別にハードコードしている。`/health` は `"koiki-framework"`、`/` は `"KOIKI Framework API"` と表記が揺れており、同一アプリケーションを指しているにもかかわらず値が一致しない。

バージョンも同様に、`pyproject.toml`・`FastAPI(version=...)`・`/health` のレスポンス・`/` のレスポンスの4箇所に別々の文字列としてハードコードされており、単一の情報源がない。将来いずれか1箇所だけ更新されて他が古いままになっても、それを検知する仕組みが現状存在しない。

## What Changes

- `/health` の `service` フィールドの値を、ハードコード文字列から `settings.APP_NAME` の参照に変更する
- `/` の `service` フィールドの値も同じ `settings.APP_NAME` の参照に統一し、表記揺れを解消する
- `/health` と `/` の `version` フィールドを、単一の情報源（FastAPIアプリケーションインスタンスに設定済みのバージョン値）からの参照に変更する
- レスポンスJSONのフィールド構成（フィールド名・型・必須性・ステータスコード・認証要否）は変更しない。値の取得元のみを変更する
- `components/koiki_ref_app/tests/unit/app/` に、`/health` と `/` の `service`・`version` が設定値と一致することを検証するテストを新設する（現状この2エンドポイントに対するテストは存在しない）。DBを検証対象としないため、既存の `test_app_rate_limiter.py` と同じく `connect_db`/`disconnect_db` をmonkeypatchしたunitテストとして配置する

## Capabilities

### New Capabilities

- `application-health`: システムの稼働状態（アプリ識別情報）を外部に開示する業務ドメイン。運用監視・障害対応の起点となる稼働可用性の開示を扱う。監査ログの記録・保持期間・メトリクス収集など、`components/libkoiki` の `security_logger.py`・`security_metrics.py`・`AuditLogMiddleware` 等が持つ横断的な監査機能は対象に含めない。それらが将来capability化される際は、実装内容に見合った別のcapability名で起こす

### Modified Capabilities

なし。

## Impact

- **コード**: `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` の `/health`・`/` ハンドラのみ。レイヤはこのChangeの範囲では `components/koiki_ref_app/` に留め、`components/libkoiki/` への移設は対象外とする
- **API契約**: フィールドの追加・削除なし、ステータスコード変更なし、認証・CSRF要否の変更なし。既存クライアントとの互換性を維持する
- **frontend**: 影響なし。`frontend/` はレスポンスボディを参照せず、Docker/nginxのヘルスチェックもHTTPステータス200のみを見ている
- **テスト**: 新規unitテストを1ファイル（3ケース）追加する。既存テストへの影響なし
- **Spec**: `application-health` 機能Spec（新規）を1件作成する。archive時に `openspec/specs/application-health/spec.md` として初めて成立する。既存の `insurance-inquiry` への影響なし
