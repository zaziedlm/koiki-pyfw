# 2026-10-27 セキュリティ情報・配布状況の再確認

確認日: 2026-10-27（日本時間）。前回監査は2026-10-26。対象コミットはcomparison.jsonを参照。今回は公開情報・manifest・監査APIの読み取りと文書更新のみで、依存更新・イメージpull／実行・配備は行っていない。

## Python公式イメージ

`python:3.13.18-slim-bookworm` の公式RegistryでHTTP 200を確認した。

- index digest: `sha256:770c65dea7da9d5eeddb968968bd514ee9fdd9bb8988e03b4463eb11ad72d3ca`
- Linux amd64: `sha256:89c04d97d1f3f0a04ea357a27d000ba4efb18536d2d68a54611f76d5c1b5fe99`
- Linux arm64/v8: `sha256:fb12d5e51ef10ac4bc3c0b669166bbc16487cd918543ca7e6e0a899e22c550ae`
- indexにはLinux 386も存在する。unknown/unknownエントリは実行CPUとして扱わない。
- amd64の公開configに `PYTHON_VERSION=3.13.18` を確認した。実行時の版・ssl・CA検証は更新時に行う。

[Registry証拠](python-registry.json) に全manifestのdigestを保存した。タグは将来差し替わるため、実装時には再確認して採用digestを記録する。

[Actionsの3.13.18配布証拠](actions-python.json) も確認した。manifest blob SHAは `b0c84be989675d2d78a4ac17491154d44075a04e`。Ubuntu 22.04／24.04／26.04向けx64／arm64等が掲載されている。LinuxのCIに使う配布経路は確認済みであり、Windows／macOSの公式インストーラー提供を確認したという意味ではない。

## 直近情報の確認範囲と結論

確認した一次情報はPython公式リリース・Python Insider、React公式ブログとセキュリティ勧告、Node公式セキュリティ告知、Viteの公式Advisory、既存ロックに対するPyPI／npmの現在の監査API。Web検索では10月26日～27日の告知を中心に確認し、RSC等の既知の重大事象も現構成への該当性を照合した。

**この範囲では、前回の監査と比べて本プロジェクトのロックに新たに追加された指摘IDは確認されなかった。インターネット全体で新しい脆弱性が発生していないという保証ではない。** 監査DBの登録遅延・未掲載・利用条件の判定は残る。

- [Python公式10月26日告知](https://blog.python.org/2026/10/python-3152-31410-31318-31216-31118/): 3.13.18を含む緊急更新。既に計画対象のeMudhra／ssl対策と整合する。
- [Python 3.13.18](https://www.python.org/downloads/release/python-31318/): ssl対策のほかExpat、tarfile等のセキュリティ修正も含む。Python更新後のアプリ依存・ネイティブ部品は別検証する。
- [Node公式告知一覧](https://nodejs.org/en/blog/vulnerability): 確認時の最新セキュリティ告知は10月21日。22.23.4をBrotli／CA対策の候補とする。
- [React公式ブログ](https://react.dev/blog): 新たなブラウザSPA全体への緊急更新告知を確認できなかった。ただしRSC関連の勧告を別途確認した。
- [Vite公式Advisory](https://github.com/vitejs/vite/security/advisories): dev server等の指摘は既存監査の対象。新しいものがないことを恒久保証しない。
- [RSCプラグインの重大勧告](https://github.com/vitejs/vite-plugin-react/security/advisories/GHSA-59pf-q495-3c99): 10月15日公開の既知事象。`@vitejs/plugin-rsc`と`react-server-dom-webpack`を対象とする。現プロジェクトのロック・構成では該当パッケージとRSCサーバーを確認できず、React使用だけを理由に該当としない。

## 前回監査との比較

同一のuv.lockから抽出した82パッケージと、root／frontendの同一npmロックを再検査した。Pythonは空の新規キャッシュ、npmは別の作業キャッシュを使用し、自動fixや依存同期は行っていない。

| 検査 | 現状 | 前回との差分 |
| --- | --- | --- |
| Pythonロック | 10パッケージ・受信51指摘（前回整理ではパッケージ別37件） | (package, ID)の追加0・削除0 |
| root npm | High 1パッケージ | (package, advisory URL)の追加0・削除0 |
| frontend npm | 18パッケージ：Critical 1／High 12／Moderate 5 | (package, advisory URL)の追加0・削除0 |

[comparison.json](comparison.json) に比較結果・ロックのハッシュ・確認日時を記録。今回の生JSONは `python-lock.json.gz`、`npm-root.json.gz`、`npm-frontend.json.gz` に保存。検査は指摘を検出して終了コード1。Banditとイメージの全件再スキャンは今回は実施しておらず、前回の結果と未検査事項を引き継ぐ。

## 準備状況と実施順

Pythonの配布待ちは解消し、**既存ロックのままPython更新・回帰検証へ着手するための配布前提は揃った**。ただしツール／CA準備T2は未実施で、独自CAや対象CPUでの実体確認も残るため、全セキュリティ対応が完了した状態ではない。

1. T2の安全な取得ツール・CA準備。
2. Python 3.13.18を通常Docker／unified／CI／Dev Containerへ反映し、旧ロックで328成功・1スキップの基準と比較。
3. certifi／pip等の計画済み依存更新。その後、既存37指摘の認証・暗号・HTTP入口を利用条件と照合し、採用版を別に確定して回帰検証。
4. フロントエンドは [別計画](../../../dev/frontend-security-update-plan.ja.md) で基準テスト→Node→npm依存→Nginx素材の順に対応。バックエンドAPI契約が変わる差分は合同で確認。
5. Keycloakの取得エラー、完成アプリ／Dev Container、実通信の残件を解消し、更新後の監査・レビューを行う。本番配備は別工程。

「新規指摘なし」は既存指摘を保留してよいという判断ではない。今回修正／別対応／非該当の根拠／修正版未提供を一覧で確定する。
