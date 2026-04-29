# プロダクト概要

## KOIKI-FW

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
- **components/libkoiki/**: reusable framework package
- **components/koiki_ref_app/**: reference application package（SSO/SAML連携、参照ドメイン）
- **app/**: legacy compatibility wrapper
- **frontend/**: Next.js 15 + React 19 フロントエンド

### フルスタック統合
- Cookie認証によるセキュアなAPI通信
- Next.js Route Handlers によるバックエンドプロキシ
- TanStack Query によるサーバー状態管理
- TypeScript + Pydantic による型安全性

## 設計思想

1. **関心事の分離**: API層 → Service層 → Repository層 → Model層
2. **フレームワークとアプリの分離**: components/libkoiki（再利用可能）と components/koiki_ref_app（参照アプリ）
3. **セキュリティファースト**: エンタープライズグレードのセキュリティ実装
4. **非同期処理**: 高パフォーマンスな async/await ベースの実装
