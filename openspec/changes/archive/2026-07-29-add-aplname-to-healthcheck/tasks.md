## 1. 実装

- [x] 1.1 `/health` の `service` を `settings.APP_NAME`、`version` を `request.app.version` から取得するよう変更する（[app_factory.py:236-247](components/koiki_ref_app/src/koiki_ref_app/app_factory.py#L236-L247)）
- [x] 1.2 `/` の `service` を `settings.APP_NAME`、`version` を `request.app.version` から取得するよう変更する（[app_factory.py:249-258](components/koiki_ref_app/src/koiki_ref_app/app_factory.py#L249-L258)）

## 2. テスト（`specs/application-health/spec.md` のScenarioと1対1）

- [x] 2.1 正常系 - ヘルスチェック応答：GET `/health` が `service=settings.APP_NAME`・`version=アプリケーションバージョン` を含むJSONをHTTP 200で返すことを検証するテストを追加する
- [x] 2.2 正常系 - サービス情報応答：GET `/` が `service=settings.APP_NAME`・`version=アプリケーションバージョン` を含むJSONをHTTP 200で返すことを検証するテストを追加する
- [x] 2.3 境界値 - APP_NAME変更時の追従：`monkeypatch.setattr(settings, "APP_NAME", ...)` で値を差し替えた状態でGET `/health` を呼び出し、`service` が差し替え後の値を返す（ハードコード文字列に戻っていない）ことを検証するテストを追加する
- [x] 2.4 Scenario総数（3件）とテストケース数（2.1〜2.3の3件）が一致することを確認する

## 3. 検証

- [x] 3.1 `components/koiki_ref_app/tests/unit/app/` 配下の新規テストを実行し、全て通過することを確認する
- [x] 3.2 `openspec validate add-aplname-to-healthcheck --strict` を実行し、Specとの整合を確認する
