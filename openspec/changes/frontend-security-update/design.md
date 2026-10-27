# フロントエンド対応方針・手順

確認日: 2026-10-27（日本時間）。[直近再確認と監査差分](../../../docs/security/reviews/2026-10-27/README.md)、[更新前の生結果](../../../docs/security/audits/2026-10-26-preupdate/README.md) を参照。

[着手前点検・T2/F0の実行単位](../../../docs/security/security-update-entry-check-2026-10-27.ja.md) を参照。F0は既存ホストNode24.19.0での基準と採用候補22系での比較を区別する。Docker用独自CAは現環境では未配置だが、ローカルF0の着手条件ではない。

## 1. 必要性とレイヤ

起点は会話当初のeMudhra／emSign証明書事件とCVE-2026-111497（Brotli）。CVE-2026-115557自体はCPythonの対策としてSPEC-101へ委ね、frontendでは同事件のNode／CAへの波及を扱う。

**セキュリティ更新は必要**。npm監査18パッケージとNodeの内蔵Brotli／CA、配信イメージのOS部品が対象である。React本体の脆弱性が現行構成で確認されたという意味ではない。

frontend/src/main.tsxはreact-dom/clientのcreateRoot、routes/index.tsxはBrowserRouterを使うブラウザSPA。vite.config.tsは@vitejs/plugin-reactを使い、ロックには@vitejs/plugin-rsc、react-server-dom-webpack等やNext.jsが存在しない。productionはNginxへdistのみコピーする。Nodeプロセスが本番HTTPを処理するSSR／RSC構成ではない。

配置はdocs/agent/boundaries.mdとdocs/frontend-spa-implementation-guide.ja.mdに従い、frontend/へ閉じる。components/libkoiki/とcomponents/koiki_ref_app/はAPI・認証の提供側として合同試験の対象にし、依存更新を理由に認可・Cookie・CSRFを緩和しない。root package.jsonはOpenSpec開発ツール用でありfrontendの依存とは混ぜない。

## 2. 対象の仕分け

| 区分 | 現状 | 方針 |
| --- | --- | --- |
| React／react-dom | ともに19.2.7、今回の監査で両パッケージ自体の指摘なし | 現構成に対する新規指摘を確認できず。RSC対策だけを理由に19.3系へ一括更新しない。変更する場合は両者を同じ系列で評価 |
| React Router | 7.18.1、High。GHSA-qwww-vcr4-c8h2はRSC ModeのCSRF問題 | 現構成はBrowserRouterでRSC actionサーバーなし。当該経路は非到達と暫定判断。修正候補7.18.2を回帰評価し将来の構成変更も防御 |
| Zod | 4.0.10、High。過大なcollection検証のメモリ消費 | フォーム・入力検証の利用を確認し、修正候補4.6.6を評価 |
| Vite | 7.3.6、High。dev server／editor連携／ファイル公開等の指摘 | 修正候補7.3.7。0.0.0.0で起動するdev／previewの公開範囲とホスト側ポート制限も確認 |
| Vitest／mocker | Vitest4.1.10、Moderate等 | 修正候補Vitest4.1.11と整合するmockerを評価 |
| tar | 7.4.3、Critical、dev依存。@tailwindcss/oxideから到達 | 修正候補7.5.21。親依存を含めてlock解決と不正archiveの入力条件を確認。ブラウザRCEとは扱わない |
| undici | 7.28.0、High、jsdomから到達するdev依存 | 公式勧告の全対象範囲を満たす版をF2で確定。Node内蔵undiciとは別更新 |
| その他間接依存 | ajv、brace-expansion、minimatch、postcss等を含む | 18パッケージすべてのID・親依存・入力元を表にして、修正／非該当理由／保留を判定 |
| Node.js | Dockerは22-slim、CIは22、Dev ContainerはNodeSource22系 | **22.23.4**を候補にBrotli／CA対策を反映。実装時に同じ22系の後続修正版の有無と公式イメージ提供を再確認 |
| Nginx／OS | 1.30.3-alpine。既存Trivy指摘あり | 当該系列の修正済み配信イメージとOS部品をF2で確定。タグのみで安全と判定しない |
| root OpenSpec用依存 | root npmのzodにHigh | 親依存とrootロックを別更新。frontend側だけの修正で対応済みと扱わない |

修正候補react-router7.18.2、vite7.3.7、vitest4.1.11、zod4.6.6、tar7.5.21はnpm公式レジストリで公開・非deprecatedとNode要件を確認した。[候補のメタデータ](../../../docs/security/reviews/2026-10-27/npm-candidates.json) にintegrityを保存。これは採用完了や全間接依存の解消保証ではなく、F2のpeer依存・解決・回帰確認で採用を確定する。

## 3. 公式情報と該当性

