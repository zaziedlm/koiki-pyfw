# セキュリティ更新の実施結果（2026-10-27）

対象ブランチは **security/backend-python-emsign-brotli**。開始は **2026-10-27 10:11:08 JST（01:11:08 UTC）**。終了・チェックポイント時刻は [execution.json](execution.json) を正本とする。起点コミットは `db57c30`。作業中のブランチ切替・mainの変更・本番配備は実施していない。

## 結果と適用範囲

会話当初のCVE-2026-115557（Python ssl）、eMudhra/emSign信頼ストア、CVE-2026-111497（Brotli）を起点に、Python本体、アプリ依存、React SPA、取得・ビルド・配信環境を更新した。アプリの認証・認可・Cookie/CSRFコードは変更していない。Keycloakは依頼者の説明に従い**テスト用の外部IdP代替**として分離し、ComposeのKeycloak定義は維持した。取得したKeycloak監査は参考資料であり、フレームワークの依存監査とは合算しない。PostgreSQLの既存コンテナ・ボリュームも変更していない。

**ローカルでPRレビューに必要な変更と検証を用意した段階**であり、全OS脆弱性の解消、本番でのIdP接続、GitHub Actionsの実行を完了した意味ではない。未検証の適用先と修正版未提供を残して、OpenSpec全体を完了扱いにしない。

## 採用した版

| 対象 | 更新前 | 更新後・判定 |
| --- | --- | --- |
| Python配備版 | 3.13.13 | **3.13.18**、通常/unified/CI/Dev Container |
| uv | Docker 0.11.7、ホスト0.12.19 | **0.13.5**、公式wheel SHA256照合、Dockerはmanifest digest固定 |
| certifi | 2026.4.22 | **2026.10.23**、libkoiki単独利用にも下限を宣言 |
| pip | 26.1.1 | **26.2.2**（開発・監査環境）。本番完成イメージから不要なpipとensurepipを除去 |
| PyJWT | 2.12.1 | **2.15.1**、認証・期限切れ拒否・options不変を確認 |
| cryptography | 47.0.0 | **50.0.2**、PyJWT crypto依存の安全な下限を宣言 |
| Starlette | 1.1.0 | **1.3.1**、FastAPI0.136.3の公開依存条件と回帰試験で互換性を確認 |
| AnyIO | 4.13.0 | **4.15.1**（下限4.14.2） |
| python-multipart | 0.0.29 | **0.0.32**（下限0.0.31） |
| Mako | 1.3.12 | **1.4.3**（下限1.4.2）。コンテナ監査で追加検出したCVE-2026-102991へ対応 |
| filelock / msgpack / urllib3 | 3.29.0 / 1.1.2 / 2.7.0 | **4.2.4 / 1.2.4 / 2.8.0**、監査ツール依存を制約・lockへ反映 |
| Debian bookworm CA | 旧イメージ由来 | **20250419~deb12u2**を実体確認 |
| Debian bookworm libbrotli1 | 旧イメージ由来 | **1.0.9-2+deb12u1**、OSバックポートを実体確認 |
| Node | Docker浮動22、旧ホスト24.19.0 | **22.23.4**、Docker/CI/Dev Container |
| npm | Node同梱10.9.9で解決エラー | **11.21.1**をビルド/CI/Dev Containerへ固定 |
| React / react-dom | 19.2.7 | **19.2.7維持**。ブラウザSPA、RSCサーバーなし |
| React Router / Zod | 7.18.1 / 4.0.10 | **7.18.4 / 4.6.7** |
| Vite / Vitest | 7.3.6 / 4.1.10 | **7.3.7 / 4.1.12**（7.3系/4.1系） |
| Nginx | 1.30.3-alpine | **1.30.3-trixie**、非root UID101、静的配信を実測。OS Brotli=1.1.0-2+deb13u1（changelogにCVE-2026-111497修正を確認） |

ホスト既存のアプリ `.venv` とグローバルuvは保持し、更新後の実測はPython3.13.18の隔離コンテナ環境で行った。通常利用も更新済みDocker/Dev Containerまたは同版のPython/uv環境で開始する。

