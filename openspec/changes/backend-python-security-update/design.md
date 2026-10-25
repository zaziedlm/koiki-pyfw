# 対応方針・進め方

## 1. 範囲と配置

対象は eMudhra／emSign 証明書問題、CVE-2026-115557、CVE-2026-111497 のバックエンド側対応。共有依存の制約は root と `components/libkoiki/`、参照アプリの疎通検証は `components/koiki_ref_app/` が担当する。`apps/` と互換ラッパ `app/` に回避実装を追加しない。配置は `docs/agent/boundaries.md` に従う。

API 契約・DB スキーマ・SSO／SAML プロトコル仕様は変更しない方針とする。互換性変更が必要になった場合は、理由・影響する利用者・追加検証を本計画へ追記してから実装する。Python 3.11／3.12 のパッケージ利用可能範囲を今回の配備版更新だけで廃止しない。

## 2. 更新前の基準（実施済み）

ブランチ作成元: `27cbd7e7cf22b7b42de9af93aacc1b4fe54307bd`（v0.8.1）。Python 3.13.13、certifi 2026.4.22、pip 26.1.1、HTTPX 0.28.1。導入済みパッケージはロックの版と一致し、プラットフォーム向け未導入の colorama を確認した。Docker／Dev Container の uv 指定は0.11.7であり、調査用ホストの uv とは区別する。

| 検証 | 成功 | スキップ | 備考 |
| --- | ---: | ---: | --- |
| libkoiki・agent_guidance | 174 | 1 | アプリ側コンテキストを必要とする既存テスト1件をスキップ |
| 参照アプリ・CI相当 | 98 | 0 | db_integration は別実行（54件選択除外） |
| DB統合 | 53 | 0 | 認証・セッション・Todo・参照業務・サービス |
| Alembic／PostgreSQL契約 | 1 | 0 | 更新・巻き戻しを含む |
| apps構成 | 2 | 0 | エントリポイント確認 |
| 合計 | 328 | 1 | 更新前の基準 |

DB統合の初回は52成功・1失敗で、SSO署名キー未設定が原因だった。実行時だけテスト用 SSO／SAML キーを指定した再実行は53成功。アプリ修正で解消した結果ではない。初回HTTPテストの待機は実行サンドボックス制限によるもので、制限外の同一テストは成功した。

AsyncMock、非推奨API、テスト用HMACキー長などの警告は既存として記録し、新しい警告と比較する。実行ログ・JUnit XML は作業環境の `/workspace/work/backend-security-baseline/` にあり、リポジトリには含めていない。環境が破棄されても基準が分かるよう件数・条件・対象を本書に記録する。既存テストは外部IdPとの実通信、修正後TLS拒否、配備済みイメージの安全性まで保証しない。

## 3. 採用版の判断

2026-10-26の再照合で、Python **3.13.18**、certifi **2026.10.23**、pip **26.2.2**、uv **0.13.5**を採用版に確定した。Debian bookwormを継続し、CAは **20250419~deb12u2**、libbrotli1は **1.0.9-2+deb12u1**（各々同系列の後続修正版を許容）を基準とする。Python向けBrotliは追加しない。

公式根拠、配布ハッシュ、現行wheel互換性と適用先は [採用版の再照合結果](version-selection.md) を正本とする。

Python 3.13.18にはCVE-2026-115557の収録証拠があるが、確認時点では `python:3.13.18-slim-bookworm` は404、Actionsのmanifestも未掲載。T1.1は配布待ち、T1.2／T1.3は完了とする。取得ツール・CA準備のT2を先行し、T3の実環境更新はT1.4の配布物確認後に行う。3.13.17をssl対策済みとして代替しない。

## 4. 段階と変更単位

1. **T1 調査・採用版確定**: 公式リリース、CVE収録、PyPI制約、対象OS／CPU向けwheelとイメージを照合する。採用版・根拠URL・確認日・残件を記録する。
2. **T2 取得ツール・信頼基盤**: 安全な取得元と公式ハッシュ／署名を確認した修正版uv／pipを準備する。古いツールからの無検証更新やTLS検証無効化を行わない。OS CAと独自CAの取り込みを確認する。
3. **T3 Python実行環境**: 通常Dockerfileのbase／production、unifiedの既定値・各ステージ、CI、Dev Containerを揃える。まず旧ロックのまま候補Pythonで同期・回帰検証し、Python変更による差分を判定する。互換性上の依存変更が必要なら理由を記録してT4と一緒に評価する。
4. **T4 アプリ依存**: certifi／pipを対象指定してロックを更新する。一括の最新版更新はしない。rootのuv制約だけではlibkoiki下流に伝わらないため、単独配布の依存メタデータでも安全な下限を保証する。pipをアプリruntime依存へ不用意に追加しない。
5. **T5 コンテナ／Brotli**: 最新ベースを取得し古いビルドレイヤーを再利用せず再ビルドする。BuildKitのcache mountは別管理なので必要なapt／uvキャッシュの取得元・鮮度も確認する。実体のPython／pip／uv／certifi、OSパッケージ版・CA参照先、イメージdigestを記録する。
6. **T6 回帰・セキュリティ検証**: 下記の同一マトリクスを再実行し、監査・TLS・libkoiki単独利用を確認する。
7. **T7 レビュー・引き継ぎ**: 変更前後一覧・試験結果・監査除外／残件・再ビルド手順・ロールバック手順をまとめる。PRレビュー可能な状態にする。本番配備は別工程。