- [Node22.23.4](https://nodejs.org/en/blog/release/v22.23.4) はCVE-2026-111497、CA・TLS等の修正を含む。npm auditだけでは内蔵部品の対処は完了しない。
- [RSCプラグインの重大勧告](https://github.com/vitejs/vite-plugin-react/security/advisories/GHSA-59pf-q495-3c99) は@vitejs/plugin-rscに内蔵されたreact-server-dom-webpackが対象。現構成で対象パッケージなし。Reactの導入だけで該当とは扱わない。
- [React RouterのRSC CSRF勧告](https://github.com/advisories/GHSA-qwww-vcr4-c8h2) はRSC Modeのサーバーaction処理を確認する。現構成の非到達は、パッケージの修正済みを意味しない。
- [Viteの公式勧告](https://github.com/vitejs/vite/security/advisories) とnpm監査の各viaを照合する。Windows限定やカスタムmiddleware限定の条件も残す。

2026-10-26から27への同一ロック再監査では新規指摘URLの追加・削除は0。現在の既存指摘は残る。将来RSC／SSRを導入する変更では、対象パッケージと公開処理を再評価する。

## 4. 段階的な実施手順

1. **F0 基準取得**: 現在のNode／npm、導入版とロックの一致、OSと実行環境を記録。既存環境でcheck-types／lint／test／buildを実行し、件数・失敗・警告を保存する。本計画作成では未実施。
2. **F1 ランタイム**: 修正版Node22系を開発用Dockerfile2種、CI、Dev Containerに反映。旧npmロックのままnpm ciと基準検証を行う。NODE_EXTRA_CA_CERTSとOS CAの両方を確認する。
3. **F2 採用版確定**: 18パッケージのviaと候補版、peer依存、Node要件、変更が必要なmanifest範囲を確定する。Nginx／OSとundiciもここで確定する。
4. **F3 依存更新**: runtime系（Zod／Router）、dev系（Vite／Vitest／関連間接依存）、root開発ツールを別の差分として対象指定で更新。npm audit fix --forceや無関係なmajor更新はしない。親依存更新を優先し、overridesが必要なら理由と解除条件を記録する。
5. **F4 検証**: 各差分でcheck-types／lint／test／buildと全依存・本番依存のnpm監査を実施。増えた失敗・警告・除外は説明する。監査の成功だけで動作互換性を判定しない。
6. **F5 配信物**: 修正済みNginx／OSイメージを採用して通常版・unifiedを再ビルド。ビルド用Nodeイメージと最終Nginxイメージの両方を検査し、Nodeや開発依存が最終配信物に混入していないことを確認する。
7. **F6 ブラウザ・合同確認**: 管理された検証環境でログイン・ログアウト・登録・認証ガード・タスク操作・SSO／SAML callback・Cookie／CSRFを確認する。バックエンド更新側と同じAPI契約を保つ。接続先未提供は未検証として残す。
8. **F7 レビュー**: before／after監査、digest、未修正と非到達の根拠、戻し方をまとめる。実際の更新はバックエンドと別コミット／PR単位で比較可能にする。本番配備は別工程。

フロントエンドCIの現在の対象はdev/v0.8へのpush／PRのみ。セキュリティ用ブランチやmainへのPRでも検証が走るか、実装時にトリガーを見直すタスクを含める。ガード削除などの機能変更を混ぜない。

## 5. 検証コマンドと完了の判断

frontend/で実行する。

```sh
npm run check-types
npm run lint
npm test
npm run build
npm audit --package-lock-only --ignore-scripts --json
npm audit --omit=dev --package-lock-only --ignore-scripts --json
```

更新前監査ではnpm ciや依存解決を行わなかった。実装時のクリーン再現は、安全なNode／取得環境でnpm ciを行い、ロックを変更しないことを確認してから検証する。更新後は変更したmanifestとlockを揃えてnpm ciで再現する。rootの監査はrootで別に行う。

既存テストは7ファイル（http-client、react-query、tasks/auth queries、login/register form、auth-guard）。SSO／SAMLの実IdP試験、Nginxの深いURLへの直接アクセス・reload、CSP／静的配信、OS脆弱性まで網羅したテストではない。必要なAPI合同確認と配信物確認を追加する。

完了はデルタSpecの9 Scenarioを正本とする。ロックの再現、全検査成功、新規失敗なし、未説明の除外増加なし、修正または根拠付き判定の記録が必要。Critical／High残存は利用条件・修正版・修正予定または例外判断を示し、単にdev依存という理由で無視しない。

## 6. 共有ファイルと戻し方

Dev ContainerはPython／uv／CAとNodeが同居するため、SPEC-101とSPEC-201で変更箇所を共有する。片方の更新で他方の差分を戻さず、共通検証環境で両ランタイムを確認する。バックエンドのPython公開待ちをフロントエンド更新の依存条件にはしない。

戻す場合はNode／npm依存定義／ロック／配信イメージを同じ検証済みの組に揃え、前のコミット単位で戻す。旧脆弱版への自動再配備はせず、隔離環境で原因を調べる。API互換性やフロントエンドのみの変更で回避できない場合は別の仕様変更として起票する。
