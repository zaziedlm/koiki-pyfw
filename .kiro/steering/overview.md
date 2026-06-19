# プロジェクト概要

## このステアリングファイルについて

このファイルはKiro（AI開発環境）での作業効率を高めるため、プロジェクトの基本情報を簡潔にまとめています。

**詳細なガイダンスとの関係:**
- **AGENTS.md**: エージェント向けエントリーポイント → `docs/agent/`への誘導
- **docs/agent/**: 詳細なアーキテクチャ、境界、テスト方針
- **Skills (.claude/skills/)**: タスク別の専門的なガイダンス
- **このステアリングファイル**: Kiroが常に把握すべき基本情報のサマリー

これらは協調して動作し、重複を避けながら必要な情報を提供します。

---

## KOIKI-FW とは

KOIKI-FW は Python (FastAPI) を用いたエンタープライズ向け Web アプリケーション構築のための堅牢な基盤フレームワークです。

### 主要な特徴

- **フレームワークとアプリの分離**: 再利用可能なフレームワーク層と参照アプリケーション層
- **エンタープライズセキュリティ**: JWT認証、RBAC、SSO/SAML統合
- **フルスタック統合**: FastAPI + Next.js 15 + React 19
- **非同期処理**: async/await ベースの高パフォーマンス実装

---

## コンポーネント構造

```
components/
├── libkoiki/              # 再利用可能なフレームワーク
│   ├── src/libkoiki/      # フレームワークコード
│   └── tests/             # フレームワークテスト
└── koiki_ref_app/         # リファレンスアプリケーション
    ├── src/koiki_ref_app/ # アプリケーションコード
    └── tests/             # アプリケーションテスト

app/                       # 互換性ラッパー（レガシー）
frontend/                  # Next.js フロントエンド
tests/                     # 統合テスト
docs/                      # ドキュメント
```

### コンポーネントの役割

| コンポーネント | 役割 | 配置すべきコード |
|--------------|------|----------------|
| **libkoiki** | 再利用可能なフレームワーク | 認証、設定、ミドルウェア、共通API、インフラ |
| **koiki_ref_app** | リファレンスアプリケーション | ビジネスロジック、SSO/SAML統合、参照ドメイン |
| **app** | 互換性ラッパー | レガシーインポートのみ（新規作業では使用しない） |

**判断基準**: 「他のアプリケーションでも使えるか？」→ Yes なら libkoiki、No なら koiki_ref_app

---

## 技術スタック

### バックエンド
- **Python**: >=3.11.7
- **FastAPI**: ASGI Webフレームワーク
- **SQLAlchemy 2.0**: 非同期ORM
- **Alembic**: マイグレーション管理
- **PostgreSQL / SQLite**: 本番・開発/テストDB
- **uv**: 依存同期とコマンド実行（uv.lock が正本）

### フロントエンド
- **Next.js 15**: App Router
- **React 19**
- **TypeScript**
- **Tailwind CSS**
- **TanStack Query**: サーバー状態管理
- **Zustand**: クライアント状態管理

### 認証・セキュリティ
- JWT認証（アクセストークン + リフレッシュトークン）
- RBAC（ロールベースアクセス制御）
- OpenID Connect (OIDC) SSO
- SAML 2.0 認証
- Keycloak統合

---

## 階層アーキテクチャ

```
API層（エンドポイント、バリデーション）
    ↓
Service層（ビジネスロジック）
    ↓
Repository層（永続化、クエリ）
    ↓
Model層（DB構造、スキーマ）
    ↓
Core/Infrastructure層（設定、認証、ミドルウェア）
```

**重要**: 下位層が上位層に依存しないこと

---

## エントリーポイント

### 現在の推奨エントリーポイント
```python
# koiki_ref_app.asgi:app
```

### レガシー互換エントリーポイント
```python
# app.main:app （新規作業では使用しない）
```

---

## Skills との協調

このプロジェクトには以下のSkillsが定義されています：

- **koiki-project-overview**: タスク分類とレイヤー選択
- **koiki-libkoiki-feature-work**: フレームワーク層（components/libkoiki/）の機能開発
- **koiki-refapp-feature-work**: リファレンスアプリ層（components/koiki_ref_app/）の機能開発
- **koiki-business-app-feature-work**: ダウンストリーム業務アプリ層（apps/）の機能開発
- **koiki-auth-security**: 認証・セキュリティ関連作業
- **koiki-testing**: テスト作成・実行

**Skillsは `docs/agent/skills/` の詳細ガイダンスを参照します。**
**このステアリングファイルは基本情報のサマリーとして、Skillsと協調動作します。**

---

## 参照先

詳細な情報は以下を参照してください：

- **AGENTS.md**: エージェント向けエントリーポイント
- **docs/agent/boundaries.md**: コンポーネント境界の詳細ルール
- **docs/agent/architecture.md**: アーキテクチャの詳細
- **docs/agent/testing.md**: テスト戦略
- **docs/agent/auth-security.md**: 認証・セキュリティの詳細
