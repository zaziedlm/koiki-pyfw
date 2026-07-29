## Context

`/health` と `/` は [app_factory.py:236-258](components/koiki_ref_app/src/koiki_ref_app/app_factory.py#L236-L258) の `create_app()` 内に直書きされている。同じ値（アプリ名・バージョン）が以下4箇所に独立してハードコードされており、一致は偶然の産物でしかない。

| 箇所 | 値 |
| --- | --- |
| `components/koiki_ref_app/pyproject.toml` | `version = "0.8.0"` |
| `FastAPI(version=..., title=settings.APP_NAME)` 呼び出し（app_factory.py:197-205） | `version="0.8.0"`（`title` は既に `settings.APP_NAME` 参照済み） |
| `/health` レスポンス | `"service": "koiki-framework"`, `"version": "0.8.0"` |
| `/` レスポンス | `"service": "KOIKI Framework API"`, `"version": "0.8.0"` |

なお `libkoiki`・`koiki_ref_app`・ルートの3つの `pyproject.toml` がそれぞれ独立に `version = "0.8.0"` を持っており、パッケージ横断でのバージョン一元化はこのChangeのスコープ外（Non-Goals参照）。

## Goals / Non-Goals

**Goals:**
- `/health` と `/` の `service` フィールドを `settings.APP_NAME`（`components/libkoiki`、既存）から取得し、表記を統一する
- `/health` と `/` の `version` フィールドを、`FastAPI(version=...)` に既に渡っている値から取得し、レスポンス側の重複ハードコードを解消する
- レスポンスJSONのフィールド構成・ステータスコード・認証要否を変更しない

**Non-Goals:**
- `pyproject.toml`（root / libkoiki / koiki_ref_app の3箇所）とアプリケーションバージョンの一元管理は対象外とする。パッケージメタデータからの動的取得は別Changeで検討する
- `/health`・`/` をルーター経由の構成へリファクタリングすることは対象外とする（既存のレイヤ構造・ルーティング方式は変更しない）
- `components/libkoiki` へのヘルスチェック機能の移設は対象外とする

## Decisions

### 配置: `components/koiki_ref_app` に留める

`/health`・`/` は現在 `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` に実装されている。ヘルスチェック自体は本来 `components/libkoiki`（再利用可能フレームワーク層）が持つべき汎用機能に近いが、今回の変更は「値の取得元をハードコードから設定値参照に変える」小さな修正であり、レイヤ移設は変更の目的にもImpactにも含まれていない。移設は責務の再配置という別種の変更になり、`docs/agent/boundaries.md` の「移動には明確な建築上の理由が要る」という原則にも反する。よって本Changeでは実装ファイルを変更せず、同一ファイル内で値の取得元のみを修正する。

### service名の取得元: `settings.APP_NAME`

`components/libkoiki/src/libkoiki/core/config.py` の `Settings.APP_NAME`（値: `"KOIKI Framework"`）を使う。`app_factory.py` は既に `from libkoiki.core.config import settings` をインポート済みであり、`FastAPI(title=settings.APP_NAME)` として使用実績がある。新規依存の追加なし。

代替案として `FastAPI` インスタンスの `title` 属性（`request.app.title`）を実行時に読む方法も検討したが、`settings.APP_NAME` を直接参照する方が意図が明確で、`request.app` 経由の間接参照より可読性が高いため採用しない。

### version の取得元: `FastAPI(version=...)` に渡した値（`request.app.version`）

`create_app()` 内で既に `FastAPI(version="0.8.0", ...)` としてバージョンを渡している。`/health`・`/` のハンドラは `request: Request` を引数に持つため、`request.app.version` で同一インスタンスの `version` 属性を参照できる。これにより、アプリケーション全体（OpenAPI `info.version` を含む）とレスポンスボディのバージョン表記が単一のリテラル（`FastAPI(version=...)` の1箇所）に収束する。

代替案として `importlib.metadata.version("koiki_ref_app")` によるパッケージメタデータからの動的取得も検討したが、次の理由で採用しない。
- `root` / `libkoiki` / `koiki_ref_app` の3つの `pyproject.toml` が独立してバージョンを持つ現状では、`koiki_ref_app` パッケージのメタデータだけを参照しても「単一の情報源」にはならない
- editable install ではない実行環境やテスト実行コンテキストでパッケージメタデータが取得できない場合の失敗モードを追加で考慮する必要があり、今回のスコープに対して過大

## Risks / Trade-offs

- [`FastAPI(version=...)` のリテラルはこのChange後も残り、更新のたびに人手で1箇所だけ書き換える運用は変わらない] → 影響は許容範囲（4箇所→1箇所への削減で十分な改善）。完全自動化は別Changeの対象とする
- [`request.app.version` は `Request` を経由するため、`app_factory.py` 外の場所（将来ルーター分割時など）から同じ値を参照する際に、`request` にアクセスできないコンテキストだと使えない] → 現時点では `/health`・`/` とも `request: Request` を既に受け取っているため問題なし。ルーター分割時に再検討する

## Open Questions

- 未確定: `pyproject.toml` 3箇所の統一（例えばroot `pyproject.toml` を単一の情報源とし、他2つが参照する、またはCI/リリースプロセスで同期を検証する）は、次にバージョン不一致が実際に発生した時点、または明示的なリリース管理Changeが起票された時点で検討する
