# フロントエンド対応タスク

今回は整理・監査再確認のみ。実装と更新前の動作テストは未着手。

## 準備と更新

- [x] P0 現行SPA、Nginx、RSC非搭載、Node利用箇所、npm監査18パッケージを確認する。
- [x] P1 公式勧告と候補版のnpm提供を照合し、直近再監査で新規指摘URLの増減0を記録する。
- [ ] F0 Node／npm・導入版・ロックを記録し、更新前check-types／lint／test／buildの基準を取得する。
- [ ] F1 Node22.23.4または同系列後続修正版の配布・digestを確定し、Docker／CI／Dev Containerを更新して旧ロックで回帰検証する。
- [ ] F2 全18パッケージの入力条件、候補版、peer依存、Nginx／OS・undiciの採用版を確定する。
- [ ] F3 runtime／dev／root開発ツールを別差分で更新し、manifest・lock・親依存を整合させる。
- [ ] F4 各差分をnpm ciで再現し、全依存とomit=devの監査、型検査・lint・test・buildを実行する。
- [ ] F5 通常／unifiedのNodeビルド素材とNginx最終イメージを検査し、OS指摘と実体を確認する。
- [ ] F6 Cookie／CSRF／SSO／SAMLと画面操作をbackendと合同確認する。
- [ ] F7 frontend-ciがセキュリティブランチ／PR先で動くトリガーへ整理し、監査と戻し方を記録する。

## Scenario別検証（9件）

- [ ] V-F-E1 指摘ごとの親依存・利用経路・修正版・判定根拠を照合する。
- [ ] V-F-E2 Critical／Highの未確認条件を未完了として記録する。
- [ ] V-F-E3 RSC非搭載の構成根拠とパッケージ修正を区別する。
- [ ] V-F-S1 npm ci・型検査・lint・test・buildと採用版記録を確認する。
- [ ] V-F-S2 ロック不一致・解決失敗時の中断手順をレビューする。
- [ ] V-F-S3 Node内蔵部品・npm依存・最終OSを別々に検証する。
- [ ] V-F-R1 認証・登録・タスク・SSO／SAMLとCookie／CSRFの契約維持を確認する。
- [ ] V-F-R2 新規失敗・除外増加時の切り分けと記録を確認する。
- [ ] V-F-R3 Nginxで深いURL直アクセス・reload・静的配信を確認する。

## 引き継ぎ

- [ ] Scenario9件と検証ケース9件の1対1対応を確認する。
- [ ] 未修正・非到達・修正版未提供・未検証を根拠付きで記録し、OpenSpec strict検証とレビューを行う。
- [ ] backendと共有するDev Container差分・API合同検証を調整し、配備は別工程に引き継ぐ。
