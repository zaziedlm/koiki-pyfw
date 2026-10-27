# React参考アプリのセキュリティ更新

## メタ情報

- change-name: frontend-security-update
- 所属機能Spec: frontend-security-maintenance
- 実装Spec種別: セキュリティ横断
- Spec番号: SPEC-201
- 作成日: 2026-10-27（日本時間）
- 状態: 対応整理・手順作成。更新実装は未着手。

## Why

参考実装のReact SPAにも、npmロック、Node.js、開発・ビルド・テスト環境、NginxとOSに既知脆弱性の指摘がある。ブラウザ配信物とNodeサーバー・ツールの違い、RSCの利用条件を区別して対応し、認証・CSRF・SSO／SAMLと画面操作を維持した更新を行うために、対象と検証手順を定める。

## What Changes

- 既存の18パッケージ指摘とNode／配信イメージを仕分ける。
- 既存テストによる更新前の基準を取得してから、Node・npm依存・配信イメージを段階的に更新する。
- RSC未導入の根拠を記録し、React使用だけでサーバー側脆弱性へ該当と判定しない。
- rootの開発ツールの監査をfrontendとは別のロックで管理する。
- 今回は文書化と再監査のみで、ソース・依存定義・ロック・Docker・CIは変更しない。

## Capabilities

### New Capabilities

- frontend-security-maintenance: React SPAとその開発・ビルド・配信環境の安全な保守。

### Modified Capabilities

なし。

## Impact

主対象はfrontend/、frontend-ci、Dev Container内のNodeとCA。root package.jsonは開発ツール用として別管理する。API契約・認証認可の主体はbackendで維持し、apps/へフロントエンドを移設しない。本番配備は別工程。