Pythonパッケージの利用可能範囲 `>=3.11.7` は維持した。3.11/3.12・arm64は今回の実行環境では実測していない。採用版・配布物のメタデータは各bootstrap.json、Nodeの収録根拠はnode-brotli-official.json、Pythonの前段根拠はOpenSpecのversion-selection.mdを参照。

Nodeの `process.versions.brotli` は **1.1.0**。これは未修正判定の根拠にはしない。公式22.23.4リリースはCVE-2026-111497に対する `0ed4268a4401abcb44720963` のcherry-pickとエラー公開を明記している。Node内蔵undici6.29.1と、npmが内蔵するundici6.29.0、アプリdev依存のundiciは別物として記録した。

## 既存機能の比較

| 検証 | 更新前/旧lock | 更新後 | 証拠 |
| --- | --- | --- | --- |
| libkoiki・agent guidance | 174成功・1スキップ | 同じ | backend-runtime-only / backend-after-final のJUnitとログ |
| reference app・非DB統合 | 98成功 | 同じ | 同上、DB対象54件は別実行 |
| auth/session/todos・DB統合 | 53成功 | 同じ | 専用DB、テスト用SSO/SAML鍵 |
| DDL往復契約 | 1成功 | 同じ | 専用koiki_baseline_contract DBのみを初期化 |
| downstream apps composition | 2成功 | 同じ | 同上 |
| バックエンド合計 | **328成功・1スキップ** | **328成功・1スキップ** | test-summary.json |
| frontend型・lint・build | すべて成功 | すべて成功 | frontend-before / frontend-node22-oldlock / frontend-*-after.log.gz |
| frontend Vitest | 7ファイル・21成功 | 7ファイル・21成功 | frontend-test-after.log.gz |
| libkoiki単独wheel | — | ビルド/独立導入/39パッケージの整合成功 | libkoiki-standalone.log.gz |
| TLS/JWT診断 | — | 正常TLS、拒否系、G3除去、JWT期限拒否/options不変成功 | tls-results.json、ops/security/verify_runtime_tls.py |
| backend本番ターゲット通常/unified | — | 専用新規DBへのmigration、実HTTP /・/openapi.json とも200 | backend-production-smoke.json |
| Nginx通常/unified | — | health、/login、/tasks、深いURL、JS資源配信成功 | frontend-nginx-smoke.json |

旧ホストNode24.19.0と採用22.23.4の両方で旧依存の既存テストを先に比較した。初回の全間接node_modules一覧は未採取であり、直接依存の一致確認とlockハッシュを保存した。後から旧lockを別領域にnpm ciし、全導入一覧と再現結果を補ったが、元の間接導入状態を遡って証明したとは扱わない。

本番ターゲットのバックエンド起動試験はテスト専用設定（DEBUG=False、テスト用秘密鍵、専用DB）で実施した。実配備設定・実IdP・Redisを揃えた本番環境の受入試験ではない。起動試験専用の新規DB2個は結果保存後に削除した。

既存のスキップはアプリ文脈に依存するlibkoikiの1件で増加なし。警告は既存のAsyncMock未await等をログに保存した。frontendのビルドには従来と同様の大きいchunk警告がある。libkoikiとアプリのORM文脈は別プロセスで検証した。

## 監査と残件

| 検査範囲 | 更新前 | 更新後 |
| --- | --- | --- |
| Python lock全体82パッケージ / PyPI pip-audit | 10パッケージ、51生指摘、別名統合37群 | **0件** |
| Bandit（app/apps/componentsの既存範囲） | 0件 | **0件** |
| frontend npm audit 全依存 / omit=dev | 全依存18パッケージ | **両方0件** |
| root OpenSpec用npm依存 | zod High | **全依存/omit=devとも0件** |
| 完成本番backend通常/unifiedのPythonパッケージ | 最初の完成イメージでMakoとpip内蔵コピーを追加検出 | **ともに0件**（開発依存とインストーラを本番から分離） |

`python-audit-all-lock-after.json` はOSマーカーを除いて全lock82パッケージを監査した結果。`python-audit-after.json` はLinux実行条件の81パッケージの結果であり、両方とも0件。

