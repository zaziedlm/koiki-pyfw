# プロダクト概要

## KOIKI-FW v0.6.1

KOIKI-FW は Python (FastAPI) を用いたエンタープライズ向け Web アプリケーション構築のための堅牢な基盤フレームワークです。

## 主要機能

### 認証・セキュリティ
- JWT認証（アクセストークン + リフレッシュトークン）
- パスワードリセット機能
- ログイン試行制限・セキュリティ監視
- RBAC（ロールベースアクセス制御）
- レート制限（slowapi）
- CSRF保護

### 外部認証連携
- OpenID Connect (OIDC) SSO認証
- SAML 2.0 認証
- Keycloak統合

### アーキテクチャ
- **libkoiki/**: フレームワークコアライブラリ（認証、ユーザー管理、Todo等の主要機能を実装）
- **app/**: アプリケーション固有の拡張（SSO/SAML連携、ビジネスロジック）
- **frontend/**: Next.js 15 + React 19 フロントエンド

### フルスタック統合
- Cookie認証によるセキュアなAPI通信
- Next.js Route Handlers によるバックエンドプロキシ
- TanStack Query によるサーバー状態管理
- TypeScript + Pydantic による型安全性

## 設計思想

1. **関心事の分離**: API層 → Service層 → Repository層 → Model層
2. **フレームワークとアプリの分離**: libkoiki（再利用可能）と app（プロジェクト固有）
3. **セキュリティファースト**: エンタープライズグレードのセキュリティ実装
4. **非同期処理**: 高パフォーマンスな async/await ベースの実装