T2～T5は論理的なコミット単位とし、実際に分離不能なら組合せと理由を記録する。各段階で検証に失敗したら次の更新を重ねず、環境要因・既存不具合・更新起因へ切り分ける。

## 5. 回帰検証の再現手順

検証に `DEBUG=False`、`ENV_FILE=.env.ci` を明示する。DB試験は新規の専用DBと専用ロールを作り、`DATABASE_URL` を明示する。SSO_STATE_SIGNING_KEY／SAML_RELAY_STATE_SIGNING_KEY はテスト専用値をプロセスに注入し、本番鍵や実ユーザーデータを使わない。

以下は後続実装時の手順であり、本計画作成では実行・更新していない。

```sh
uv lock --check
uv sync --locked --group dev --group test --group security
# ORM bootstrapの混在を防ぐため、以下は別プロセスで実行する
uv run --locked pytest components/libkoiki/tests/ tests/unit/agent_guidance/
uv run --locked pytest -m 'not db_integration' components/koiki_ref_app/tests/ tests/integration/services/
uv run --locked pytest tests/unit/test_apps_composition.py
```

DB統合は `scripts/run-db-integration-tests.ps1` と同じ対象を実行する。

```sh
# 専用DBとテスト用設定の注入後、RUN_DB_INTEGRATION=1で実行
uv run --locked pytest -m db_integration   components/koiki_ref_app/tests/integration/app/api/test_auth_api.py   components/koiki_ref_app/tests/integration/app/api/test_auth_session_api.py   components/koiki_ref_app/tests/integration/app/api/test_todos_api.py   components/koiki_ref_app/tests/integration/app/test_vnext_reference_db_workflows.py   tests/integration/services/
```

DDL往復テストは、新規作成した `koiki_baseline_contract` DBだけを対象にする。DATABASE_URLとBASELINE_CONTRACT_DATABASE_URLを一致させ、`test_vnext_baseline_contract.py -m db_integration` を実行する。既存の同名DBがあれば破壊せず、隔離したPostgreSQL環境を用意する。

実行ごとにPythonと導入版一覧、ロック検証、JUnit XML、警告、終了コードを保存する。既存328成功・1スキップとの比較は件数だけでなくテストID・除外理由で行い、新規失敗と未説明のスキップ増加を認めない。

## 6. セキュリティの検証

- pip-auditの変更前後JSONを取得し、監査対象のruntime／dev、workspaceパッケージの監査対象外、OS・内蔵コピーの検出範囲外を明示する。監査の未検出だけで完了にしない。
- HTTPXのDocker内SSL_CERT_FILE、certifiの参照先、pip内蔵certifi、OS／独自CAを確認する。問題の信頼が残らないことを公式の対象情報と照合する。
- 安全なローカルfixtureで、正規TLSの成功と不正チェーンの拒否を確認する。侵害された公開鍵の拒否は、保守元の回帰テスト／安全な隔離fixtureまたはベンダーの収録証拠で確認する。第三者サイトへPoCを送らない。
- テスト用IdPまたは管理された検証先で、SSOトークン交換・JWKS・SAMLメタデータ取得の実通信をTLS検証有効のまま確認する。接続先や資格情報が未提供なら未検証として残し、モックテストで代替済みとは記載しない。
- 通常版dev／production、unified dev／optimized／production、Dev Containerの実体を確認する。productionでuvが含まれない構成では非搭載を記録する。
- libkoiki単独のクリーン環境で依存を解決し、HTTPX／certifiの版と制約を確認する。

## 7. 完了・中断・戻し方

完了判定はデルタSpecの9 Scenarioを正本とする。採用版の収録証拠、回帰成功、CA／取得ツールの反映、OS Brotliの修正版または非搭載・非到達の根拠、未検証事項の扱いを記録する。非到達はライブラリ修正済みとは区別する。

修正版未提供、依存解決失敗、新規機能退行、独自CA未確認、実通信未検証があれば、該当項目を未完了として残す。新規テストが必要な場合は検証する振る舞いを記し、実装をなぞるだけのテストは追加しない。

戻す場合はこのブランチの更新コミットを単位に、Python・取得ツール・依存定義・ロック・イメージを整合した組で戻す。旧脆弱版へ戻すことは安全性回復ではないため、隔離した検証環境で原因調査を行い、本番へ旧版を自動再配備しない。DBスキーマ変更は想定せず、DDL試験で本番DBに触れない。

## 8. 後続範囲と一次情報

フロントエンドNode.js／npm、Vite開発環境、外部Envoy／Istio等、実運用への配備は別タスクへ引き継ぐ。Dev ContainerはPython／uv／CAの変更を今回扱い、Node.jsのBrotli対策が済んだとは扱わない。

- Python注意喚起: https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576/1
- Python同梱pip更新: https://blog.python.org/2026/10/python-3151-3149-31317/
- CVE-2026-115557: https://mail.python.org/archives/list/security-announce@python.org/message/FNAJMZV6XQYLVPABNINDMF3VF66AYLW4/
- CPython 3.13バックポート: https://github.com/python/cpython/pull/160570
- uv: https://github.com/astral-sh/uv/security/advisories/GHSA-hq85-5cpj-mr62
- Brotli: https://github.com/google/brotli/releases/tag/v1.2.1
- Debian: https://security-tracker.debian.org/tracker/CVE-2026-111497

採用版確定時に確認日・リリース番号・収録証拠・対象イメージを追記する。今回の再照合結果・確認日・配布物の制約はversion-selection.mdを参照する。