`frontend-triage.json` は当初18パッケージの旧版/新版/親依存/勧告を保持する。Pythonの旧指摘は更新前python-findings.jsonと対応付ける。PyJWTの「修正版未提示」だったoptions変更問題は、採用版での不変性を実測し、更新後監査でも指摘がないことを確認した。

コンテナの生結果は `trivy-*.json.gz`、集計はcontainer-audit-summary.json。**0件は上表の限定した範囲**で、完成イメージ全体のゼロを意味しない。OSの多数の指摘には現行suiteでFixedVersionがない。前後でDB時点・OSが異なるため、ベースイメージの件数を単純な改善率として比較しない。

| 残件ID | 残る内容・扱い | 次の処置 |
| --- | --- | --- |
| OS-BE | Debian12完成backend各351行、Critical2/High70。Criticalはlibsqlite3-0/CVE-2025-7458（affected）とzlib1g/CVE-2023-45853（will_not_fix）。現行DBで提供修正版0行 | Debianの修正提供を監視。到達条件と保守元の判定をレビューし、配備側のリスク判断を別記録。無条件の安全宣言や監査除外はしない |
| OS-FE | Debian13完成Nginx各336行、Critical1/High58。Criticalはlibxml2/CVE-2026-6653（affected）。提供修正版0行 | 静的SPAの構成を保持し、Nginx/XML変換の利用条件とディストリ更新を追跡。Criticalを消すためにOS共有ライブラリを手作業で削除しない |
| OS-DEV | Dev ContainerのOS452行、Critical3/High75。openssh-client/CVE-2026-60002はfix_deferred | 開発環境の到達条件も別評価し、保守元の修正を追跡 |
| VENDOR-PIP | Dev Containerのシステムpip26.2.2内蔵msgpack/setuptools/urllib3に7行。外側のmsgpack等を更新しても内蔵コピーは置き換わらない | pip26.2.2が確認時の最新。親pipの更新待ちを追跡。本番イメージにはpip/ensurepip・開発依存を含めない |
| VENDOR-NPM | npm11.21.1の内蔵ip-address10.7.2に1件、undici6.29.0に2件。Node内蔵undici6.29.1とは別。確認したnpm12.2.1も同じ内蔵版 | 未検証の内蔵ファイル差し替えは行わず、親npmの修正を追跡。npm11はビルド/開発のみで、最終Nginxには存在しない |
| VERIFY-IDP | 管理された実IdPのTLS/JWKS/SSO/SAMLと実ブラウザによる合同操作は未実施 | 配備前に接続先・正規CA・資格情報のある管理環境で確認。テスト用Keycloakの更新とは別項目 |
| VERIFY-CPU-CI | 実測Linux/amd64。arm64、実配備CPU、GitHub Actions、Dev ContainerのVS Codeライフサイクル全体は未実測 | CI/配備時に確認。ローカルの定義整合とコンテナ内版は確認済み |
| BASELINE-INVENTORY | 更新前の全間接node_modules一覧は後から完全復元できない | 元lockの別領域再現と全導入一覧を補助資料として保存 |

上記はリスク受容の承認ではない。OpenSpecの未完了チェックは残し、配布元修正や環境確認を追跡する。参考Keycloakは旧26.3.5で364行、候補26.8.1で92行/Java指摘0を観測したが、ユーザーの範囲説明により採用変更・realm移行・既存サービスの再起動は実施していない。

## 実装上の判断と失敗の扱い

