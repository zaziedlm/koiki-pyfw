# フロントエンド対応タスク

2026-10-27に実装・npm ci・既存検証を実施。7ファイル21成功、全依存/本番依存監査0件。実施証拠と残件は `docs/security/implementation/2026-10-27/README.ja.md` とscenario-results.ja.mdを参照。

## 準備と更新

- [x] P0 現行SPA、Nginx、RSC非搭載、Node利用箇所、npm監査18パッケージを確認する。
- [x] P1 公式勧告と候補版のnpm提供を照合し、直近再監査で新規指摘URLの増減0を記録する。
- [ ] F0 更新前動作テストの基準を取得する（子タスク全件の結果で判定）。
- [ ] F0.1 Node／npmの実パス・版、全導入依存、manifest／lockハッシュを記録する。
- [x] F0.2 既存node_modulesの一致・実行条件を確認する。Node24.19.0の旧環境と採用候補22系を区別し、外部の未検証入力を持ち込まない。
- [x] F0.3 check-types／lint／test／buildを個別に実行し、終了コード・ログ・件数・警告を保存する。
- [x] F0.4 manifest／lock不変と生成物を確認し、既存失敗・環境制約・更新後の比較方法を記録する。
- [x] F1 Node22.23.4または同系列後続修正版の配布・digestを確定し、Docker／CI／Dev Containerを更新して旧ロックで回帰検証する。
- [x] F2 全18パッケージの入力条件、候補版、peer依存、Nginx／OS・undiciの採用版を確定する。
- [x] F3 runtime／dev／root開発ツールを別差分で更新し、manifest・lock・親依存を整合させる。
- [x] F4 各差分をnpm ciで再現し、全依存とomit=devの監査、型検査・lint・test・buildを実行する。
- [x] F5 通常／unifiedのNodeビルド素材とNginx最終イメージを検査し、OS指摘と実体を確認する。
- [ ] F6 Cookie／CSRF／SSO／SAMLと画面操作をbackendと合同確認する。
- [x] F7 frontend-ciがセキュリティブランチ／PR先で動くトリガーへ整理し、監査と戻し方を記録する。

## Scenario別検証（9件）

- [x] V-F-E1 指摘ごとの親依存・利用経路・修正版・判定根拠を照合する。
- [x] V-F-E2 Critical／Highの未確認条件を未完了として記録する。
- [x] V-F-E3 RSC非搭載の構成根拠とパッケージ修正を区別する。
- [x] V-F-S1 npm ci・型検査・lint・test・buildと採用版記録を確認する。
- [x] V-F-S2 ロック不一致・解決失敗時の中断手順をレビューする。
- [x] V-F-S3 Node内蔵部品・npm依存・最終OSを別々に検証する。
- [ ] V-F-R1 認証・登録・タスク・SSO／SAMLとCookie／CSRFの契約維持を確認する。
- [x] V-F-R2 新規失敗・除外増加時の切り分けと記録を確認する。
- [x] V-F-R3 Nginxで深いURL直アクセス・reload・静的配信を確認する。

## 引き継ぎ

- [x] Scenario9件と検証ケース9件の1対1対応を確認する。
- [x] 未修正・非到達・修正版未提供・未検証を根拠付きで記録し、OpenSpec strict検証とレビューを行う。
- [x] backendと共有するDev Container差分・API合同検証を調整し、配備は別工程に引き継ぐ。

着手手順・当初CVEとの対応・欠損依存時の再現条件は `docs/security/security-update-entry-check-2026-10-27.ja.md` 第2・5節を参照。

## 実施後の補足（2026-10-27）

チェック済みはLinux/amd64で観測したローカルの実績。CIの実行、実配備CPU、実ブラウザと管理された実IdPの合同確認、OS/ツール内蔵コピーの残件は全体完了に含めない。実施時点ではPR発行・ドラフト作成・main mergeを行わなかった。その後、依頼者の許可でmain向けドラフトPR #148を作成した（下記「PR作成後の更新」参照）。

F0/F0.1: 初回の全間接node_modules一覧は未採取。旧lockの別領域npm ci・全導入一覧・再検証を補ったが初回の全間接一致を遡って証明しないため親タスクは未完了。F6/V-F-R1: 自動UI/API契約は確認済み、実ブラウザと実IdP合同操作は未実施。F7はトリガー定義と監査/戻し方の記録までで、CIの実行を意味しない。

## PR作成後の更新（2026-10-27）

- `Frontend CI`／`CI Pipeline` はブランチのpushとドラフトPR #148で実行され、すべて成功した。F7のトリガー定義でCIが実際に動くことを確認した。
- ローカルPCで`unified-dev`／`unified-optimized`の実ブラウザ操作（ログイン、タスク一覧・作成・更新、ログアウト、CSRF再取得）を確認した。記録は `docs/security/implementation/2026-10-27/local-container-verification.ja.md`。SSO／SAMLと実IdPの合同操作は未実施のためF6／V-F-R1は未チェックのまま。
- F0／F0.1は、初回の全間接node_modules一覧を後から取得できないため未チェックのまま残し、制約付きで閉じるかは依頼者が別途判断する。
