# KOIKI-FW プロジェクト 概要

## プロジェクトの目的
KOIKI-FW は、Python FastAPIを基盤とした**エンタープライズ向けWebアプリケーション構築フレームワーク**です。本格的なビジネスアプリケーション開発に必要な機能を包括的に提供します。

## 主要な特徴
- **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery等
- **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離アーキテクチャ
- **非同期処理**: 高パフォーマンスな非同期処理対応
- **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上
- **強化されたセキュリティ**: JWT認証, リフレッシュトークン, RBAC, レートリミット等
- **認証系API**: 包括的な認証システム（基本認証、パスワード管理、トークン管理）
- **監視・ロギング**: 構造化ログ, 監査ログ, Prometheus連携
- **フロントエンド統合**: Next.js + TypeScript による現代的なWebUI

## プロジェクト構成
```
koiki-pyfw/
├── components/
│   ├── libkoiki/     # reusable framework package
│   └── koiki_ref_app/# reference application package
├── app/              # 互換 wrapper
├── frontend/         # Next.js + TypeScript フロントエンド
├── tests/            # shared / cross-component tests
├── docs/             # 詳細なドキュメント
└── ops/              # 運用スクリプト・ツール
```

## 開発環境の特徴
- **Windows対応**: PowerShellスクリプトによる開発環境構築
- **Docker対応**: docker-compose.ymlによるコンテナ環境
- **CI/CD**: GitHub Actionsによる自動テスト・品質チェック
- **包括的テスト**: 単体・統合・セキュリティテストの完全分離

## バージョン情報
- **Python**: 3.11.7+
