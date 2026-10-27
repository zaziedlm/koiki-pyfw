# フロントエンドの安全な保守（frontend-security-maintenance）

## Purpose

認証と業務画面の参考実装を維持しながら、フロントエンドの配信物・ランタイム・依存関係の脆弱性を根拠に基づいて扱い、開発環境の問題と利用者へ配信される画面の問題を混同せずに更新・検証する。

## 業務処理概要

保守担当者はnpm依存と実行・配信基盤の指摘を分類し、認証と業務操作の継続を確認して運用へ引き継ぐ。「RSC」はReact Server Componentsのサーバー側処理、「SPA」はブラウザで実行し静的配信する画面、「合同試験」はbackendのAPI・Cookie・CSRFと一緒に確認する試験を指す。

## 業務目線の入出力

入力は現構成と脆弱性情報、出力は適用判定・更新内容・検証結果・未完了事項の記録。

## 基本情報

- capability名: frontend-security-maintenance
- 番台対応: 本案件の200番台
- 主なレイヤ: frontend/と開発・配信基盤
- backendの認可仕様変更と本番配備は本Specの対象外とし、各担当工程に委ねる。
- 状態: 計画段階の意図仕様であり更新済みを意味しない。

## Requirements

### Requirement: フロントエンド指摘の適用範囲

- 【SHALL】担当者は、ブラウザ配信、RSCサーバー、開発・ビルド・テスト、Node内蔵部品、配信OSを区別して指摘を判定しなければならない。
- 【SHALL NOT】担当者は、React使用だけを理由にRSC脆弱性へ該当と判定してはならない。

#### Scenario: F-E1 正常系 - 依存の指摘を分類
- **WHEN** 現行ロックの指摘を処理する
- **THEN** 親依存・利用経路・修正版・判定根拠を記録する

#### Scenario: F-E2 異常系 - 未確認の利用条件
- **WHEN** CriticalまたはHigh指摘の到達条件を確認していない
- **THEN** 対応済みとせず確認タスクを残す

#### Scenario: F-E3 境界値 - RSC非搭載
- **WHEN** 現行SPAにRSCパッケージとサーバー処理が存在しない
- **THEN** 非到達の構成根拠を記録してパッケージ修正済みと区別する

### Requirement: 更新の再現と信頼

- 【SHALL】担当者は、Node・npmロック・ビルド素材・配信イメージの版と検査結果を記録しなければならない。
- 【SHALL NOT】担当者は、更新のためにTLS検証またはCookie・CSRF保護を無効化してはならない。

#### Scenario: F-S1 正常系 - クリーン再現
- **WHEN** 修正後ロックでクリーン環境を構築する
- **THEN** npm ciと型検査・lint・テスト・buildが成功し採用版を記録する

#### Scenario: F-S2 異常系 - ロックの不一致
- **WHEN** manifestとlockが不一致または解決に失敗する
- **THEN** 更新を完了とせず原因を記録する

#### Scenario: F-S3 境界値 - Node更新のみ
- **WHEN** NodeのBrotli修正を反映する
- **THEN** npm依存と最終Nginxの検査を別項目として残す

### Requirement: SPA機能と配信契約の維持

- 【SHALL】担当者は、更新前後の既存テストと認証・画面・配信契約の比較結果を保存しなければならない。
- 【SHALL NOT】担当者は、新規失敗や未検証の合同試験を残した状態で全体を完了としてはならない。

#### Scenario: F-R1 正常系 - 既存操作の継続
- **WHEN** 更新後のSPAで認証・登録・タスク・SSO／SAML遷移を確認する
- **THEN** API契約とCookie／CSRF保護を維持し結果を記録する

#### Scenario: F-R2 異常系 - 回帰の検出
- **WHEN** 新規失敗または未説明のテスト除外を検出する
- **THEN** 次の更新を止めて原因を切り分ける

#### Scenario: F-R3 境界値 - 静的配信
- **WHEN** productionのNginxイメージを検証する
- **THEN** 深いURLの直接アクセスと静的配信を確認しNodeの開発環境の検査と区別する