- 独自CAの固定COPYが欠損でビルドを止めていたため、正規提供された組織CAは存在時だけ導入する。セッションのプロキシCAはBuildKit secretでuv/npmのRUNにだけ渡す。TLS無効化は行っていない。
- Alpine配布先が環境の許可対象外でOS更新に失敗し、同一Nginx版のbookwormタグも存在しなかった。同じ1.30.3の公式trixieタグへ変更し、署名済みapt更新・非root起動・配信契約を確認した。OS変更なので全OS件数の単純比較はしない。frontend-os-changelog.txt.gzはBrotliの修正記録を含む。CAのnative changelogは同じ抽出パターンでは取得できず、CA版はruntime-probes.jsonの実体と保守元根拠で確認した。
- Node同梱npm10.9.9のpeer解決内部エラー（edgesOut）では更新を止めた。公式ハッシュ照合済みnpm11.21.1で元lockを保持して解決し、強制更新・legacy-peer-deps・overridesは使用していない。最終lockは公式Node同梱npm10のnpm ciでも再現できた。
- 初回コンテナ監査でMakoとpip内蔵コピーを検出したため、Makoを追加更新し、本番は通常/unifiedとも実行依存だけにした。検出を隠す除外は設定していない。
- 並行ビルドのVFS展開とJava監査DBで32GBディスクが不足した。再生成可能なビルドキャッシュを解放し、今回のTrivy DBを/tmpへ移動した。既存コンテナ・DBボリューム・リポジトリは削除していない。失敗したビルドは再実行した。
- Nginx設定のCOPY元が0600だとUID101から読めず起動失敗した。設定を0644、配信資源をUID101所有として両Dockerfileで明示し、両方のHTTPスモークを再実行した。
- TLS補助fixtureは最初にAKI/CA KeyUsage不足で厳格検証に失敗したためfixtureを修正した。OS/証明書の判定ではemSign全ルートではなく、公式勧告対象G3を検査する。完成コードで正常系・拒否系とも再確認した。

## 再現・PRと配備への引き継ぎ

1. 指定ブランチで `uv lock --check`、`uv sync --locked --group dev --group test`。Python3.13.18/uv0.13.5を使い、DEBUG=False/ENV_FILE=.env.ciを設定する。
2. 既存バックエンドテストをdesign.mdの順序・別プロセスで実行する。DB統合は**専用DBのみ**、DDL往復は専用koiki_baseline_contractを使う。JUnit/manifestのコマンド参照。テスト用SSO/SAML state鍵を明示する。
3. Node22.23.4/npm11.21.1でrootとfrontendの `npm ci` を実行。frontendはcheck-types/lint/test/build、rootとfrontendは全依存/omit=dev監査を実行する。
4. `uv run --locked python ops/security/verify_runtime_tls.py`。管理ネットワークの外部TLSには正規の結合CAバンドルをSSL_CERT_FILEで渡す。
5. 通常/unifiedのbackendはproduction、frontendはrunnerをビルドする。`--secret id=proxy_ca,src=/path/to/approved-combined-bundle.pem` を必要な環境で渡す。Dev Containerも同じsecretでbuildする。本番backendは追加のbuild-argなしで開発依存を除く。
6. TrivyはOS/CPU・DB日時を記録し、完成イメージとNode deps/Dev Containerを別に監査する。built-images.jsonのIDは**ローカル検証物**で、公開レジストリの配備digestではない。
7. main向けPRで変更資源・本記録・OpenSpec未完了項目をレビューし、CI実行を確認する。merge/本番公開/IdP移行はこの作業では実施しない。

ロールバックはPRのコード・lock・Docker/CI定義を同じコミットの組へ戻す。旧脆弱版の本番自動再配備は行わず、まず隔離検証環境で原因を切り分ける。今回DBスキーマや既存realmを移行していないので、それらの巻き戻しは対象外。依頼者の明示指示により、実施時点ではPR発行・ドラフトPR作成を行わなかった。その後、リポジトリのローカル取り込みとブラウザ操作での確認（[local-container-verification.ja.md](local-container-verification.ja.md)）を終えた段階で、依頼者がPR発行を許可し、2026-10-27にmain向けドラフトPR #148を作成した。マージは未実施で、未解消の項目の扱いを判断してから行う。引き継ぎは本ブランチの資源のみとする。

## ローカルPCでのコンテナ動作確認と未対応の気づき

更新後の依存でコンテナをビルドし、ローカルPCのブラウザ操作（ログイン、タスク一覧・作成・更新）まで確認した実績と、その際に気づいた未対応事項（DEBUGモードのSQLログ、`user_agent`の中身、ログアウトの監査記録など）は [local-container-verification.ja.md](local-container-verification.ja.md) に記録した。未対応事項は解消済みを意味しない。
