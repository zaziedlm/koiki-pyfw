# ディレクトリ構造とコード配置

## このステアリングファイルについて

このファイルはKiroでの作業時に、コードをどこに配置すべきかを素早く判断するための簡潔なガイドです。

**詳細なルールは `docs/agent/boundaries.md` と `docs/agent/architecture.md` を参照してください。**

---

## ディレクトリ構造

```
koiki-v07/
├── components/
│   ├── libkoiki/                    # 再利用可能なフレームワーク
│   │   ├── src/libkoiki/
│   │   │   ├── api/v1/              # フレームワークAPI
│   │   │   ├── core/                # 設定、認証、ミドルウェア
│   │   │   ├── models/              # 共通モデル
│   │   │   ├── repositories/        # 共通リポジトリ
│   │   │   ├── schemas/             # 共通スキーマ
│   │   │   └── services/            # 共通サービス
│   │   └── tests/                   # フレームワークテスト
│   │
│   └── koiki_ref_app/               # リファレンスアプリケーション
│       ├── src/koiki_ref_app/
│       │   ├── api/v1/              # アプリケーションAPI
│       │   ├── asgi.py              # ASGIエントリーポイント
│       │   ├── models/              # アプリ固有モデル
│       │   ├── repositories/        # アプリ固有リポジトリ
│       │   ├── schemas/             # アプリ固有スキーマ
│       │   └── services/            # アプリ固有サービス
│       ├── alembic/                 # マイグレーション
│       └── tests/                   # アプリケーションテスト
│
├── app/                             # 互換性ラッパー（レガシー）
│   └── main.py                      # 旧エントリーポイント
│
├── frontend/                        # Next.js フロントエンド
│   ├── src/
│   │   ├── app/                     # App Router
│   │   ├── components/              # Reactコンポーネント
│   │   ├── hooks/                   # カスタムフック
│   │   ├── lib/                     # ユーティリティ
│   │   └── types/                   # TypeScript型定義
│   └── public/                      # 静的ファイル
│
├── tests/                           # ルート統合テスト
├── docs/                            # ドキュメント
│   └── agent/                       # エージェント向けガイダンス
├── ops/                             # 運用ヘルパー
└── docker/                          # Docker関連ファイル
```

---

## コード配置の判断フロー

### 1. バックエンドコードの配置

```
質問: このコードは他のアプリケーションでも使えるか？
  │
  ├─ YES → components/libkoiki/
  │         例: 認証、設定、共通ミドルウェア、汎用API
  │
  └─ NO  → components/koiki_ref_app/
            例: ビジネスロジック、SSO統合、参照ドメイン
```

### 2. 階層別の配置

| 階層 | libkoiki | koiki_ref_app |
|------|----------|---------------|
| **API層** | `src/libkoiki/api/v1/` | `src/koiki_ref_app/api/v1/` |
| **Service層** | `src/libkoiki/services/` | `src/koiki_ref_app/services/` |
| **Repository層** | `src/libkoiki/repositories/` | `src/koiki_ref_app/repositories/` |
| **Model層** | `src/libkoiki/models/` | `src/koiki_ref_app/models/` |
| **Schema層** | `src/libkoiki/schemas/` | `src/koiki_ref_app/schemas/` |
| **Core/Infrastructure** | `src/libkoiki/core/` | - |

### 3. テストの配置

```
テスト対象に合わせて配置:
- フレームワーク機能 → components/libkoiki/tests/
- アプリケーション機能 → components/koiki_ref_app/tests/
- 統合テスト → tests/
```

---

## 具体例

### ✅ 正しい配置例

**フレームワーク機能（libkoiki）:**
```python
# components/libkoiki/src/libkoiki/core/auth.py
# JWT認証の共通実装

# components/libkoiki/src/libkoiki/services/user_service.py
# 汎用的なユーザー管理サービス
```

**アプリケーション機能（koiki_ref_app）:**
```python
# components/koiki_ref_app/src/koiki_ref_app/services/sso_service.py
# SSO統合のビジネスロジック

# components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/todos.py
# Todo機能のエンドポイント（参照実装）
```

### ❌ 避けるべき配置

```python
# ❌ ビジネスロジックをlibkoikiに配置
# components/libkoiki/src/libkoiki/services/company_specific_workflow.py

# ❌ 汎用機能をkoiki_ref_appで再実装
# components/koiki_ref_app/src/koiki_ref_app/core/duplicate_auth.py

# ❌ 新規コードをapp/に配置
# app/new_feature.py
```

---

## 重要な原則

### 1. 依存の方向
```
上位層 → 下位層（OK）
下位層 → 上位層（NG）

例:
API → Service → Repository → Model（OK）
Model → Service（NG）
```

### 2. コンポーネント間の依存
```
koiki_ref_app → libkoiki（OK）
libkoiki → koiki_ref_app（NG）
```

### 3. app/の扱い
```
app/ は互換性ラッパーのみ
新規コードは components/ 配下に配置
```

---

## 迷ったときの判断基準

1. **「他のアプリでも使えるか？」** を自問する
2. 不明な場合は **koiki_ref_app に配置** してから検討
3. 既存の類似コードの配置を参考にする
4. **現在の実装が最優先**（ドキュメントより実装を信頼）

---

## Skills との協調

コード配置の判断には以下のSkillsが役立ちます：

- **koiki-project-overview**: タスク分類とレイヤー選択
- **koiki-libkoiki-feature-work**: フレームワーク層での作業
- **koiki-app-feature-work**: アプリケーション層での作業

---

## 参照先

詳細なルールは以下を参照してください：

- **docs/agent/boundaries.md**: コンポーネント境界の詳細ルール
- **docs/agent/architecture.md**: アーキテクチャの詳細
- **AGENTS.md**: エージェント向けエントリーポイント
