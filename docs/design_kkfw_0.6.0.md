# KOIKI-FW v0.6.0

---

本ドキュメントは、エンタープライズ向けFastAPIベースのWebアプリケーション開発フレームワーク「KOIKI-FW」のバージョンである v0.6.0 に対応した機能設計・構成ガイドです。
このバージョンでは、v0.5.0の基本構成とセキュリティ修正を継承しながら、認証系APIの充実とセキュリティ監査APIの強化、包括的なドキュメント整備が実施されました。

---

## 目次

- [01. はじめに](#01-はじめに)
    - [🔰 用語解説](#01はじめに-用語解説)
- [02. アーキテクチャ概要](#02-アーキテクチャ概要)
    - [2.1 プロジェクト構造とレイヤー](#21-プロジェクト構造とレイヤー)
    - [2.2 依存関係の流れ](#22-依存関係の流れ)
- [03. ディレクトリ構成](#03-ディレクトリ構成)
    - [3.1 libkoiki (フレームワークコア)](#31-libkoiki-フレームワークコア)
    - [3.2 app (アプリケーション固有)](#32-app-アプリケーション固有)
- [04. 設定（Config）と依存性注入（DI）](#04-設定configと依存性注入di)
    - [🔰 用語解説](#04設定configと依存性注入di-用語解説)
    - [4.1 設定管理 (config.py)](#41-設定管理-configpy)
    - [4.2 依存性注入 (dependencies.py)](#42-依存性注入-dependenciespy)
- [05. モデル & スキーマ層](#05-モデルスキーマ層)
    - [🔰 用語解説](#05モデルスキーマ層-用語解説)
    - [5.1 データベースモデル (SQLAlchemy)](#51-データベースモデル-sqlalchemy)
    - [5.2 APIスキーマ (Pydantic)](#52-apiスキーマ-pydantic)
- [06. リポジトリ層](#06-リポジトリ層)
    - [🔰 用語解説](#06リポジトリ層-用語解説)
    - [6.1 ベースリポジトリ](#61-ベースリポジトリ)
    - [6.2 具体的なリポジトリ実装](#62-具体的なリポジトリ実装)
- [07. サービス層](#07-サービス層)
    - [🔰 用語解説](#07サービス層-用語解説)
    - [7.1 サービスクラスの実装](#71-サービスクラスの実装)
    - [7.2 トランザクション管理](#72-トランザクション管理)
- [08. 認証・認可（JWT）](#08-認証認可jwt)
    - [🔰 用語解説](#08認証認可jwt-用語解説)
    - [8.1 JWT認証の実装](#81-jwt認証の実装)
    - [8.2 認証APIエンドポイント](#82-認証apiエンドポイント)
    - [8.3 ロールベースアクセス制御 (RBAC)](#83-ロールベースアクセス制御-rbac)
- [09. 非同期処理（Celery & Redis）](#09-非同期処理celeryredis)
    - [🔰 用語解説](#09非同期処理celeryredis-用語解説)
    - [9.1 Celeryによる非同期タスク](#91-celeryによる非同期タスク)
    - [9.2 イベントシステム (オプション)](#92-イベントシステム-オプション)
    - [9.3 Celeryの本番運用に関する考慮事項](#93-celeryの本番運用に関する考慮事項)
- [10. アプリケーション実装例と起動方法 (app/)](#10-アプリケーション実装例と起動方法-app)
    - [10.1 app/main.py](#101-appmainpy)
    - [10.2 app/routers/todo_router.py](#102-approuterstodo_routerpy)
    - [10.3 app/services/todo_service.py](#103-appservicestodo_servicepy)
    - [10.4 app/repositories/todo_repository.py](#104-apprepositoriestodo_repositorypy)
    - [10.5 libkoiki/models/todo.py](#105-libkoikimodelstodopy)
    - [10.6 libkoiki/schemas/todo.py](#106-libkoikischemastodopy)
    - [10.7 app/api/dependencies.py (アプリケーション固有の依存性)](#107-appapidependenciespy-アプリケーション固有の依存性)
    - [10.8 データベースマイグレーション (Alembic)](#108-データベースマイグレーション-alembic)
    - [10.9 起動方法](#109-起動方法)
- [11. エラーハンドリングと例外処理](#11-エラーハンドリングと例外処理)
    - [11.1 カスタム例外](#111-カスタム例外)
    - [11.2 グローバル例外ハンドラー](#112-グローバル例外ハンドラー)
- [12. ロギングとモニタリング](#12-ロギングとモニタリング)
    - [🔰 用語解説 (ロギング)](#12ロギングとモニタリング-用語解説-ロギング)
    - [12.1 ロギング設定 (structlog)](#121-ロギング設定-structlog)
    - [12.2 監査ログ](#122-監査ログ)
    - [12.3 ミドルウェアによるモニタリング (リクエストログ)](#123-ミドルウェアによるモニタリング-リクエストログ)
    - [🔰 用語解説 (モニタリング)](#12ロギングとモニタリング-用語解説-モニタリング)
    - [12.4 Prometheus メトリクス](#124-prometheus-メトリクス)
- [13. セキュリティ](#13-セキュリティ)
    - [🔰 用語解説 (セキュリティ一般)](#13セキュリティ-用語解説-セキュリティ一般)
    - [13.1 レートリミット (slowapi)](#131-レートリミット-slowapi)
    - [13.2 セキュリティヘッダ](#132-セキュリティヘッダ)
    - [13.3 入力バリデーション](#133-入力バリデーション)
    - [🔰 用語解説 (パスワードセキュリティ)](#13セキュリティ-用語解説-パスワードセキュリティ)
    - [13.4 パスワードポリシー](#134-パスワードポリシー)
- [14. テスト戦略とテスト実装](#14-テスト戦略とテスト実装)
    - [🔰 用語解説 (テストの種類)](#14テスト戦略とテスト実装-用語解説-テストの種類)
    - [14.1 テスト設定 (conftest.py)](#141-テスト設定-conftestpy)
    - [14.2 単体テスト例](#142-単体テスト例)
    - [🔰 用語解説 (モック)](#14テスト戦略とテスト実装-用語解説-モック)
    - [14.3 統合テスト例](#143-統合テスト例)
- [15. ロールと権限](#15-ロールと権限)
    - [15.1 ロール・権限モデル](#151-ロール権限モデル)
    - [15.2 権限チェックの実装](#152-権限チェックの実装)
- [16. UI/UX実装の選択肢](#16-uiux実装の選択肢)
    - [🔰 用語解説 (UI/UX)](#16uiux実装の選択肢-用語解説-uiux)
- [17. 継続的インテグレーション (CI)](#17-継続的インテグレーション-ci)
    - [🔰 用語解説 (CI/CD)](#17継続的インテグレーション-ci-用語解説-cicd)
    - [17.1 GitHub Actions によるCI](#171-github-actions-によるci)
    - [17.2 CIパイプラインの構成](#172-ciパイプラインの構成)
    - [17.3 テスト自動化とカバレッジ](#173-テスト自動化とカバレッジ)
    - [17.4 CI環境の設定](#174-ci環境の設定)
- [18. まとめ](#18-まとめ)
- [19. 今後の拡張・DDDへの布石](#19-今後の拡張dddへの布石)
- [20. バージョン履歴](#20-バージョン履歴)
- [おわりに](#おわりに)

## 01. はじめに

KOIKI-FW は、FastAPI による堅牢かつ拡張可能な Web アプリケーションを構築するためのエンタープライズ向けテンプレートフレームワークです。

本フレームワークは以下のような目的で設計されています：

- エンジニアが業務アプリケーションを迅速に立ち上げられる **開発基盤の提供**
- インフラとロジックを明確に分離し、**保守性・再利用性・テスト容易性** を実現
- 非同期処理やJWT認証など、**実務要件に即した機能モジュールの標準搭載**
- 将来的な DDD（ドメイン駆動設計）導入を視野に入れた、拡張可能な構造

KOIKI-FW v0.6.0 では、v0.5.0 の堅牢なセキュリティ基盤を継承しながら、**認証系APIの充実**と**セキュリティ監査APIの強化**を重点的に実施しました。JWT認証、リフレッシュトークン、パスワードリセット、ログイン試行制限など、エンタープライズ環境で求められる包括的な認証システムを標準提供し、実務に即した認証・認可機能を実現しています。

KOIKI-FW は以下を目的としたフレームワークです：

- **高い拡張性**を持つ FastAPI ベースのアプリ基盤
- **業務アプリに求められる非同期処理、認証、権限、DB操作の統合**
- **DDD（ドメイン駆動設計）への段階的な移行が可能な構造**

---

### 🔰 用語解説

- **FastAPI**: PythonのモダンなWebフレームワーク。高いパフォーマンスと開発効率が特徴。
- **SQLAlchemy**: PythonのORM（Object-Relational Mapper）ライブラリ。データベース操作をPythonオブジェクトとして扱える。
- **Pydantic**: Pythonのデータバリデーションライブラリ。型ヒントに基づきデータの検証やシリアライズを行う。
- **JWT (JSON Web Token)**: Webで安全に情報をやり取りするためのコンパクトなトークン形式。認証によく用いられる。
- **Celery**: Pythonで人気の非同期タスクキュー/ジョブキュー。時間のかかる処理をバックグラウンドで実行するのに使う。
- **非同期処理**: 処理を待たずに裏で同時に実行する仕組み。例：Celery などのバックグラウンド処理。
- **Redis**: メッセージキューとしても使える高速なインメモリデータストア。
- **DDD (ドメイン駆動設計)**: ビジネスの関心事（ドメイン）を中心にソフトウェアを設計するアプローチ。

## 02. アーキテクチャ概要

本フレームワークは、関心事の分離 (Separation of Concerns) を重視したレイヤードアーキテクチャを採用しています。

### 2.1 プロジェクト構造とレイヤー

-   **APIレイヤー** (`app/routers/`, `libkoiki/api/v1/endpoints/`):
    *   HTTPリクエストの受信、ルーティング、入力バリデーション（Pydantic スキーマ経由）、レスポンス整形。
    *   依存性注入を利用してサービス層を呼び出す。
    *   認証・認可、レートリミットの適用。
-   **サービスレイヤー** (`app/services/`, `libkoiki/services/`):
    *   アプリケーションのコアとなるビジネスロジックを実装。
    *   複数のリポジトリを組み合わせてユースケースを実現。
    *   トランザクション管理の責務を持つ。
    *   API層や他のサービスから利用される。
-   **リポジトリレイヤー** (`app/repositories/`, `libkoiki/repositories/`):
    *   データ永続化層（データベース）へのアクセスを抽象化。
    *   SQLAlchemy を使用した CRUD 操作やカスタムクエリの実装。
    *   サービス層から利用される。
-   **モデルレイヤー** (`libkoiki/models/`, `libkoiki/schemas/`, `app/models/`, `app/schemas/`):
    *   `models/`: SQLAlchemy を用いたデータベーステーブル定義 (ORM モデル)。
    *   `schemas/`: Pydantic を用いた API のリクエスト/レスポンスデータ構造定義、およびバリデーションルール。
-   **コア・インフラストラクチャレイヤー** (`libkoiki/core/`, `libkoiki/db/`, `libkoiki/tasks/`):
    *   設定 (`config.py`)、セキュリティ (`core/security.py`)、カスタム例外 (`exceptions.py`)、トランザクション管理 (`transaction.py`)、ロギング (`logging.py`)、データベース接続管理など。

### 2.2 依存関係の流れ

以下に、主要コンポーネント間の依存関係の流れをテキストベースで示します。

```
[Client / External System]
  |
  (HTTP Request)
  V
[API Layer (FastAPI Routers in app/ or libkoiki/api/v1/endpoints/)]
  |  -------------------------------------------------------> [Authentication/Authorization (libkoiki/core/security.py)]
  |  -------------------------------------------------------> [Configuration (libkoiki/core/config.py)]
  |  -------------------------------------------------------> [Logging (libkoiki/core/logging.py)]
  |  -------------------------------------------------------> [Monitoring (libkoiki/core/monitoring.py)]
  |
  (Calls Service, Uses Schemas)
  V
[Service Layer (Business Logic in app/services/ or libkoiki/services/)]
  |  -------------------------------------------------------> [Configuration]
  |  -------------------------------------------------------> [Logging]
  |  ---- (May Publish Events) -----------------------------> [Message Queue (Redis via libkoiki/events/ - Optional)]
  |  ---- (May Dispatch Tasks) -----------------------------> [Task Queue (Celery via libkoiki/tasks/)]
  |
  (Uses Repository, Uses Schemas for internal data structure)
  V
[Repository Layer (Data Access in app/repositories/ or libkoiki/repositories/)]
  |  -------------------------------------------------------> [Configuration]
  |  -------------------------------------------------------> [Logging]
  |
  (Interacts with DB, Uses DB Models)
  V
[Database (e.g., PostgreSQL, managed by libkoiki/db/)]
  ^
  | (Celery Worker may access DB via Repository/Service)
  |
[Async Task Workers (Celery in libkoiki/tasks/)]
  |
  (Uses Message Broker)
  V
[Message Broker (e.g., Redis, for Celery and optionally Events)]

Associated Data Structures:
- DB Models (SQLAlchemy in libkoiki/models/, app/models/) - Used by Repository Layer
- Data Schemas (Pydantic in libkoiki/schemas/, app/schemas/) - Used by API and Service Layers

Note: In v0.6.0, most models and schemas are implemented in libkoiki/ for framework-level functionality, with app/ available for application-specific extensions.
```

-   **依存の方向**: 矢印は依存の方向を示します。例えば、APIレイヤーはサービスレイヤーに依存しますが、サービスレイヤーはAPIレイヤーを知りません。
-   **依存性注入 (DI)**: FastAPI の `Depends` 機能により、上位レイヤーは下位レイヤーの具体的な実装ではなく、抽象（または依存性解決関数）に依存します。
-   **コア機能**: 認証、設定、ロギング、モニタリングといった横断的な機能は、各レイヤーから必要に応じて利用されます。

---

## 03. ディレクトリ構成

本フレームワークは以下の2層に分かれた構成を推奨しています。

- `libkoiki/`: 共通的なフレームワークロジック（DI/認証/非同期/DB処理など、再利用可能なコンポーネント）
- `app/`: アプリケーション固有のルーティング・UI/API定義・ドメイン実装

```
プロジェクトルート/
├── app/                     # アプリケーション固有のコード
│   ├── __init__.py
│   ├── api/                 # アプリケーション固有のDIなど
│   │   └── dependencies.py
│   ├── models/              # アプリケーション固有のDBモデル (拡張用)
│   │   └── __init__.py
│   ├── repositories/        # アプリケーション固有のリポジトリ
│   │   └── __init__.py
│   ├── routers/             # アプリケーション固有のAPIルーター
│   │   └── __init__.py
│   ├── schemas/             # アプリケーション固有のPydanticスキーマ (拡張用)
│   │   └── __init__.py
│   ├── services/            # アプリケーション固有のサービス
│   │   └── __init__.py
│   └── main.py              # アプリケーションのエントリポイント
├── libkoiki/                # フレームワークコアライブラリ
│   ├── __init__.py
│   ├── api/                 # API共通コンポーネント
│   │   ├── __init__.py
│   │   └── v1/              # APIバージョン1
│   │       ├── __init__.py
│   │       └── endpoints/   # エンドポイント実装
│   │           ├── __init__.py
│   │           ├── auth.py           # 認証エンドポイント (統合)
│   │           ├── auth_basic.py     # 🆕 v0.6.0: 基本認証
│   │           ├── auth_password.py  # 🆕 v0.6.0: パスワード関連
│   │           ├── auth_token.py     # 🆕 v0.6.0: トークン関連
│   │           ├── security_monitor.py # 🆕 v0.6.0: セキュリティ監視
│   │           ├── todos.py          # 🆕 v0.6.0: ToDoエンドポイント
│   │           └── users.py          # ユーザーエンドポイント
│   ├── core/                # コアユーティリティ
│   │   ├── config.py        # 設定管理
│   │   ├── dependencies.py  # 共通DI
│   │   ├── error_handlers.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── monitoring.py
│   │   ├── rate_limiter.py  # レートリミット
│   │   ├── security.py      # JWT認証
│   │   └── transaction.py   # トランザクション管理
│   ├── db/                  # データベース関連
│   │   ├── base.py          # SQLAlchemy Base と共通モデル
│   │   └── session.py       # DBセッション管理
│   ├── models/              # 共通DBモデル (User, Role, Permission, 認証関連など)
│   │   ├── __init__.py
│   │   ├── associations.py
│   │   ├── login_attempt.py    # 🆕 v0.6.0: ログイン試行履歴
│   │   ├── password_reset.py   # 🆕 v0.6.0: パスワードリセット
│   │   ├── permission.py
│   │   ├── refresh_token.py    # 🆕 v0.6.0: リフレッシュトークン
│   │   ├── role.py
│   │   ├── todo.py             # 🆕 v0.6.0: ToDoモデル
│   │   └── user.py
│   ├── repositories/        # 共通リポジトリ (BaseRepository, UserRepositoryなど)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── login_attempt_repository.py    # 🆕 v0.6.0: ログイン試行リポジトリ
│   │   ├── password_reset_repository.py   # 🆕 v0.6.0: パスワードリセットリポジトリ
│   │   ├── refresh_token_repository.py    # 🆕 v0.6.0: リフレッシュトークンリポジトリ
│   │   ├── todo_repository.py             # 🆕 v0.6.0: ToDoリポジトリ
│   │   └── user_repository.py
│   ├── schemas/             # 共通Pydanticスキーマ (User, Token, 認証関連など)
│   │   ├── __init__.py
│   │   ├── auth.py             # 🆕 v0.6.0: 認証系スキーマ
│   │   ├── permission.py
│   │   ├── refresh_token.py    # 🆕 v0.6.0: リフレッシュトークン
│   │   ├── role.py
│   │   ├── todo.py             # 🆕 v0.6.0: ToDoスキーマ
│   │   ├── token.py
│   │   └── user.py
│   ├── services/            # 共通サービス (UserService, 認証関連など)
│   │   ├── __init__.py
│   │   ├── auth_service.py            # 🆕 v0.6.0: 認証サービス
│   │   ├── login_security_service.py  # 🆕 v0.6.0: ログインセキュリティサービス
│   │   ├── password_reset_service.py  # 🆕 v0.6.0: パスワードリセットサービス
│   │   ├── todo_service.py            # 🆕 v0.6.0: ToDoサービス
│   │   └── user_service.py
│   ├── tasks/               # Celeryタスク関連
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── email.py            # 🆕 v0.6.0: メール送信タスク
│   └── pyproject.toml       # libkoikiのパッケージ情報
├── alembic/                 # DBマイグレーションスクリプト
├── tests/                   # テストコード (unit, integration)
├── .env.example             # 環境変数サンプル
├── .github/                 # GitHub Actions設定
│   └── workflows/
│       └── ci.yml           # CIパイプライン定義
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### 3.1 libkoiki (フレームワークコア)
`libkoiki/` は、アプリケーション横断的に利用される共通機能や基盤部品を配置します。この部分は独立した Python ライブラリとして管理され、他のプロジェクトでも再利用できます。

- `libkoiki/core/`: 設定、ロギング、エラーハンドリング、ミドルウェア、トランザクション管理、認証など。
- `libkoiki/db/`: SQLAlchemyのベース設定、DBセッション管理。
- `libkoiki/models/`: 汎用的な User, Role, Permission, Todo, 認証関連 などのDBモデル。
- `libkoiki/schemas/`: User, Token, Todo, 認証関連 などの汎用的なPydanticスキーマ。
- `libkoiki/repositories/`: `BaseRepository` や `UserRepository`, 認証関連リポジトリ などの汎用リポジトリ。
- `libkoiki/services/`: `UserService`, `AuthService`, `TodoService` などの汎用サービス。
- `libkoiki/api/v1/endpoints/`: 認証（基本・パスワード・トークン）、Todo、ユーザー、セキュリティ監視などの共通エンドポイント実装。
- `libkoiki/tasks/`: Celeryの基本設定やメール送信などの共通タスク。

### 3.2 app (アプリケーション固有)
`app/` は、特定のビジネスドメインに特化したコードを配置します。v0.6.0では、基本的な機能（Todo、認証、ユーザー管理など）は`libkoiki/`で実装されており、`app/`は拡張やカスタマイズ用の構造を提供します。

- `app/main.py`: FastAPIアプリケーションインスタンスの生成、`libkoiki`の機能の組み込み、`app/`固有ルーターの登録など。
- `app/routers/`: アプリケーション固有のAPIエンドポイント定義。
- `app/services/`: アプリケーション固有のビジネスロジック。
- `app/repositories/`: アプリケーション固有のデータアクセスロジック。
- `app/models/`, `app/schemas/`: アプリケーション固有のデータ構造定義（現在v0.6.0では主に`libkoiki/`内で定義されているが、拡張用に構造を提供）。

**v0.6.0での実装状況:** 
- Todo機能、認証機能、ユーザー管理機能は`libkoiki/`内で完全に実装されている
- `app/`は将来的なビジネス固有の拡張やカスタマイズのための基盤を提供

この構成により、`libkoiki` を pip install 可能なフレームワークとして外部提供しながら、
`app/` 側では個別のユースケースやドメインに特化した開発を進めることができます。

---

## 04. 設定（Config）と依存性注入（DI）

この章では、アプリケーションを柔軟に構成する「設定管理」と、各処理で必要な機能を簡潔に使えるようにする「依存性注入（DI）」の仕組みについて説明します。

### 🔰 用語解説

- **設定（Config）**: アプリケーションを実行する際に、接続するデータベースや外部サービスの情報を `.env` ファイルなどから動的に読み込めるようにする仕組み。
- **依存性注入（DI: Dependency Injection）**: あるクラスや関数が必要とする機能（例：DB接続やサービス）を「外から渡す」ことで、再利用性とテストの容易さを高める設計手法。

### 4.1 設定管理 (config.py)

アプリケーションの設定は `pydantic` の `BaseSettings` を使用して管理します。環境変数や `.env` ファイルから値を読み込み、型検証も行います。

**`libkoiki/core/config.py` の実装例:**
```python
# libkoiki/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, PostgresDsn, validator
from typing import List, Optional, Union, Dict, Any

class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "KOIKI Framework"
    APP_ENV: str = "development"  # development, testing, production
    DEBUG: bool = True
    SERVER_NAME: str = "KOIKI Framework"
    SERVER_HOST: AnyHttpUrl = Field(default="http://localhost:8000")
    API_PREFIX: str = "/api/v1"

    # --- JWT ---
    JWT_SECRET: str = "jwt_secret_development_only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PROJECT_NAME: str = "KOIKI Framework"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # データベース接続プール設定
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # --- Redis ---
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    # --- レートリミット設定 ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "10/minute"
    RATE_LIMIT_STRATEGY: str = "fixed-window"
    RATE_LIMIT_PER_SECOND: int = 10

    # --- ログ設定 ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" または "console"

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        # PostgreSQLのURLを構築
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Redis URL がない場合は構築する
        if not self.REDIS_URL and self.REDIS_HOST:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

# グローバル設定オブジェクト
settings = Settings()
```

**環境設定の優先順位:**
1. OS環境変数
2. `.env` ファイル（`ENV_FILE`で指定されたもの、またはデフォルトの `.env`）
3. `Settings` クラスのフィールドで定義されたデフォルト値

**シークレット管理:**
`SECRET_KEY` や本番DBのパスワードなどの機密情報は、`.env` ファイルに直接記述せず、HashiCorp Vault, AWS Secrets Manager などのシークレット管理サービスや、CI/CDパイプラインの環境変数として管理することをお勧めします。

### 4.2 依存性注入 (dependencies.py)

FastAPI の `Depends` を活用し、コンポーネント間の依存関係を解決します。これにより、コードの再利用性やテスト容易性が向上します。

**`libkoiki/api/dependencies.py` の実装例:**
```python
# libkoiki/api/dependencies.py
from typing import Optional, Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from libkoiki.db.session import get_db as get_db_session
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.repositories.todo_repository import TodoRepository
from libkoiki.repositories.refresh_token_repository import RefreshTokenRepository
from libkoiki.repositories.password_reset_repository import PasswordResetRepository
from libkoiki.repositories.login_attempt_repository import LoginAttemptRepository
from libkoiki.services.user_service import UserService
from libkoiki.services.todo_service import TodoService
from libkoiki.services.auth_service import AuthService
from libkoiki.services.password_reset_service import PasswordResetService
from libkoiki.services.login_security_service import LoginSecurityService
from libkoiki.events.publisher import EventPublisher
from libkoiki.core.security import get_user_from_token as get_current_user_from_token
from libkoiki.models.user import UserModel
from libkoiki.core.config import settings
from libkoiki.core.logging import get_logger

logger = get_logger(__name__)

# --- 基本的な依存性 ---
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# --- Redis クライアント ---
async def get_redis_client(request: Request) -> Redis:
    """アプリケーション状態からRedisクライアントを取得"""
    if not hasattr(request.app.state, 'redis') or not request.app.state.redis:
        logger.error("Redis client requested but not available in app state.")
        raise HTTPException(status_code=503, detail="Redis connection not available")
    return request.app.state.redis

RedisClientDep = Annotated[Redis, Depends(get_redis_client)]

# --- サービス依存性 ---
async def get_user_service(db: DBSessionDep) -> UserService:
    repository = UserRepository()
    repository.set_session(db)
    return UserService(repository)

async def get_auth_service(db: DBSessionDep) -> AuthService:
    refresh_token_repo = RefreshTokenRepository()
    refresh_token_repo.set_session(db)
    return AuthService(refresh_token_repo)

async def get_login_security_service(db: DBSessionDep) -> LoginSecurityService:
    login_attempt_repo = LoginAttemptRepository()
    login_attempt_repo.set_session(db)
    return LoginSecurityService(login_attempt_repo)

# 依存性注入用のタイプエイリアス
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
LoginSecurityServiceDep = Annotated[LoginSecurityService, Depends(get_login_security_service)]

# --- 認証済みユーザー依存性 ---
async def get_current_user(db: DBSessionDep, token: str = Depends(oauth2_scheme)) -> UserModel:
    return await get_current_user_from_token(token=token, db=db)

async def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

ActiveUserDep = Annotated[UserModel, Depends(get_current_active_user)]

# 認証関連の依存性はsecurity.pyで定義されています
```

**`libkoiki/core/security.py` の認証関連依存性:**
```python
# libkoiki/core/security.py (一部抜粋)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from libkoiki.core.config import settings
from libkoiki.db.session import get_db
from libkoiki.models.user import UserModel

# OAuth2スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# JWT認証で現在のユーザーを取得
async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserModel:
    # 実装詳細は省略（8.1 JWT認証の実装を参照）
    ...

# 認証済みユーザーのみアクセス可能
async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user_from_token)]
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# 管理者ユーザーのみアクセス可能
async def get_current_active_superuser(
    current_user: Annotated[UserModel, Depends(get_current_active_user)]
) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# 依存性注入用のタイプエイリアス
CurrentUserDep = Annotated[UserModel, Depends(get_current_user_from_token)]
ActiveUserDep = Annotated[UserModel, Depends(get_current_active_user)]
SuperUserDep = Annotated[UserModel, Depends(get_current_active_superuser)]
```

**`libkoiki/core/rate_limiter.py` のレートリミット設定:**
```python
# libkoiki/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from libkoiki.core.config import settings

# レートリミッターのグローバルインスタンス
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    enabled=settings.RATE_LIMIT_ENABLED,
    strategy=settings.RATE_LIMIT_STRATEGY
)

# エンドポイントでの使用例:
# @router.post("/")
# @limiter.limit("5/minute")
# async def create_item(...):
#    ...
```

FastAPIのDIシステムは、エンドポイント関数のシグネチャで `Depends` を使用して依存性を宣言すると、FastAPIがその依存性（関数やクラス）を実行または解決し、結果をエンドポイント関数に注入します。これにより、各コンポーネントの疎結合が実現し、テストの容易性も向上します。

---

## 05. モデル & スキーマ層

ここでは、データベースとのやり取りを行う **モデル（Model）** と、クライアントとのデータ送受信を定義する **スキーマ（Schema）** について説明します。

### 🔰 用語解説

- **モデル（Model）**: Python で定義したクラスと、データベースのテーブル構造をマッピングする仕組みです（ORM: Object Relational Mapping）。FastAPI では SQLAlchemy を使用します。
- **スキーマ（Schema）**: API を通じてやり取りされるデータの形式を定義するもので、`pydantic` モデルを使って型チェック・バリデーションが行えます。

モデルは「保存形式」、スキーマは「通信形式」と捉えると理解しやすいです。

### 5.1 データベースモデル (SQLAlchemy)

SQLAlchemyのDeclarative Systemを使用してDBテーブルをPythonクラスとして定義します。
共通カラム（id, created_at, updated_at）を持つベースモデルを定義すると便利です。

**`libkoiki/db/base.py` (共通ベースモデル):**
```python
# libkoiki/db/base.py
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, func
from typing import Any

class CustomBase:
    @declared_attr
    def __tablename__(cls) -> str:
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower().replace("_model", "")

    id: Any = Column(Integer, primary_key=True, index=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

Base = declarative_base(cls=CustomBase)
```

**`libkoiki/models/user.py` (UserModel例):**
```python
# libkoiki/models/user.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base

# user_roles テーブルの関連付け（多対多）
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)

class UserModel(Base):
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # リレーション
    todos = relationship("TodoModel", back_populates="owner", cascade="all, delete-orphan")
    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")
    
    # v0.6.0で追加された認証関連リレーション
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetModel", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttemptModel", back_populates="user", cascade="all, delete-orphan")
```

**🆕 v0.6.0で追加された認証関連モデル:**

**`libkoiki/models/refresh_token.py` (リフレッシュトークン):**
```python
# libkoiki/models/refresh_token.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base

class RefreshTokenModel(Base):
    """リフレッシュトークンモデル"""
    __tablename__ = "refresh_tokens"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    device_info = Column(Text, nullable=True)  # JSON文字列として保存
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # リレーション
    user = relationship("UserModel", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        """トークンが期限切れかどうかを判定"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """トークンが有効かどうかを判定"""
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        """トークンを無効化"""
        self.is_revoked = True

    def update_last_used(self):
        """最終使用時刻を更新"""
        self.last_used_at = datetime.now(timezone.utc)
```

**`libkoiki/models/login_attempt.py` (ログイン試行記録):**
```python
# libkoiki/models/login_attempt.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from libkoiki.db.base import Base

class LoginAttemptModel(Base):
    """ログイン試行履歴モデル"""
    __tablename__ = "login_attempts"

    email = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)
    is_successful = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String(100), nullable=True)  # 失敗理由
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # リレーション
    user = relationship("UserModel", back_populates="login_attempts")

    @classmethod
    def get_lockout_window_start(cls, minutes: int = 15) -> datetime:
        """アカウントロックアウトの時間枠開始時刻を取得"""
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)

    def is_within_window(self, minutes: int = 15) -> bool:
        """指定した時間枠内の試行かどうかを確認"""
        window_start = self.get_lockout_window_start(minutes)
        return self.attempted_at >= window_start
```

**`libkoiki/models/password_reset.py` (パスワードリセット):**
```python
# libkoiki/models/password_reset.py
from datetime import datetime, timedelta
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base

class PasswordResetModel(Base):
    """パスワードリセットトークンモデル"""
    __tablename__ = "password_reset_tokens"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)

    # リレーション
    user = relationship("UserModel", back_populates="password_reset_tokens")

    @classmethod
    def create_token_expiry(cls, hours: int = 1) -> datetime:
        """トークンの有効期限を設定（デフォルト1時間）"""
        return datetime.utcnow() + timedelta(hours=hours)

    def is_expired(self) -> bool:
        """トークンが期限切れかどうかを確認"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """トークンが有効かどうかを確認"""
        return not self.is_used and not self.is_expired()
```

(RoleModel, PermissionModel, associations.py なども同様に `libkoiki/models/` に定義)

**注意:** 現在のv0.6.0では、`TodoModel`を含むすべてのモデルは`libkoiki/models/`内で定義されています。アプリケーション固有の拡張が必要な場合は`app/models/`に配置することも可能です。

### 5.2 APIスキーマ (Pydantic)

Pydanticモデルを使用してAPIのリクエスト/レスポンスのデータ構造とバリデーションルールを定義します。

**`libkoiki/schemas/user.py` (Userスキーマ例):**
```python
# libkoiki/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

# --- Request Schemas ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # パスワードポリシーはサービス層でも検証

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

# --- Response Schemas ---
class RoleResponseSimple(BaseModel): # UserResponse内で使用
     id: int
     name: str
     class Config:
         orm_mode = True

class UserResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    # roles: List[RoleResponseSimple] = [] # RBACを有効にする場合

    class Config:
        from_attributes = True # SQLAlchemyモデルからPydanticモデルへの変換を許可
```

**`libkoiki/schemas/token.py` (認証トークンスキーマ):**
```python
# libkoiki/schemas/token.py
from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    """アクセストークンとトークンタイプ"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")

class TokenWithRefresh(BaseModel):
    """🆕 v0.6.0: アクセストークンとリフレッシュトークンのペア"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

class TokenPayload(BaseModel):
    """JWTトークンのペイロード (内容)"""
    sub: Optional[str] = Field(None, description="Subject of the token (usually user ID)")
    exp: Optional[int] = Field(None, description="Expiration time (Unix timestamp)")
```

**🆕 v0.6.0で追加された認証関連スキーマ:**

**`libkoiki/schemas/auth.py` (認証スキーマ):**
```python
# libkoiki/schemas/auth.py
from pydantic import BaseModel, Field
from typing import Optional

class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 chars)")

class PasswordResetRequest(BaseModel):
    """パスワードリセット要求"""
    email: str = Field(..., description="Email address for password reset")

class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 chars)")

class AuthResponse(BaseModel):
    """認証系API共通レスポンス"""
    message: str = Field(..., description="Response message")
    user: Optional[dict] = Field(None, description="User information (if applicable)")
    data: Optional[dict] = Field(None, description="Additional response data")
```

**注意:** 現在のv0.6.0では、`TodoSchema`を含むすべてのスキーマは`libkoiki/schemas/`内で定義されています。アプリケーション固有の拡張が必要な場合は`app/schemas/`に配置することも可能です。

---

## 06. リポジトリ層

リポジトリ（Repository）層は、データベースアクセスの詳細を隠蔽し、サービス層からは「データ取得・保存」という操作として扱えるようにする役割を持ちます。

### 🔰 用語解説

- **リポジトリパターン**: データベースへのアクセス処理を専用クラスに切り出すことで、アプリのビジネスロジックを簡潔かつテストしやすく保つ設計パターン。
- たとえば「Todoを追加する」処理は、SQL を直接書くのではなく、`TodoRepository.create()` というメソッドを通じて呼び出します。

### 6.1 ベースリポジトリ
共通のCRUD操作を提供するジェネリックなベースリポジトリを定義します。

**`libkoiki/repositories/base.py` の実装例:**
```python
# libkoiki/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Sequence, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sql_delete, update as sql_update
from pydantic import BaseModel as PydanticBaseModel # SQLAlchemyのBaseと区別
from libkoiki.db.base import Base as DBBase # SQLAlchemyのORM Base

ModelType = TypeVar("ModelType", bound=DBBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
        self._db: Optional[AsyncSession] = None

    def set_session(self, db: AsyncSession):
        self._db = db

    @property
    def db(self) -> AsyncSession:
        if self._db is None:
            raise Exception(f"DB session not set for repository {self.__class__.__name__}")
        return self._db

    async def get(self, id: Any) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit).order_by(self.model.id)
        )
        return result.scalars().all()

    async def create(self, obj_in: ModelType) -> ModelType:
        self.db.add(obj_in)
        await self.db.flush()
        await self.db.refresh(obj_in)
        return obj_in

    async def update(
        self, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> Optional[ModelType]:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
        return obj
```
このベースリポジトリは、コンストラクタで操作対象のモデルクラスを受け取り、`set_session` メソッドで非同期DBセッションを設定します。サービス層のトランザクション管理と連携するために、外部からセッションを注入する設計になっています。

### 6.2 具体的なリポジトリ実装
ベースリポジトリを継承し、モデル固有のクエリメソッドなどを追加します。

**`libkoiki/repositories/user_repository.py` の実装例:**
```python
# libkoiki/repositories/user_repository.py
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from libkoiki.models.user import UserModel
from libkoiki.models.role import RoleModel
from libkoiki.repositories.base import BaseRepository
from libkoiki.schemas.user import UserCreate, UserUpdate # 直接は使わないことが多い

class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(UserModel)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    # RBAC使用時など、リレーションをロードするメソッド
    async def get_user_with_roles_permissions(self, user_id: int) -> Optional[UserModel]:
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.roles).selectinload(RoleModel.permissions)
            )
            .where(UserModel.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```
アプリケーション固有のリポジトリ (例: `TodoRepository`) は `app/repositories/` に配置します。

---

## 07. サービス層

サービス層は、ビジネスロジック（＝「どう処理すべきか」というルール）をまとめる場所です。

### 🔰 用語解説

- **サービス（Service）**: アプリケーションが提供する機能をまとめたクラスや関数群です。コントローラー（API層）とデータ層（リポジトリ）との仲介役を果たします。
- たとえば「Todo を更新する」処理では、まずデータを取得し、必要な変更を加え、再保存するという一連の流れをこのサービス層で処理します。

この層を設けることで、APIルーティングやUIからの呼び出しが非常にシンプルになります。

### 7.1 サービスクラスの実装
サービスクラスは、コンストラクタで必要なリポジトリや他のサービスを受け取り（DI経由）、ビジネスロジックを実行するメソッドを提供します。

**`libkoiki/services/user_service.py` の実装例:**
```python
# libkoiki/services/user_service.py
from typing import Optional, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from libkoiki.repositories.user_repository import UserRepository
from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate, UserUpdate
from libkoiki.core.security import get_password_hash, verify_password, check_password_complexity
# from libkoiki.events.publisher import EventPublisher # イベントシステムを使う場合
from libkoiki.core.exceptions import ValidationException, ResourceNotFoundException
from libkoiki.core.transaction import transactional # トランザクションデコレータ

logger = structlog.get_logger(__name__)

class UserService:
    def __init__(self, repository: UserRepository): # event_publisher: Optional[EventPublisher] = None):
        self.repository = repository
        # self.event_publisher = event_publisher

    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> Optional[UserModel]:
        self.repository.set_session(db)
        user = await self.repository.get(user_id)
        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)
        return user

    async def get_user_by_email(self, email: str, db: AsyncSession) -> Optional[UserModel]:
        self.repository.set_session(db)
        return await self.repository.get_by_email(email)

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[UserModel]:
        self.repository.set_session(db)
        return await self.repository.get_multi(skip=skip, limit=limit)

    @transactional # トランザクション管理
    async def create_user(self, user_in: UserCreate, db: AsyncSession) -> UserModel:
        self.repository.set_session(db)
        if await self.repository.get_by_email(user_in.email):
            raise ValidationException("このメールアドレスは既に使用されています")

        if not check_password_complexity(user_in.password): # パスワードポリシーチェック
            raise ValidationException(
                "パスワードは8文字以上で、大文字、小文字、数字、記号を各1つ以上含めてください。"
            )

        hashed_password = get_password_hash(user_in.password)
        # Pydanticモデルの dict() は便利だが、DBモデルに直接渡せるフィールドのみにする
        user_model_data = user_in.dict(exclude={"password"}, exclude_unset=True)
        user_model_data["hashed_password"] = hashed_password
        
        user = UserModel(**user_model_data)
        created_user = await self.repository.create(user)

        logger.info("User created successfully", user_id=created_user.id, email=created_user.email)
        # if self.event_publisher:
        #     await self.event_publisher.publish("user_created", {"user_id": created_user.id, "email": created_user.email})
        return created_user

    @transactional
    async def update_user(self, user_id: int, user_in: UserUpdate, db: AsyncSession) -> UserModel:
        self.repository.set_session(db)
        user = await self.repository.get(user_id)
        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)

        update_data = user_in.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            if not check_password_complexity(update_data["password"]):
                 raise ValidationException("パスワードは8文字以上で、大文字、小文字、数字、記号を各1つ以上含めてください。")
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        elif "password" in update_data: # passwordが空文字やNoneの場合
             del update_data["password"]

        if "email" in update_data and update_data["email"] != user.email:
             existing_user = await self.repository.get_by_email(update_data["email"])
             if existing_user and existing_user.id != user_id:
                 raise ValidationException("このメールアドレスは既に使用されています")

        updated_user = await self.repository.update(user, update_data)
        logger.info("User updated", user_id=updated_user.id)
        # if self.event_publisher:
        # await self.event_publisher.publish("user_updated", {"user_id": updated_user.id})
        return updated_user

    @transactional
    async def delete_user(self, user_id: int, db: AsyncSession) -> Optional[UserModel]:
        self.repository.set_session(db)
        user = await self.repository.get(user_id)
        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)
        # 物理削除か論理削除かはリポジトリ層またはここで制御
        deleted_user = await self.repository.delete(user_id) # deleteがオブジェクトを返す場合
        logger.info("User deleted", user_id=user_id)
        return deleted_user

    async def authenticate_user(self, email: str, password: str, db: AsyncSession) -> Optional[UserModel]:
        self.repository.set_session(db)
        user = await self.repository.get_by_email(email)
        if not user:
            logger.warning("Authentication failed: user not found", email=email)
            return None
        if not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed: invalid password", email=email)
            return None
        return user
```

### 7.2 トランザクション管理
複数のDB操作を伴うビジネスロジックでは、処理の原子性を保証するためにトランザクション管理が不可欠です。
`@transactional` デコレータをサービスメソッドに適用することで、メソッド全体を一つのトランザクションスコープで実行します。

**`libkoiki/core/transaction.py` の実装例:**
```python
# libkoiki/core/transaction.py
import functools
from typing import Callable, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

# from libkoiki.db.session import get_db_session # DBセッション取得関数を直接使わない
logger = structlog.get_logger(__name__)

def transactional(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # デコレータが適用されたメソッドの最後の引数が AsyncSession であることを期待
        # 例: async def my_method(self, ..., db: AsyncSession):
        db: Optional[AsyncSession] = None
        # argsの最後がAsyncSessionか、kwargsにdbがあるかチェック
        if args and isinstance(args[-1], AsyncSession):
            db = args[-1]
        elif "db" in kwargs and isinstance(kwargs["db"], AsyncSession):
            db = kwargs["db"]
        
        if db is None:
            # 通常、サービスメソッドはFastAPIのDIからdbセッションを注入される
            # このデコレータはそのセッションをトランザクション管理に使う
            raise ValueError(
                f"Transactional method {func.__name__} must receive an AsyncSession "
                "instance as its last positional argument or as a 'db' keyword argument."
            )

        # 既にトランザクションが開始されているか確認 (ネストトランザクションは begin_nested() が必要)
        # ここでは単純なトップレベルトランザクションを想定
        if db.in_transaction():
            # ネストされた呼び出しの場合、何もしないでそのまま実行
            logger.debug(f"Joining existing transaction for {func.__name__}")
            return await func(*args, **kwargs)

        # 新しいトランザクションを開始
        async with db.begin(): # begin() で自動的に commit/rollback
            logger.debug(f"Starting transaction for {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                # await db.commit() # async with db.begin() が自動で行う
                logger.debug(f"Transaction for {func.__name__} will be committed.")
                return result
            except Exception as e:
                logger.error(f"Transaction failed for {func.__name__}, will be rolled back. Error: {e}", exc_info=True)
                # await db.rollback() # async with db.begin() が自動で行う
                raise
    return wrapper
```
**使用方法:**
サービスメソッドの最後の引数として `db: AsyncSession` を受け取り、そのメソッドに `@transactional` デコレータを付けます。
メソッド内でリポジトリを使用する際は、`repository.set_session(db)` を呼び出して現在のトランザクションスコープのセッションをリポジトリに渡します。

---

## 08. 認証・認可（JWT）

アプリケーションを利用するユーザーが「誰であるか」を確認し、そのユーザーが「何をしてよいか」を制御するための仕組みが **認証・認可** です。

### 🔰 用語解説

- **JWT（JSON Web Token）**: ユーザーの情報を暗号化して保持するトークン形式。これをAPIリクエストに含めることで、ユーザーを識別できます。
- **アクセストークン**: 一定時間有効な「ログイン証明書」のようなものです。トークンがある間、ログイン状態としてAPIにアクセスできます。
- **RBAC (Role-Based Access Control)**: ロール（役割）に基づいてユーザーの権限を管理する仕組み。

### 8.1 JWT認証の実装
`python-jose` と `passlib[bcrypt]` を使用してJWTの生成・検証とパスワードハッシュ化を行います。

**`libkoiki/core/security.py` の実装例:**
```python
# libkoiki/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog
import secrets
import hashlib

from libkoiki.core.config import settings
from libkoiki.schemas.token import TokenPayload
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.models.user import UserModel
from libkoiki.models.role import RoleModel
from libkoiki.models.permission import PermissionModel

logger = structlog.get_logger(__name__)

# --- パスワードハッシュ化 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 スキーマ ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# --- トークン生成 ---
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    新しいアクセストークンを生成します。

    Args:
        subject: トークンの主体 (通常はユーザーID)。
        expires_delta: トークンの有効期間。None の場合は設定値を使用。

    Returns:
        生成されたJWTトークン文字列。
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}  # subject は文字列に変換
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    logger.debug("Access token created", subject=subject, expires_at=expire.isoformat())
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化パスワードを比較して一致するか検証します"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化します"""
    return pwd_context.hash(password)

# パスワード複雑性チェック
import re
def check_password_complexity(password: str) -> bool:
    """パスワードが複雑性要件を満たしているか検証します"""
    if len(password) < 8: return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True

async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserModel:
    """
    JWTトークンを検証し、対応するユーザー情報をDBから取得します。
    ロールと権限も Eager Loading します。
    DBセッションは呼び出し元 (e.g., dependencies.py) で提供される必要があります。
    
    Args:
        token: Bearer トークン
        db: DBセッション
    
    Returns:
        認証済みUserModelインスタンス
        
    Raises:
        HTTPException: トークンが無効か期限切れの場合
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload) # ペイロードをスキーマで検証
        
        # 有効期限チェック
        if token_data.exp is None or datetime.fromtimestamp(token_data.exp, timezone.utc) < datetime.now(timezone.utc):
             logger.warning("Token expired", user_id=token_data.sub, exp=token_data.exp)
             raise credentials_exception
        
        # サブジェクト (ユーザーID) チェック
        if token_data.sub is None:
            logger.warning("Token subject (user ID) is missing")
            raise credentials_exception
        
        user_id = int(token_data.sub) # IDを整数に変換
        logger.debug("Token decoded successfully", user_id=user_id)

    except (JWTError, ValidationError) as e:
        logger.warning(f"Token validation failed: {e}", token=token[:10]+"...") # トークンの一部だけログに
        raise credentials_exception
    
    # リポジトリを使ってユーザーをロールと権限情報も含めて取得
    user_repo = UserRepository()
    user_repo.set_session(db) # 渡された db セッションを使用
    user = await user_repo.get_user_with_roles_permissions(user_id)

    if user is None:
        logger.warning("User specified in token not found in DB", user_id=user_id)
        raise credentials_exception
    
    return user

# 認証済みユーザーのみアクセス可能
async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user_from_token)]
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# 管理者ユーザーのみアクセス可能
async def get_current_active_superuser(
    current_user: Annotated[UserModel, Depends(get_current_active_user)]
) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# 依存性注入用のタイプエイリアス
CurrentUserDep = Annotated[UserModel, Depends(get_current_user_from_token)]
ActiveUserDep = Annotated[UserModel, Depends(get_current_active_user)]
SuperUserDep = Annotated[UserModel, Depends(get_current_active_superuser)]
```

### 8.2 認証APIエンドポイント
v0.6.0では、認証APIが機能別に分割されています：

**`libkoiki/api/v1/endpoints/auth.py` - 統合ルーター:**
```python
# libkoiki/api/v1/endpoints/auth.py
"""
認証系APIの統合ルーター

機能別に分割されたエンドポイントを統合します：
- auth_basic: ログイン、登録、ログアウト、現在ユーザー取得
- auth_password: パスワード変更、パスワードリセット
- auth_token: トークンリフレッシュ、全トークン無効化
"""
from fastapi import APIRouter

from . import auth_basic, auth_password, auth_token

router = APIRouter()

# 基本認証機能
router.include_router(auth_basic.router, tags=["Authentication - Basic"])

# パスワード管理機能  
router.include_router(auth_password.router, tags=["Authentication - Password"])

# トークン管理機能
router.include_router(auth_token.router, tags=["Authentication - Token"])
```

**`libkoiki/api/v1/endpoints/auth_basic.py` - 基本認証機能:**
```python
# libkoiki/api/v1/endpoints/auth_basic.py
from typing import Annotated
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from libkoiki.api.dependencies import (
    ActiveUserDep,
    AuthServiceDep,
    DBSessionDep,
    LoginSecurityServiceDep,
    UserServiceDep,
)
from libkoiki.core.auth_decorators import handle_auth_errors
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.security import extract_device_info
from libkoiki.schemas.token import TokenWithRefresh
from libkoiki.schemas.user import UserCreate, UserResponse

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
@handle_auth_errors("login")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    login_security_service: LoginSecurityServiceDep,
    db: DBSessionDep,
) -> TokenWithRefresh:
    """
    OAuth2互換のトークンエンドポイント。
    メールアドレスとパスワードで認証し、アクセストークンとリフレッシュトークンを返します。

    - **username**: ユーザーのメールアドレス
    - **password**: ユーザーのパスワード
    """
    email = form_data.username
    ip_address = request.client.host if request.client else "unknown"
    device_info = extract_device_info(request)

    # ログイン試行制限チェック
    can_attempt = await login_security_service.can_attempt_login(
        email=email, ip_address=ip_address, db=db
    )
    if not can_attempt:
        logger.warning("Login blocked due to too many attempts", email=email, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # ユーザー認証
    user = await user_service.authenticate_user(
        email=email, password=form_data.password, db=db
    )
    
    if not user:
        # 失敗を記録
        await login_security_service.record_failed_attempt(
            email=email, ip_address=ip_address, db=db
        )
        logger.warning("Login failed: invalid credentials", email=email, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        await login_security_service.record_failed_attempt(
            email=email, ip_address=ip_address, db=db
        )
        logger.warning("Login attempt with inactive account", email=email, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )

    # トークンペア生成
    tokens = await auth_service.create_tokens_for_user(
        user=user, device_info=device_info, db=db
    )
    
    # 成功を記録
    await login_security_service.record_successful_attempt(
        email=email, ip_address=ip_address, user_id=user.id, db=db
    )
    
    logger.info("User logged in successfully", user_id=user.id, email=user.email)
    return tokens
```

### 8.3 ロールベースアクセス制御 (RBAC)
ユーザーにロールを割り当て、ロールに権限を紐付けることでアクセス制御を行います。
詳細は [15. ロールと権限](#15-ロールと権限) を参照。

### 8.4 🆕 認証系API拡張機能 (v0.6.0新機能)

**v0.6.0では、エンタープライズ環境で求められる包括的な認証システムを実装しました。**

#### 8.4.1 リフレッシュトークン機能

**長期間ログイン状態を維持しつつ、セキュリティを確保するための機能です。**

- **アクセストークン**: 短期間（15分～1時間）有効、API呼び出しに使用
- **リフレッシュトークン**: 長期間（7日～30日）有効、アクセストークンの更新に使用
- **自動更新**: アクセストークン期限切れ時に自動でトークンペアを更新

```python
# リフレッシュトークン例
@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """リフレッシュトークンを使用してアクセストークンを更新"""
    # 実装詳細は docs/authentication-api-guide.md を参照
    pass
```

#### 8.4.2 パスワードリセット機能

**パスワードを忘れたユーザーのためのセキュアなリセット機能です。**

- **メール送信**: パスワードリセット用の一時トークンをメール送信
- **トークン検証**: 一時トークンの有効性と期限を検証
- **新パスワード設定**: 安全にパスワードを変更

```python
# パスワードリセット例
@router.post("/password-reset/request")
async def request_password_reset(email: str):
    """パスワードリセットリクエスト"""
    # メール送信とトークン生成
    pass

@router.post("/password-reset/confirm")
async def confirm_password_reset(token: str, new_password: str):
    """パスワードリセット実行"""
    # トークン検証と新パスワード設定
    pass
```

#### 8.4.3 ログイン試行制限

**ブルートフォース攻撃を防ぐためのセキュリティ機能です。**

- **試行回数制限**: IPアドレスまたはユーザー単位での試行回数制限
- **一時ロック**: 規定回数失敗後の一時的なアカウントロック
- **段階的制限**: 失敗回数に応じた待機時間の増加

```python
# ログイン試行制限例
async def check_login_attempts(
    ip_address: str, 
    email: str, 
    db: AsyncSession
) -> bool:
    """ログイン試行制限チェック"""
    # IP単位とユーザー単位の制限確認
    # 詳細は libkoiki/services/auth_security_service.py を参照
    pass
```

### 8.5 🆕 セキュリティ監査API (v0.6.0新機能)

**認証関連のセキュリティイベントを監視・記録する機能です。**

#### 8.5.1 認証ログ記録

- **ログイン成功/失敗**: すべてのログイン試行を記録
- **トークン操作**: トークン発行、更新、無効化を記録
- **セキュリティイベント**: 不審なアクセス試行を記録

#### 8.5.2 監査レポート

- **ログイン履歴**: ユーザー別、期間別のログイン履歴
- **セキュリティアラート**: 不審な活動の自動検出とアラート
- **アクセス分析**: IPアドレス、ユーザーエージェント等の分析

```python
# 監査ログ例
await audit_service.log_authentication_event(
    user_id=user.id,
    event_type="login_success",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    additional_info={"method": "password"}
)
```

#### 8.5.3 関連ドキュメント

**v0.6.0では、認証系APIの詳細なドキュメントを整備しました：**

- **[認証系API完全ガイド](docs/authentication-api-guide.md)**: 認証システムの詳細な実装ガイド
- **[セキュリティ強化対応記録](docs/authentication-api-security-fixes.md)**: セキュリティ改善の記録と対応履歴  
- **[認証系APIテストガイド](認証系APIテストガイド.md)**: 認証システムのテスト方法とベストプラクティス

---

## 09. 非同期処理（Celery & Redis）

非同期処理とは、「ユーザーの待ち時間を減らす」ために、重い処理を裏で行う仕組みです。

### 🔰 用語解説

- **非同期処理**: ユーザーが待たずに操作できるように、裏側で別スレッドやプロセスで処理を実行する仕組み。Webアプリケーションでは、メール送信やレポート生成などに使用。
- **Celery**: Pythonで定番の非同期タスクキューライブラリ。
- **Redis**: Celeryと連携し、タスクの待ち行列を管理する役割を担う高速なインメモリデータストア。

### 9.1 Celeryによる非同期タスク
時間のかかる処理（メール送信、レポート生成など）をバックグラウンドで実行します。

**`libkoiki/tasks/celery_app.py`:**
```python
# libkoiki/tasks/celery_app.py
from celery import Celery
from libkoiki.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

celery_app = None
if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    celery_app = Celery(
        "worker", # Celeryアプリケーション名
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    # Autodiscover tasks from installed apps (libkoiki.tasks, app.tasks)
    # For this to work, tasks modules should be importable.
    # The list should contain paths to modules where tasks are defined.
    celery_app.autodiscover_tasks(lambda: ['libkoiki.tasks', 'app.tasks']) # app側のタスクも探索

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=getattr(settings, 'TIMEZONE', "UTC"), # settingsにTIMEZONEがあれば使用
        enable_utc=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True, # メッセージのACKをタスク完了後にする
    )
    
    logger.info("Celery application initialized successfully")
else:
    logger.warning("Celery broker or backend URL not configured. Celery tasks disabled.")

# @celery_app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(10.0, some_task.s('hello'), name='add every 10')
```

**`libkoiki/tasks/example_task.py` (共通タスク例):**
```python
# libkoiki/tasks/example_task.py
from libkoiki.tasks.celery_app import celery_app # celery_appインスタンスをインポート
import structlog

logger = structlog.get_logger(__name__)

if celery_app: # celery_appがNoneでないことを確認
    @celery_app.task(name="libkoiki.tasks.add") # タスク名を明示的に指定すると良い
    def add(x: int, y: int) -> int:
        logger.info(f"Task 'add' called with x={x}, y={y}")
        return x + y

    @celery_app.task(name="libkoiki.tasks.send_email_example")
    def send_email_example(to_email: str, subject: str, body: str):
        logger.info(f"Simulating email send to {to_email} with subject '{subject}'")
        # 実際のメール送信ロジック (例: smtplib や外部メールサービスAPI)
        import time
        time.sleep(5) # メール送信にかかる時間をシミュレート
        logger.info(f"Email to {to_email} sent successfully.")
        return {"status": "success", "to_email": to_email}
else:
    # Celeryが無効な場合のフォールバックや警告
    def add(x: int, y: int) -> int:
        logger.warning("Celery is not configured. Task 'add' is running synchronously.")
        return x + y
    def send_email_example(to_email: str, subject: str, body: str):
        logger.warning("Celery is not configured. Task 'send_email_example' is running synchronously.")
        # 同期的に実行する簡易版
        logger.info(f"Simulating synchronous email send to {to_email}")
        return {"status": "success", "to_email": to_email, "mode": "synchronous"}
```
アプリケーション固有のタスクは `app/tasks/` に配置します。
`app/tasks/__init__.py` を作成し、`app.tasks.your_task_module` のようにCeleryが検出できるようにします。

### 9.2 イベントシステム (オプション)
Redis Pub/Sub を利用したシンプルなイベント駆動アーキテクチャを構築することも可能です。
サービス層でビジネスイベントを発行し、別のコンポーネント（イベントハンドラ）がそれを購読して非同期に処理します。
v0.3.0 の `libkoiki/events/` ディレクトリの実装 (EventPublisher, EventHandler) などを参考に導入できます。

### 9.3 Celeryの本番運用に関する考慮事項
- **リトライ戦略**: タスク失敗時の自動リトライ（`autoretry_for`, `retry_kwargs`, `max_retries`など）。
- **監視**: Flowerなどのツールでタスクの実行状況、キューの長さを監視。Prometheusと連携してメトリクス収集。
- **ワーカ管理**: SupervisorやSystemdでワーカプロセスをデーモン化し、自動再起動を設定。負荷に応じたワーカ数の調整（スケーリング）。
- **デッドレターキュー**: 処理に失敗し続けるタスクを隔離する仕組み。
- **冪等性**: タスクが複数回実行されても問題ないように設計（特にリトライ時）。
- **タスクの分割**: 長時間実行されるタスクは、小さなサブタスクに分割することを検討。
- **結果バックエンド**: 結果が不要なタスクではバックエンド設定を省略してパフォーマンス向上。必要な場合でも、結果のTTLを設定してRedisのメモリ使用量を抑える。

---

## 10. アプリケーション実装例と起動方法 (app/)

このセクションでは、`libkoiki` フレームワークを利用して、具体的なアプリケーション (`app/` ディレクトリ以下) をどのように構築するかの例として、シンプルなToDo管理アプリを示します。

### 10.1 app/main.py
アプリケーションのエントリポイント。FastAPIインスタンスの初期化、ミドルウェアの設定、ルーターの登録などを行います。

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler # slowapi のデフォルトハンドラ
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as aioredis # redis.asyncio をインポート
import structlog

from libkoiki.core.config import settings
from libkoiki.core.logging import setup_logging, get_logger
from libkoiki.core.error_handlers import setup_exception_handlers
from libkoiki.db.session import connect_db, disconnect_db
from libkoiki.core.rate_limiter import limiter
# from libkoiki.core.monitoring import setup_monitoring # Prometheus使う場合
# from libkoiki.core.middleware import SecurityHeadersMiddleware, AuditLogMiddleware # 必要なら

# アプリケーション固有のルーターをインポート
from app.routers import todo_router # ToDoルーター

logger = get_logger(__name__) # ロガーを取得

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- アプリケーション起動時 ---
    setup_logging(
        log_level_str=settings.LOG_LEVEL,
        app_env=settings.APP_ENV,
        debug=settings.DEBUG
    )
    logger.info(f"Starting application: {settings.APP_NAME} in {settings.APP_ENV} mode")

    await connect_db() # DB接続確認

    # Redisクライアント初期化 (レートリミット、キャッシュ、Pub/Sub用)
    if settings.REDIS_URL:
        try:
            # aioredis.from_url は aioredis.Redis.from_url に変更されている場合がある
            app.state.redis = aioredis.Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await app.state.redis.ping() # 接続確認
            logger.info("Redis connection successful.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}", exc_info=True)
            app.state.redis = None # 失敗した場合はNoneに設定
    else:
        app.state.redis = None
        logger.warning("Redis URL not configured. Redis client not initialized.")

    # レートリミッターをアプリケーション状態に設定
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # slowapiデフォルトハンドラ
    # グローバルにミドルウェアとして適用する場合
    # app.add_middleware(SlowAPIMiddleware)
    logger.info(f"Rate limiter initialized (Strategy: {limiter.strategy}).")

    # setup_monitoring(app) # Prometheusメトリクス設定 (有効にする場合)

    yield # アプリケーション実行

    # --- アプリケーション終了時 ---
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed.")
    await disconnect_db()
    logger.info("Application shutdown.")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan # lifespanコンテキストマネージャを登録
)

# グローバル例外ハンドラー設定
setup_exception_handlers(app)

# ミドルウェア設定
# from libkoiki.core.middleware import AuditLogMiddleware, SecurityHeadersMiddleware # インポート
# app.add_middleware(AuditLogMiddleware) # 監査ログ (DBアクセスに注意)
# app.add_middleware(SecurityHeadersMiddleware) # セキュリティヘッダ
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS], # 文字列リストに
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーター登録
# 認証ルーターは libkoiki に含まれるものを使用
from libkoiki.api.v1.endpoints import auth
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"]) 

# アプリケーション固有のルーター
app.include_router(todo_router.router, prefix=f"{settings.API_PREFIX}/todos", tags=["Todos"]) 

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "Application is healthy"}

# Celeryを使う場合、celery_appをFastAPIインスタンスから参照できるようにする (オプション)
from libkoiki.tasks.celery_app import celery_app
app.state.celery_app = celery_app

# if __name__ == "__main__":
# import uvicorn
# uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 10.2 app/routers/todo_router.py
ToDo APIのエンドポイントを定義します。`libkoiki` の共通依存性や `app` 固有の依存性を使用します。

```python
# app/routers/todo_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
import structlog

from libkoiki.core.dependencies import DBSessionDep
from libkoiki.core.security import ActiveUserDep # 認証済みユーザー
from libkoiki.models.user import UserModel # UserModelをインポート

from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema, TodoResponseSchema
from app.services.todo_service import TodoService # アプリケーション固有のサービス
from app.api.dependencies import get_todo_service # アプリケーション固有のDI

logger = structlog.get_logger(__name__)
router = APIRouter()
TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]

@router.post("/", response_model=TodoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_todo_endpoint(
    todo_in: TodoCreateSchema,
    db: DBSessionDep,
    todo_service: TodoServiceDep,
    current_user: ActiveUserDep, # 認証済みユーザーのみ作成可能
):
    """新しいToDoを作成します。認証が必要です。"""
    logger.info("Creating new todo", user_id=current_user.id)
    return await todo_service.create_todo(todo_data=todo_in, db=db, owner_id=current_user.id)

@router.get("/", response_model=List[TodoResponseSchema])
async def get_todos_endpoint(
    db: DBSessionDep,
    todo_service: TodoServiceDep,
    current_user: ActiveUserDep, # 自分のToDoのみ取得
    skip: int = 0,
    limit: int = 100,
):
    """認証ユーザーのToDo一覧を取得します。"""
    logger.debug("Fetching todos for user", user_id=current_user.id, skip=skip, limit=limit)
    return await todo_service.get_todos_by_owner(owner_id=current_user.id, db=db, skip=skip, limit=limit)

@router.get("/{todo_id}", response_model=TodoResponseSchema)
async def get_todo_by_id_endpoint(
    todo_id: int,
    db: DBSessionDep,
    todo_service: TodoServiceDep,
    current_user: ActiveUserDep,
):
    """指定されたIDのToDoを取得します。認証ユーザーのToDoである必要があります。"""
    todo = await todo_service.get_todo_by_id_and_owner(todo_id=todo_id, owner_id=current_user.id, db=db)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found or not authorized")
    return todo

@router.put("/{todo_id}", response_model=TodoResponseSchema)
async def update_todo_endpoint(
    todo_id: int,
    todo_in: TodoUpdateSchema,
    db: DBSessionDep,
    todo_service: TodoServiceDep,
    current_user: ActiveUserDep,
):
    """指定されたIDのToDoを更新します。認証ユーザーのToDoである必要があります。"""
    updated_todo = await todo_service.update_todo(
        todo_id=todo_id, todo_data=todo_in, db=db, owner_id=current_user.id
    )
    if not updated_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found or not authorized")
    return updated_todo

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_endpoint(
    todo_id: int,
    db: DBSessionDep,
    todo_service: TodoServiceDep,
    current_user: ActiveUserDep,
):
    """指定されたIDのToDoを削除します。認証ユーザーのToDoである必要があります。"""
    deleted = await todo_service.delete_todo(todo_id=todo_id, db=db, owner_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found or not authorized")
    return None # No content
```

### 10.3 app/services/todo_service.py
ToDoに関連するビジネスロジックを実装します。`libkoiki`のトランザクションデコレータなどを使用できます。

```python
# app/services/todo_service.py
from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from libkoiki.core.transaction import transactional
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException # 使用する場合はインポート
from app.repositories.todo_repository import TodoRepository
from app.models.todo_model import TodoModel
from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema

logger = structlog.get_logger(__name__)

class TodoService:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    @transactional
    async def create_todo(self, todo_data: TodoCreateSchema, db: AsyncSession, owner_id: int) -> TodoModel:
        self.repository.set_session(db)
        # owner_idをTodoModelのコンストラクタに渡す
        todo = TodoModel(**todo_data.dict(), owner_id=owner_id)
        created_todo = await self.repository.create(todo)
        logger.info("Todo created", todo_id=created_todo.id, owner_id=owner_id)
        return created_todo

    async def get_todos_by_owner(
        self, owner_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[TodoModel]:
        self.repository.set_session(db)
        return await self.repository.get_multi_by_owner(owner_id=owner_id, skip=skip, limit=limit)

    async def get_todo_by_id_and_owner(
        self, todo_id: int, owner_id: int, db: AsyncSession
    ) -> Optional[TodoModel]:
        self.repository.set_session(db)
        todo = await self.repository.get(todo_id)
        if not todo:
            logger.warning("Todo not found", todo_id=todo_id)
            return None # ルーターで404処理
        if todo.owner_id != owner_id:
            logger.warning("Todo access denied - ownership mismatch", todo_id=todo_id, requested_by=owner_id, owner_id=todo.owner_id)
            return None # ルーターで404または403処理
        return todo

    @transactional
    async def update_todo(
        self, todo_id: int, todo_data: TodoUpdateSchema, db: AsyncSession, owner_id: int
    ) -> Optional[TodoModel]:
        self.repository.set_session(db)
        todo = await self.repository.get(todo_id) # まず取得
        if not todo:
            logger.warning("Todo not found for update", todo_id=todo_id)
            return None
        if todo.owner_id != owner_id: # 所有者チェック
            logger.warning("Todo update denied - ownership mismatch", todo_id=todo_id, requested_by=owner_id, owner_id=todo.owner_id)
            return None # Not authorized
        
        update_data = todo_data.dict(exclude_unset=True)
        updated_todo = await self.repository.update(todo, update_data) # 取得したオブジェクトを更新
        logger.info("Todo updated", todo_id=todo_id, owner_id=owner_id)
        return updated_todo

    @transactional
    async def delete_todo(self, todo_id: int, db: AsyncSession, owner_id: int) -> bool:
        self.repository.set_session(db)
        todo = await self.repository.get(todo_id) # まず取得
        if not todo:
            logger.warning("Todo not found for deletion", todo_id=todo_id)
            return False
        if todo.owner_id != owner_id: # 所有者チェック
            logger.warning("Todo deletion denied - ownership mismatch", todo_id=todo_id, requested_by=owner_id, owner_id=todo.owner_id)
            return False # Not authorized
        
        await self.repository.delete(todo_id) # IDで削除 (deleteメソッドの実装による)
        logger.info("Todo deleted", todo_id=todo_id, owner_id=owner_id)
        return True
```

### 10.4 app/repositories/todo_repository.py
ToDoモデル固有のデータアクセス処理を実装します。`libkoiki`の`BaseRepository`を継承できます。

```python
# app/repositories/todo_repository.py
from typing import Optional, Sequence
from sqlalchemy.future import select

from libkoiki.repositories.base import BaseRepository
from app.models.todo_model import TodoModel
from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema # スキーマは直接使わないことが多い

class TodoRepository(BaseRepository[TodoModel, TodoCreateSchema, TodoUpdateSchema]):
    def __init__(self):
        super().__init__(TodoModel) # 操作対象のモデルを渡す

    async def get_multi_by_owner(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[TodoModel]:
        """指定されたowner_idを持つToDoを複数取得します。"""
        result = await self.db.execute(
            select(self.model) # self.model (TodoModel) を使用
            .where(self.model.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.id) # 例: IDでソート
        )
        return result.scalars().all()
```

### 10.5 libkoiki/models/todo.py
ToDoのデータベースモデルは`libkoiki`フレームワーク内で定義されています。

```python
# libkoiki/models/todo.py
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base
from libkoiki.models.user import UserModel

class TodoModel(Base):
    __tablename__ = 'todos'

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False, server_default='false')

    # 所有者 (User) への外部キー
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Userモデルとのリレーション
    owner: UserModel = relationship("UserModel", back_populates="todos")

    def __repr__(self):
        status = "Completed" if self.is_completed else "Pending"
        return f"<Todo(id={self.id}, title='{self.title[:20]}...', status='{status}', owner_id={self.owner_id})>"
```

**双方向リレーション:** `UserModel`には既に`todos = relationship("TodoModel", back_populates="owner", cascade="all, delete-orphan")`が定義されています。

### 10.6 libkoiki/schemas/todo.py
ToDoのPydanticスキーマは`libkoiki`フレームワーク内で定義されています。

```python
# libkoiki/schemas/todo.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the ToDo item")
    description: Optional[str] = Field(None, description="Optional description for the ToDo item")

class TodoCreate(TodoBase):
    # 作成時は is_completed は指定させない（デフォルトは False）
    pass

class TodoUpdate(BaseModel):
    # 更新時はすべてのフィールドを任意にする
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title for the ToDo item")
    description: Optional[str] = Field(None, description="New description for the ToDo item")
    is_completed: Optional[bool] = Field(None, description="Completion status of the ToDo item")

class TodoResponse(TodoBase):
    id: int = Field(..., description="Unique ID of the ToDo item")
    is_completed: bool = Field(..., description="Completion status")
    owner_id: int = Field(..., description="ID of the user who owns this ToDo")
    created_at: datetime = Field(..., description="Timestamp when the ToDo was created")
    updated_at: datetime = Field(..., description="Timestamp when the ToDo was last updated")

    class Config:
        from_attributes = True # SQLAlchemyモデルインスタンスから変換できるようにする
```

### 10.7 app/api/dependencies.py (アプリケーション固有の依存性)
アプリケーション固有の依存性（DI）を定義します。

```python
# app/api/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.core.dependencies import DBSessionDep
from app.services.todo_service import TodoService
from app.repositories.todo_repository import TodoRepository

def get_todo_repository() -> TodoRepository:
    """ToDoリポジトリのインスタンスを返す依存性関数。"""
    return TodoRepository()

def get_todo_service(
    # リポジトリをDIで注入
    repo: Annotated[TodoRepository, Depends(get_todo_repository)],
    # DBセッションはサービス内でリポジトリに設定するため不要
) -> TodoService:
    """ToDoサービスのインスタンスを返す依存性関数。"""
    return TodoService(repository=repo)
```

### 10.8 データベースマイグレーション (Alembic)
Alembicが `app/models/` 内のモデルも認識できるように設定します。

**`alembic/env.py` の修正箇所:**
`env.py` の冒頭で、`libkoiki` と `app` の両方のモデルモジュールをインポートするようにします。

```python
# alembic/env.py の上部 (sys.pathの設定などがある場合、その直後)
# ...
# プロジェクトルートをPythonパスに追加 (alembicコマンド実行時のカレントディレクトリに依存するため)
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

# libkoiki のモデルをインポートしてAlembicに認識させる
import libkoiki.models.user # 例
import libkoiki.models.role # 例
import libkoiki.models.permission # 例
import libkoiki.models.associations # 例

# app のモデルをインポートしてAlembicに認識させる
import app.models.todo_model # 例

# target_metadata の設定
from libkoiki.db.base import Base # プロジェクトで共有されるBaseインスタンス
target_metadata = Base.metadata
# ...
```
Alembicが正しく動作するためには、`alembic.ini` の `sqlalchemy.url` が設定されていること、そして `env.py` 内で `target_metadata` が全てのテーブルを含むように設定されていることが重要です。
`libkoiki.db.base.Base` が `app` 側でも共通して使われていれば、`target_metadata = Base.metadata` で問題ありません。

マイグレーションコマンド:
- `alembic revision --autogenerate -m "create_todos_table"`
- `alembic upgrade head`

### 10.9 起動方法

```bash
# 依存関係インストール (プロジェクトルートで)
# pip install -r requirements.txt (もしあれば)
poetry install # poetryを使用する場合
# pip install ".[dev]" (pyproject.tomlにdev依存がある場合)

# .envファイル作成 (プロジェクトルートに.env.exampleをコピーして編集)
# SECRET_KEY と JWT_SECRET を必ず設定！
cp .env.example .env
nano .env # または任意のエディタで編集

# DBマイグレーション (データベースが起動していること)
alembic upgrade head

# FastAPIアプリケーション起動 (プロジェクトルートから)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker 起動 (プロジェクトルートから、Celery設定が有効な場合)
# .envファイルで CELERY_BROKER_URL と CELERY_RESULT_BACKEND を設定しておくこと
celery -A libkoiki.tasks.celery_app worker --loglevel=info
```

Docker Compose を使用する場合:
```bash
# (docker-compose.yml が適切に設定されている前提)
docker-compose up --build
```
`docker-compose.yml` では、FastAPIアプリケーション、PostgreSQL、Redis、Celeryワーカを各サービスとして定義します。

---

## 11. エラーハンドリングと例外処理

アプリケーション全体で一貫性のあるエラーレスポンスを提供し、デバッグを容易にするための仕組みです。

### 11.1 カスタム例外
ビジネスロジック固有のエラーを示すカスタム例外。

**`libkoiki/core/exceptions.py` の実装例:**
```python
# libkoiki/core/exceptions.py
from fastapi import HTTPException, status
from typing import Optional

class BaseAppException(HTTPException): # FastAPIのHTTPExceptionを継承
    def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None, headers: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code if error_code else self.__class__.__name__.upper().replace("EXCEPTION", "_ERROR")

class ResourceNotFoundException(BaseAppException):
    def __init__(self, resource_name: str, resource_id: any, detail: Optional[str] = None):
        detail_msg = detail or f"{resource_name} with ID '{resource_id}' not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail_msg, error_code="RESOURCE_NOT_FOUND")

class ValidationException(BaseAppException): # ビジネスルール違反用
    def __init__(self, detail: str, error_code: Optional[str] = "BUSINESS_VALIDATION_ERROR"): # Pydanticのとは区別
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code)

class AuthenticationException(BaseAppException):
    def __init__(self, detail: str = "Authentication failed.", error_code: Optional[str] = "AUTHENTICATION_FAILED"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code=error_code, headers={"WWW-Authenticate": "Bearer"})

class AuthorizationException(BaseAppException):
    def __init__(self, detail: str = "Not authorized to perform this action.", error_code: Optional[str] = "AUTHORIZATION_FAILED"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, error_code=error_code)

class ConflictException(BaseAppException): # 例: 重複作成しようとした場合など
    def __init__(self, detail: str = "Resource conflict.", error_code: Optional[str] = "CONFLICT_ERROR"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, error_code=error_code)
```

### 11.2 グローバル例外ハンドラー
特定の例外を補足し、統一されたJSONエラーレスポンスを返します。

**`libkoiki/core/error_handlers.py` の実装例:**
```python
# libkoiki/core/error_handlers.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError # Pydanticのバリデーションエラー
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
from slowapi.errors import RateLimitExceeded # slowapiの例外
import structlog

from libkoiki.core.exceptions import BaseAppException, ResourceNotFoundException, ValidationException as BusinessValidationException

logger = structlog.get_logger(__name__)

async def base_app_exception_handler(request: Request, exc: BaseAppException):
    """カスタムアプリケーション例外の汎用ハンドラ"""
    error_code = getattr(exc, "error_code", "APPLICATION_ERROR") # error_codeがあれば使用
    log_extra = {"error_code": error_code, "status_code": exc.status_code, "path": str(request.url)}
    
    # エラーの深刻度に応じてログレベルを調整
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        logger.info(f"Application Exception (NotFound): {exc.detail}", extra=log_extra, exc_info=False)
    elif exc.status_code // 100 == 4: # 4xx系エラー
        logger.warning(f"Application Exception (ClientError): {exc.detail}", extra=log_extra, exc_info=False)
    else: # 5xx系エラーや予期せぬもの
        logger.error(f"Application Exception (ServerError): {exc.detail}", extra=log_extra, exc_info=True)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": error_code},
        headers=getattr(exc, "headers", None), # ヘッダーがあれば付与
    )

async def pydantic_validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPIのPydanticバリデーションエラーハンドラ"""
    logger.warning(f"Pydantic Request Validation Error at {request.method} {request.url.path}: {exc.errors()}", extra={"error_details": exc.errors(), "path": str(request.url)})
    # エラー詳細を整形して返すことも可能
    # errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "error_code": "PYDANTIC_VALIDATION_ERROR"}, # FastAPIデフォルトに近い形式
    )

async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    """データベース関連エラーの汎用ハンドラ"""
    error_code = "DB_OPERATION_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An unexpected database error occurred."

    if isinstance(exc, IntegrityError): # 一意性制約違反など
        status_code = status.HTTP_409_CONFLICT # 409 Conflictの方が適切
        detail = "Database integrity constraint violated. Resource might already exist or a foreign key constraint failed."
        error_code = "DB_INTEGRITY_ERROR"
        logger.warning(f"Database Integrity Error: {exc}", exc_info=False, extra={"error_code": error_code, "path": str(request.url)})
    elif isinstance(exc, NoResultFound): # SQLAlchemy 2.0 の .one() などで発生
        status_code = status.HTTP_404_NOT_FOUND
        detail = "The requested database record was not found."
        error_code = "DB_NO_RESULT_FOUND"
        logger.info(f"Database NoResultFound Error: {exc}", exc_info=False, extra={"error_code": error_code, "path": str(request.url)})
    else: # その他の SQLAlchemyError
        logger.error(f"Unhandled Database Error: {exc}", exc_info=True, extra={"error_code": error_code, "path": str(request.url)})

    return JSONResponse(status_code=status_code, content={"detail": detail, "error_code": error_code})

async def generic_exception_handler(request: Request, exc: Exception):
    """その他の予期せぬエラーのための最終防衛ラインハンドラ"""
    logger.error(f"Unhandled Generic Exception at {request.method} {request.url.path}: {exc}", exc_info=True, extra={"path": str(request.url)})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please try again later.", "error_code": "UNHANDLED_INTERNAL_SERVER_ERROR"},
    )

def setup_exception_handlers(app: FastAPI):
    """アプリケーションに主要な例外ハンドラーを登録する"""
    app.add_exception_handler(BaseAppException, base_app_exception_handler) # カスタムアプリ例外
    app.add_exception_handler(RequestValidationError, pydantic_validation_exception_handler) # Pydanticバリデーションエラー
    app.add_exception_handler(SQLAlchemyError, db_exception_handler) # DBエラー
    # RateLimitExceeded は app.main の lifespan で slowapi の _rate_limit_exceeded_handler を登録
    app.add_exception_handler(Exception, generic_exception_handler) # 最も汎用的なハンドラを最後に登録
    logger.info("Global exception handlers configured.")
```
`app/main.py` の `FastAPI` インスタンス作成後に `setup_exception_handlers(app)` を呼び出して登録します。

---

## 12. ロギングとモニタリング

アプリケーションの動作状況を把握し、問題発生時の調査を容易にするための機能です。

### 🔰 用語解説 (ロギング)

- **ロギング**: アプリケーションの挙動を記録することで、不具合の調査や運用監視に役立ちます。
- **structlog**: Pythonの構造化ロギングライブラリ。JSON形式などでログを出力し、機械的な処理を容易にする。
- **監査ログ**: セキュリティ上重要な操作（誰が、いつ、何をしたか）を記録するログ。

### 12.1 ロギング設定 (structlog)
`structlog` と標準 `logging` を組み合わせて構造化ログを出力します。

**`libkoiki/core/logging.py` の実装例:**
```python
# libkoiki/core/logging.py
import logging
import sys
import structlog
from structlog.types import Processor
from typing import Optional

def setup_logging(log_level_str: str = "INFO", app_env: str = "development", debug: bool = False):
    """structlog を使用してロギングを設定"""
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # structlogの共通プロセッサチェーン
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars, # contextvarsからの情報をマージ (リクエストIDなど)
        structlog.stdlib.add_logger_name,        # ロガー名 (module名) を追加
        structlog.stdlib.add_log_level,          # ログレベル (INFO, ERRORなど) を追加
        structlog.stdlib.PositionalArgumentsFormatter(), # %s形式のフォーマットに対応
        structlog.processors.StackInfoRenderer(),      # スタック情報をレンダリング (オプション)
        structlog.processors.format_exc_info,          # 例外情報を整形
        structlog.processors.TimeStamper(fmt="iso", utc=True), # ISO形式のタイムスタンプ (UTC)
    ]

    # 環境に応じた最終的な出力フォーマッタを選択
    if app_env == "development" or debug:
        # 開発環境: 人間が読みやすいコンソール出力
        final_processor = structlog.dev.ConsoleRenderer()
    else:
        # 本番環境: JSON形式で出力 (ログ集約システムとの連携を想定)
        final_processor = structlog.processors.JSONRenderer()
        # キーの順番を固定したい場合など
        # final_processor = structlog.processors.JSONRenderer(serializer=json.dumps, sort_keys=True)

    # structlog と標準 logging を連携させる設定
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter, # 標準loggingハンドラ用ラッパー
        ],
        logger_factory=structlog.stdlib.LoggerFactory(), # 標準loggingのLoggerを生成
        wrapper_class=structlog.stdlib.BoundLogger,    # 標準loggingのLogger互換のBoundLogger
        cache_logger_on_first_use=True,
    )

    # 標準loggingのルートロガー設定
    # これにより、structlog経由だけでなく、他のライブラリ(例: SQLAlchemy)からのログも同じ形式で出力される
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=final_processor, # 最終的な出力形式
        foreign_pre_chain=shared_processors, # structlog以外のログに適用するプロセッサ
    )

    handler = logging.StreamHandler(sys.stdout) # 標準出力へ
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Uvicornなどが既に追加しているハンドラをクリアする場合
    # for h in root_logger.handlers[:]:
    #     root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level) # ルートロガーのログレベル

    # 特定のライブラリのログレベルを調整
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not debug else logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not debug else logging.INFO)

    logger = structlog.get_logger("logging_setup") # このモジュール用のロガー
    logger.info("Logging configured successfully.", log_level=log_level_str, app_env=app_env, debug_mode=debug)

def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """structlogロガーを取得するヘルパー関数"""
    # __name__ を渡すと、呼び出し元のモジュール名でロガーが取得される
    return structlog.get_logger(name if name else __name__)

# 監査ログ用ロガー設定 (オプション、必要なら別の設定関数を作成)
# def setup_audit_logger():
#     audit_handler = logging.FileHandler("audit.log") # 例: 監査ログ専用ファイル
#     audit_formatter = structlog.stdlib.ProcessorFormatter(
#         processor=structlog.processors.JSONRenderer(), # 監査ログはJSON形式推奨
#         foreign_pre_chain=shared_processors
#     )
#     audit_handler.setFormatter(audit_formatter)
#     audit_log_instance = logging.getLogger("audit") # "audit" という名前のロガー
#     audit_log_instance.addHandler(audit_handler)
#     audit_log_instance.setLevel(logging.INFO)
#     audit_log_instance.propagate = False # ルートロガーに伝播させない
#     return structlog.wrap_logger(audit_log_instance)
```
`app/main.py` の `lifespan` 内で `setup_logging(settings.LOG_LEVEL, settings.APP_ENV, settings.DEBUG)` のように呼び出します。

### 12.2 監査ログ
セキュリティ上重要な操作を記録します。ミドルウェアで基本的な情報を記録し、サービス層で詳細情報を補足できます。

**`libkoiki/core/middleware.py` に監査ログミドルウェアの例:**
```python
# libkoiki/core/middleware.py (続き)
        # リクエスト/レスポンスボディのログ記録はデータ量と機密性に注意して選択的に行う
        # if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
        #     try:
        #         req_body_bytes = await request.body()
        #         # request.stream() を消費すると後続処理で読めなくなるため、再度ストリームを生成する
        #         request._stream = lambda: asyncio.BytesIO(req_body_bytes)
        #         if req_body_bytes: # 機密情報はマスキング処理が必要
        #             try:
        #                 req_json = json.loads(req_body_bytes.decode('utf-8'))
        #                 # パスワードなどの機密情報をマスク
        #                 if 'password' in req_json:
        #                     req_json['password'] = '***MASKED***'
        #                 log_entry["request_body"] = req_json
        #             except json.JSONDecodeError:
        #                 log_entry["request_body"] = "[Non-JSON body]"
        #     except Exception as e:
        #         log_entry["request_body_error"] = str(e)

        audit_logger.info("API request processed", **log_entry) # 構造化ログとして出力
        return response
```
`app/main.py` で `app.add_middleware(AuditLogMiddleware)` として登録。

### 12.3 ミドルウェアによるモニタリング (リクエストログ)
HTTPリクエストの基本情報をログ出力します。`structlog` を使用する場合、Uvicornのアクセスログを `structlog` で処理するように設定する方が一般的です。
(`uvicorn.run(..., access_log=True)` と `logging.getLogger("uvicorn.access").handlers = [...]`)
Uvicornのアクセスログはデフォルトで `INFO` レベルで出力されるため、`libkoiki/core/logging.py` で `uvicorn.access` ロガーのレベルを調整することで制御できます。

### 🔰 用語解説 (モニタリング)

- **モニタリング**: アプリケーションの動作状態（負荷、応答時間、異常発生など）を常時観測すること。
- **Prometheus**: オープンソースの監視ツール。時系列データを収集・保存し、アラートを発行できる。
- **メトリクス**: 監視対象の数値データ（例: リクエスト数、エラー率、CPU使用率）。

### 12.4 Prometheus メトリクス
`prometheus-fastapi-instrumentator` を使用してPrometheus形式のメトリクスを公開します。

**`libkoiki/core/monitoring.py` の実装例:**
```python
# libkoiki/core/monitoring.py
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

# カスタムメトリクスの例 (必要に応じて定義)
# from prometheus_client import Counter
# user_creations_total = Counter(
#     "koiki_user_creations_total", # メトリクス名 (プレフィックスを付けると良い)
#     "Total number of users created through the API."
# )

logger = structlog.get_logger(__name__)

def setup_monitoring(app: FastAPI):
    """FastAPIアプリケーションにPrometheus Instrumentatorを設定し、メトリクスエンドポイントを公開する"""
    
    instrumentator = Instrumentator(
        should_group_status_codes=True,   # ステータスコードをグループ化 (2xx, 3xx など)
        should_instrument_requests_inprogress=True, # 現在処理中のリクエスト数を計測
        excluded_handlers=["/metrics", "/health"],  # /metrics や /health エンドポイント自体は計測対象外
        inprogress_name="fastapi_requests_inprogress", # 処理中リクエスト数のメトリクス名
        inprogress_labels=True, # 処理中リクエストにラベルを付与するか
    )
    
    # FastAPIアプリケーションにInstrumentatorを適用し、
    # /metrics エンドポイントを公開する
    instrumentator.instrument(app).expose(
        app, 
        include_in_schema=False, # OpenAPIスキーマに/metricsを含めない
        should_gzip=True         # レスポンスをgzip圧縮するか
    )
    
    # 標準で追加されるメトリクスの例:
    # - fastapi_requests_total (ハンドラ、メソッド、ステータスコード別リクエスト総数)
    # - fastapi_requests_latency_seconds (リクエスト処理時間のヒストグラム/サマリ)
    # - fastapi_request_size_bytes (リクエストボディサイズのヒストグラム/サマリ)
    # - fastapi_response_size_bytes (レスポンスボディサイズのヒストグラム/サマリ)
    # - fastapi_requests_inprogress (処理中リクエスト数)
    
    logger.info("Prometheus monitoring configured. Metrics available at /metrics")

# カスタムメトリクスをインクリメントする例 (サービス層などで使用)
# def increment_user_creation_counter():
#     user_creations_total.inc()
```
`app/main.py` の `lifespan` 内で `setup_monitoring(app)` を呼び出す。
また、カスタムメトリクスを使用する場合は、該当する処理箇所で `increment_user_creation_counter()` のような関数を呼び出します。

---

## 13. セキュリティ

Web アプリケーションを保護するための基本的なセキュリティ機能です。

### 🚨 v0.5.0 セキュリティアップデート

KOIKI-FW v0.5.0では、重要なセキュリティ脆弱性の修正が実施されました：

**修正された脆弱性:**
- **fastapi**: 0.104.1 → 0.115.13 (修正: PYSEC-2024-38)
- **python-jose**: 3.3.0 → 3.5.0 (修正: PYSEC-2024-232, PYSEC-2024-233)  
- **starlette**: 0.27.0 → 0.46.2 (修正: GHSA-f96h-pmfr-66vw)

**その他のセキュリティ強化:**
- Python 3.13対応によるセキュリティ機能の強化
- 依存関係全体の最新化によるセキュリティリスクの軽減
- エンタープライズ向けセキュリティ監査ツール (pip-audit, bandit) の導入

### 🔰 用語解説 (セキュリティ一般)

- **セキュリティ**: アプリケーションを不正アクセスやデータ漏洩から守るための技術全般。
- **レートリミット**: 一定時間内に許可されるAPIリクエスト数を制限し、総当たり攻撃やDoS攻撃を防ぐ。
- **セキュリティヘッダ**: ブラウザのセキュリティ機能を有効化し、XSSやクリックジャッキングなどの攻撃を緩和するHTTPレスポンスヘッダ。
- **入力バリデーション**: 不正な入力データによる脆弱性を防ぐため、入力値を検証・無害化すること。

### 13.1 レートリミット (slowapi)
`slowapi` を使用してAPIエンドポイントへのリクエスト数を制限します。

**`libkoiki/core/rate_limiter.py` の実装例:**
```python
# libkoiki/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from libkoiki.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# レートリミッターのグローバルインスタンス
limiter = Limiter(
    key_func=get_remote_address,  # クライアントIPでレート制限
    default_limits=[settings.RATE_LIMIT_DEFAULT],  # デフォルトの制限（設定から）
    enabled=settings.RATE_LIMIT_ENABLED,  # 有効/無効設定
    strategy=settings.RATE_LIMIT_STRATEGY  # 制限戦略（例: fixed-window）
)

logger.debug(
    "Rate limiter initialized", 
    enabled=settings.RATE_LIMIT_ENABLED, 
    default_limits=settings.RATE_LIMIT_DEFAULT,
    strategy=settings.RATE_LIMIT_STRATEGY
)

# 使用例:
# 1. グローバル適用（app.add_middleware(SlowAPIMiddleware)）
# 2. エンドポイント単位で適用:
#    @router.post("/")
#    @limiter.limit("5/minute")
#    async def create_item(...):
#        ...
```

### 13.2 セキュリティヘッダ
ミドルウェアを使用してHTTPレスポンスにセキュリティ関連ヘッダを追加します。

**`libkoiki/core/middleware.py` に `SecurityHeadersMiddleware` の例:**
```python
# libkoiki/core/middleware.py
# (AuditLogMiddleware と同じファイル内でも良い)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # HTTPSを強制 (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Type Sniffing 防止
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # クリックジャッキング防止
        response.headers["X-Frame-Options"] = "DENY" # または "SAMEORIGIN"
        
        # リファラポリシー (プライバシー向上)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin" # 推奨値の一つ
        
        # Content-Security-Policy (CSP) はアプリケーションのコンテンツに合わせて慎重に設定
        # 例: インラインスクリプトやevalを禁止し、スクリプトやスタイルは同一オリジンからのみ許可
        # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none';"
        
        # Permissions-Policy (旧 Feature-Policy) - ブラウザ機能へのアクセス制御
        # 例: マイク、カメラ、位置情報へのアクセスをデフォルトで無効化
        # response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
```
`app/main.py` で `app.add_middleware(SecurityHeadersMiddleware)` として登録。CSPの設定は特に注意が必要で、フロントエンドの構成や使用する外部リソースによって適切に調整する必要があります。

### 13.3 入力バリデーション
- **Pydantic**: API層での型チェックと形式検証（メールアドレス、URL、数値範囲など）。スキーマ定義で `Field` を使って詳細なバリデーションルール（最小/最大長、正規表現パターンなど）を設定できます。
- **サービス層**: ビジネスルールに基づいたより複雑な検証（例: 関連データの存在チェック、状態遷移の妥当性）。カスタム例外 (`ValidationException`) でエラーを明示的に通知します。
- **サニタイズ**:
    - **SQLインジェクション**: SQLAlchemyなどのORMは、パラメータ化クエリ（プリペアドステートメント）を内部で使用するため、適切に使用されていれば防御できます。生のSQLを使う場合は必ずパラメータ化します。
    - **XSS (クロスサイトスクリプティング)**:
        - APIレスポンスとしてJSONを返す場合は、クライアント側（フロントエンド）がHTMLにデータを埋め込む際の処理が重要です。React, Vueなどのモダンフレームワークは基本的に安全な方法でデータをレンダリングします。
        - サーバーサイドでHTMLを生成する場合（Jinja2など）、テンプレートエンジンが提供する自動エスケープ機能を必ず有効にします。
    - **その他**: ファイルアップロード時のファイル名や種類、外部コマンド実行時の引数など、ユーザー入力を元にする場合は常に検証と無害化を行います。

### 🔰 用語解説 (パスワードセキュリティ)

- **パスワードポリシー**: 安全なパスワード設定をユーザーに強制するための規則群（長さ、文字種など）。
- **ハッシュ化**: パスワードを元の値に戻せない（または極めて困難な）一方向関数で変換すること。保存時は必ずハッシュ化されたパスワードを格納します。
- **ソルト**: ハッシュ化の際にパスワード毎に付加されるランダムなデータ。同じパスワードでも異なるハッシュ値が生成され、レインボーテーブル攻撃を防ぎます。

### 13.4 パスワードポリシー
安全なパスワード設定を強制します。

- **実装**: パスワード設定・変更APIを受け付けるサービス層 (`UserService`) でポリシーをチェックします。
- **ヘルパー関数**: `libkoiki/core/security.py` の `check_password_complexity` で基本的な複雑性（長さ、文字種）をチェック。
- **ポリシー例**:
    - 最小文字数（例: 12文字以上を推奨）
    - 文字種（大文字、小文字、数字、記号をそれぞれ1つ以上含む）
    - よく使われるパスワードの禁止（辞書攻撃対策、Have I Been Pwned API連携など）
    - パスワード履歴（過去N回のパスワードの再利用禁止）
    - アカウントロックアウト（ログイン試行回数制限を超えた場合に一時的にアカウントをロック）

**`libkoiki/core/security.py` のパスワードポリシーチェック (再掲):**
```python
# libkoiki/core/security.py の check_password_complexity 関数
import re
def check_password_complexity(password: str) -> bool:
    """パスワードが複雑性要件を満たしているか検証します"""
    if len(password) < 8: return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True
```

---

## 14. テスト戦略とテスト実装

品質確保と安全な開発のためにテストは不可欠です。`pytest` と `httpx.AsyncClient` を使用します。

### 🔰 用語解説 (テストの種類)

- **単体テスト (Unit Test)**: 個々の関数やクラスなど、最小単位の機能を隔離して検証。依存性はモック化。
- **統合テスト (Integration Test)**: 複数のコンポーネント（API、サービス、DBなど）を連携させて検証。
- **E2Eテスト (End-to-End Test)**: 実際のユーザー操作を模倣し、システム全体を検証。

### 14.1 テスト設定 (conftest.py)
`pytest` の設定と共通フィクスチャを `tests/conftest.py` で定義。

**`tests/conftest.py` の実装例:**
```python
# tests/conftest.py
import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool # テストではNullPoolを使うことが多い

from libkoiki.db.base import Base as CombinedBase # libkoikiとappで共有されるBase
from app.main import app # FastAPIアプリケーションインスタンス
from libkoiki.db.session import get_db # DI用のDBセッション取得関数

# テスト用のDB URL (環境変数やテスト専用設定ファイルから取得推奨)
DEFAULT_TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/koiki_test_db"

# --- Database Fixtures ---
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """セッションスコープのテストDBエンジン。テスト実行前にテーブルを作成し、終了後に破棄。"""
    # 環境変数からテストDB URLを取得、なければデフォルト値
    test_db_url = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    
    # テストではコネクションプールを無効化することが推奨される場合がある
    engine = create_async_engine(test_db_url, echo=False, poolclass=NullPool)
    
    async with engine.begin() as conn:
        # 既存のテーブルを全て削除 (安全のため)
        await conn.run_sync(CombinedBase.metadata.drop_all)
        # スキーマに基づいてテーブルを再作成
        await conn.run_sync(CombinedBase.metadata.create_all)
    
    yield engine # テスト実行中はエンジンを提供
    
    # テスト終了後にエンジンを破棄
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """関数スコープのテストDBセッション。各テスト後にロールバックする。"""
    # テスト用のセッションファクトリを作成
    AsyncTestingSessionLocal = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False # テストではFalse推奨
    )
    async with AsyncTestingSessionLocal() as session:
        # 各テストをネストされたトランザクション内で実行
        # これにより、テスト終了時にロールバックしてDB状態を元に戻せる
        await session.begin_nested() 
        yield session
        # テストでコミットされても、このロールバックで元に戻る
        await session.rollback() 
        await session.close()


# --- HTTP Client Fixture ---
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """非同期HTTPテストクライアント。DBセッションをテスト用にオーバーライド。"""
    
    # get_db 依存性をテスト用セッションでオーバーライドする関数
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # FastAPIアプリケーションの依存性をオーバーライド
    app.dependency_overrides[get_db] = override_get_db
    
    # httpx.AsyncClient をアプリケーションインスタンスと共に初期化
    async with AsyncClient(app=app, base_url="http://testserver") as async_client: # base_urlは任意
        yield async_client
    
    # テスト終了後にオーバーライドを元に戻す (クリーンアップ)
    del app.dependency_overrides[get_db]

# --- 認証済みクライアントのフィクスチャ (オプション) ---
from libkoiki.services.user_service import UserService
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.schemas.user import UserCreate
from libkoiki.models.user import UserModel
from libkoiki.core.security import create_access_token

@pytest_asyncio.fixture(scope="function")
async def authenticated_user(db_session: AsyncSession) -> UserModel:
    """テスト用の認証済みユーザーを作成し、返すフィクスチャ。"""
    user_repo = UserRepository() # リポジトリをインスタンス化
    user_service = UserService(repository=user_repo) # サービスをインスタンス化
    
    test_user_email = "authtest@example.com"
    test_user_password = "AuthTestP@sswOrd1!"
    # 既存ユーザーがいれば削除または取得 (冪等性のため)
    user_repo.set_session(db_session)
    existing_user = await user_repo.get_by_email(test_user_email)
    if existing_user:
        # 既存ユーザーを使用
        return existing_user

    user_data = UserCreate(email=test_user_email, password=test_user_password, full_name="Auth Test User")
    user = await user_service.create_user(user_in=user_data, db=db_session)
    return user

@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, authenticated_user: UserModel):
    """認証済みユーザーのトークンをヘッダーに設定したHTTPクライアントを返す。"""
    token = create_access_token(subject=authenticated_user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    # 後処理 (ヘッダー削除など)
    del client.headers["Authorization"]
```

### 14.2 単体テスト例
サービス層のロジックなどを、依存性をモック化 (`unittest.mock.AsyncMock`) してテストします。

**`tests/unit/services/test_app_todo_service.py` の実装例:**
```python
# tests/unit/services/test_app_todo_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.services.todo_service import TodoService
from app.repositories.todo_repository import TodoRepository # モック対象
from app.models.todo_model import TodoModel # 返り値の型として使用
from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException # 例外のテスト用

# テスト用にロガーをモック
@pytest.fixture(autouse=True)
def mock_structlog():
    with patch('structlog.get_logger'):
        yield

@pytest.fixture
def mock_todo_repo() -> MagicMock:
    repo = MagicMock(spec=TodoRepository) # specでメソッド存在チェック
    repo.set_session = MagicMock() # set_sessionもモック化
    repo.create = AsyncMock()      # DB操作メソッドはAsyncMock
    repo.get = AsyncMock()
    repo.get_multi_by_owner = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo

@pytest.fixture
def mock_db_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    # トランザクションデコレータが `session.begin()` を呼び出すため、そのモックも用意
    # __aenter__ と __aexit__ を持つコンテキストマネージャを返すようにする
    mock_transaction_context = AsyncMock()
    mock_transaction_context.__aenter__ = AsyncMock(return_value=None) # begin() の中身
    mock_transaction_context.__aexit__ = AsyncMock(return_value=None)  # commit/rollback
    session.begin = MagicMock(return_value=mock_transaction_context) # begin()がコンテキストマネージャを返す
    session.in_transaction = MagicMock(return_value=False) # 通常はトランザクション外から開始
    return session

@pytest.fixture
def todo_service(mock_todo_repo: TodoRepository) -> TodoService:
    return TodoService(repository=mock_todo_repo)

@pytest.mark.asyncio
async def test_create_todo_success(
    todo_service: TodoService, 
    mock_todo_repo: MagicMock,
    mock_db_session: AsyncMock
):
    """ToDo作成が成功するケースの単体テスト"""
    todo_data = TodoCreateSchema(title="Unit Test Todo", description="Test description")
    owner_id = 1
    
    # リポジトリのcreateメソッドが返すダミーのTodoModelインスタンス
    expected_created_todo = TodoModel(id=1, title=todo_data.title, description=todo_data.description, owner_id=owner_id, completed=False)
    mock_todo_repo.create.return_value = expected_created_todo

    # @transactional デコレータを考慮し、dbセッションを渡す
    # デコレータ内のロガーをモック化 (オプション)
    with patch('libkoiki.core.transaction.logger'):
        created_todo = await todo_service.create_todo(todo_data=todo_data, db=mock_db_session, owner_id=owner_id)

    assert created_todo is not None
    assert created_todo.id == 1
    assert created_todo.title == "Unit Test Todo"
    assert created_todo.owner_id == owner_id
    
    # リポジトリメソッドの呼び出し確認
    mock_todo_repo.set_session.assert_called_once_with(mock_db_session)
    mock_todo_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_todo_by_id_and_owner_found(
    todo_service: TodoService, mock_todo_repo: MagicMock, mock_db_session: AsyncMock
):
    """IDとオーナーIDでToDoを取得し、見つかるケース"""
    todo_id = 1
    owner_id = 1
    expected_todo = TodoModel(id=todo_id, title="Test Todo", owner_id=owner_id)
    mock_todo_repo.get.return_value = expected_todo # getメソッドの戻り値を設定

    todo = await todo_service.get_todo_by_id_and_owner(todo_id=todo_id, owner_id=owner_id, db=mock_db_session)

    assert todo is not None
    assert todo.id == todo_id
    assert todo.owner_id == owner_id
    mock_todo_repo.set_session.assert_called_once_with(mock_db_session)
    mock_todo_repo.get.assert_called_once_with(todo_id)

@pytest.mark.asyncio
async def test_get_todo_by_id_and_owner_not_found(
    todo_service: TodoService, mock_todo_repo: MagicMock, mock_db_session: AsyncMock
):
    """ToDoが見つからないケース"""
    todo_id = 99
    owner_id = 1
    mock_todo_repo.get.return_value = None # getメソッドがNoneを返すように設定

    todo = await todo_service.get_todo_by_id_and_owner(todo_id=todo_id, owner_id=owner_id, db=mock_db_session)
    
    assert todo is None # サービスはNoneを返し、ルーターが404をハンドリングする想定

@pytest.mark.asyncio
async def test_get_todo_by_id_and_owner_unauthorized(
    todo_service: TodoService, mock_todo_repo: MagicMock, mock_db_session: AsyncMock
):
    """オーナーが異なるため権限がないケース"""
    todo_id = 1
    correct_owner_id = 2
    requesting_owner_id = 1 # 別のユーザー
    
    # DBにはToDoが存在するが、オーナーが異なる
    todo_in_db = TodoModel(id=todo_id, title="Someone else's Todo", owner_id=correct_owner_id)
    mock_todo_repo.get.return_value = todo_in_db

    todo = await todo_service.get_todo_by_id_and_owner(todo_id=todo_id, owner_id=requesting_owner_id, db=mock_db_session)
    
    assert todo is None # サービスはNoneを返し、ルーターが404/403をハンドリング
```

### 🔰 用語解説 (モック)

- **モック (Mock)**: テスト対象のコードが依存している外部コンポーネント（DB、外部APIなど）の振る舞いを模倣する偽のオブジェクト。これにより、テストが外部環境に依存せず、実行速度が向上し、エラーケースなど特定のシナリオを再現しやすくなります。

### 14.3 統合テスト例
APIエンドポイントからDBまでを連携させてテストします。`client` フィクスチャを使用します。

**`tests/integration/api/test_app_todos_api.py` の実装例:**
```python
# tests/integration/api/test_app_todos_api.py
import pytest
from httpx import AsyncClient
from fastapi import status
import structlog

from libkoiki.core.config import settings
from libkoiki.models.user import UserModel

# API Prefix を取得
API_PREFIX = settings.API_PREFIX
TODO_API_BASE_URL = f"{API_PREFIX}/todos" # /api/v1/todos など

# テスト用にロガーをモック
@pytest.fixture(autouse=True)
def mock_structlog():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(structlog, "get_logger", lambda *args, **kwargs: MagicMock())
        yield

@pytest.mark.asyncio
async def test_create_todo_api_success(authenticated_client: AsyncClient, authenticated_user: UserModel):
    """ToDo作成APIが正常に動作するケース (201 Created)"""
    todo_payload = {"title": "Integration Test My Todo", "description": "This is an integration test."}
    response = await authenticated_client.post(TODO_API_BASE_URL + "/", json=todo_payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == todo_payload["title"]
    assert data["description"] == todo_payload["description"]
    assert "id" in data
    assert data["completed"] is False # デフォルト値の確認
    assert data["owner_id"] == authenticated_user.id # 作成者が正しいか確認

@pytest.mark.asyncio
async def test_create_todo_api_unauthenticated(client: AsyncClient):
    """未認証でToDo作成APIを呼ぶとエラー (401 Unauthorized)"""
    todo_payload = {"title": "Unauthorized Todo"}
    response = await client.post(TODO_API_BASE_URL + "/", json=todo_payload) # auth_headersなし
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_my_todos_api_success(authenticated_client: AsyncClient, authenticated_user: UserModel):
    """自分のToDo一覧を取得するAPIが正常に動作するケース"""
    # 事前にテストユーザーのToDoをいくつか作成 (このテスト専用)
    await authenticated_client.post(TODO_API_BASE_URL + "/", json={"title": "My Todo Item 1"})
    await authenticated_client.post(TODO_API_BASE_URL + "/", json={"title": "My Todo Item 2"})
    
    response = await authenticated_client.get(TODO_API_BASE_URL + "/")
    assert response.status_code == status.HTTP_200_OK
    todos = response.json()
    assert isinstance(todos, list)
    assert len(todos) >= 2 # 少なくとも2つはあるはず
    for todo in todos:
        assert todo["owner_id"] == authenticated_user.id # 自分のToDoのみが返されていることを確認

@pytest.mark.asyncio
async def test_get_todo_by_id_api_success(authenticated_client: AsyncClient, authenticated_user: UserModel):
    """特定のToDoを取得するAPIが正常に動作するケース"""
    # 1. テスト用ToDoを作成
    create_response = await authenticated_client.post(
        TODO_API_BASE_URL + "/", 
        json={"title": "Todo for Get Test", "description": "This todo will be retrieved by ID"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    todo_id = create_response.json()["id"]
    
    # 2. 作成したToDoをIDで取得
    get_response = await authenticated_client.get(f"{TODO_API_BASE_URL}/{todo_id}")
    assert get_response.status_code == status.HTTP_200_OK
    todo = get_response.json()
    assert todo["id"] == todo_id
    assert todo["title"] == "Todo for Get Test"
    assert todo["owner_id"] == authenticated_user.id

@pytest.mark.asyncio
async def test_update_my_todo_api_success(authenticated_client: AsyncClient):
    """自分のToDoを更新するAPIが正常に動作するケース"""
    # 1. 更新対象のToDoを作成
    create_response = await authenticated_client.post(TODO_API_BASE_URL + "/", json={"title": "Todo Before Update"})
    assert create_response.status_code == status.HTTP_201_CREATED
    todo_id_to_update = create_response.json()["id"]

    # 2. ToDoを更新
    update_payload = {"title": "Todo After Update", "completed": True}
    update_response = await authenticated_client.put(f"{TODO_API_BASE_URL}/{todo_id_to_update}", json=update_payload)
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["title"] == update_payload["title"]
    assert updated_data["completed"] == update_payload["completed"]

@pytest.mark.asyncio
async def test_delete_my_todo_api_success(authenticated_client: AsyncClient):
    """自分のToDoを削除するAPIが正常に動作するケース"""
    # 1. 削除対象のToDoを作成
    create_response = await authenticated_client.post(TODO_API_BASE_URL + "/", json={"title": "Todo To Be Deleted"})
    assert create_response.status_code == status.HTTP_201_CREATED
    todo_id_to_delete = create_response.json()["id"]

    # 2. ToDoを削除
    delete_response = await authenticated_client.delete(f"{TODO_API_BASE_URL}/{todo_id_to_delete}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT # 成功時はNo Content

    # 3. 削除されたことを確認 (GETで404になるはず)
    get_response_after_delete = await authenticated_client.get(f"{TODO_API_BASE_URL}/{todo_id_to_delete}")
    assert get_response_after_delete.status_code == status.HTTP_404_NOT_FOUND
```

---

## 15. ロールと権限

RBAC (ロールベースアクセス制御) のためのモデルと仕組み。

### 15.1 ロール・権限モデル
`libkoiki/models/` に `RoleModel`, `PermissionModel`, およびそれらをUserと紐付ける中間テーブル (`user_roles_association`, `role_permissions_association` in `libkoiki/models/associations.py`) を定義します。

**`libkoiki/models/role.py`:**
```python
# libkoiki/models/role.py
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base
from libkoiki.models.associations import user_roles_association, role_permissions_association # 中間テーブルをインポート

class RoleModel(Base):
    # __tablename__ = "roles" # CustomBaseで自動設定

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship(
        "UserModel", 
        secondary=user_roles_association, 
        back_populates="roles"
    )
    permissions = relationship(
        "PermissionModel", 
        secondary=role_permissions_association, 
        back_populates="roles"
    )
```

**`libkoiki/models/permission.py`:**
```python
# libkoiki/models/permission.py
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base
from libkoiki.models.associations import role_permissions_association # 中間テーブルをインポート

class PermissionModel(Base):
    # __tablename__ = "permissions" # CustomBaseで自動設定

    name = Column(String, unique=True, index=True, nullable=False) # 例: "todos:create", "users:read"
    description = Column(String, nullable=True)

    roles = relationship(
        "RoleModel", 
        secondary=role_permissions_association, 
        back_populates="permissions"
    )
```

**`libkoiki/models/associations.py` (中間テーブル):**
```python
# libkoiki/models/associations.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from libkoiki.db.base import Base # Base.metadata を使用するため

# ユーザーとロールの多対多関連テーブル
user_roles_association = Table(
    "user_roles_association", # テーブル名を明示的に指定
    Base.metadata, # このBaseはプロジェクト全体で共有されるインスタンスであること
    Column("user_id", Integer, ForeignKey("usermodel.id", ondelete="CASCADE"), primary_key=True), # テーブル名は小文字
    Column("role_id", Integer, ForeignKey("rolemodel.id", ondelete="CASCADE"), primary_key=True)  # テーブル名は小文字
)

# ロールと権限の多対多関連テーブル
role_permissions_association = Table(
    "role_permissions_association",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("rolemodel.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissionmodel.id", ondelete="CASCADE"), primary_key=True)
)
```
`libkoiki/models/user.py` の `UserModel` にも `roles` リレーションを追加します。
```python
# libkoiki/models/user.py (追記)
from libkoiki.models.associations import user_roles_association # 中間テーブルをインポート
# ... UserModelクラス内 ...
roles = relationship(
    "RoleModel",
    secondary=user_roles_association,
    back_populates="users",
    lazy="selectin" # Eager loading strategy (optional, for performance)
)
```
`lazy="selectin"` などのEager Loading戦略は、特に認証時にユーザーのロールや権限を頻繁に参照する場合にパフォーマンス改善に繋がることがあります。

### 15.2 権限チェックの実装
`libkoiki/core/security.py` (または `libkoiki/auth/rbac.py`) で権限チェック用の依存性ヘルパーを定義します。

```python
# libkoiki/core/security.py (または libkoiki/auth/rbac.py に分離推奨)
# ... 既存のインポートに加えて ...
from fastapi import Security
import structlog

logger = structlog.get_logger(__name__)

# 権限チェックのための依存性関数
def require_permission(required_permission: str):
    """
    指定された権限をユーザーが持っているか確認する依存性。
    持っていない場合はHTTP 403 Forbiddenを返す。
    
    Args:
        required_permission: 必要な権限名 (例: "todos:create")
        
    Returns:
        Depends オブジェクト
    """
    async def permission_checker(
        current_user: Annotated[UserModel, Security(get_current_active_user)] # SecurityでActiveUserDepを使用
    ) -> UserModel:
        if not hasattr(current_user, 'roles') or not current_user.roles:
            logger.warning(
                "Permission check failed: user has no roles", 
                user_id=current_user.id, 
                required_permission=required_permission
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User has no roles assigned or roles not loaded."
            )

        user_permissions = set()
        for role in current_user.roles:
            if hasattr(role, 'permissions') and role.permissions:
                for perm_obj in role.permissions: # perm_obj は PermissionModel インスタンス
                    user_permissions.add(perm_obj.name) # PermissionModelのname属性 (権限名) をセットに追加
        
        if required_permission not in user_permissions:
            logger.warning(
                "Permission check failed: insufficient permissions", 
                user_id=current_user.id,
                user_permissions=list(user_permissions),
                required_permission=required_permission
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: '{required_permission}'"
            )
            
        logger.debug(
            "Permission check passed", 
            user_id=current_user.id, 
            required_permission=required_permission
        )
        return current_user # 権限があればユーザーオブジェクトを返す (他の処理で使えるように)
    
    return Depends(permission_checker) # Dependsでラップして返す

# 使用例 (ルーターのエンドポイントで):
# @router.post("/", dependencies=[Depends(require_permission("todos:create"))])
# async def create_item(...):
#     ...
```
**重要:**
`get_current_user_from_token` 関数内で、ユーザー取得時に `selectinload` を使って `roles` および `roles.permissions` リレーションをEager Loadingすることを忘れないでください。これは、`UserRepository` の `get_user_with_roles_permissions` メソッドを使用して実現されています。

---

## 16. UI/UX実装の選択肢

このバックエンドフレームワークは、様々なフロントエンド実装と組み合わせることが可能です。

### 🔰 用語解説 (UI/UX)
- **UI (User Interface)**: ユーザーがシステムとやり取りする接点（画面デザイン、ボタンなど）。
- **UX (User Experience)**: ユーザーがシステムを利用する際の全体的な体験（使いやすさ、満足度など）。
- **SPA (Single Page Application)**: 単一のHTMLページで動作し、JavaScriptで動的にコンテンツを書き換えるWebアプリ。React, Vue, Angularなど。
- **SSR (Server-Side Rendering)**: サーバー側でHTMLを生成してクライアントに返す方式。Jinja2など。
- **SSG (Static Site Generation)**: ビルド時に静的なHTMLファイルを生成する方式。Next.js, Gatsbyなど。
- **Hybrid**: SPAとSSR/SSGを組み合わせたアプローチ。Next.jsなど。

### 16.1 SPA (React, Next.js, Vue.js など)

*   **特徴**: モダンな UI/UX、高いインタラクティブ性、バックエンドとの完全分離。状態管理が複雑になることがある。
*   **連携**: バックエンドの REST API (このフレームワークが提供) と HTTP 通信。
*   **構成**: フロントエンドプロジェクトをバックエンドとは別のリポジトリ/ディレクトリで管理することが一般的。Docker Compose で統合して開発・デプロイできる。
*   **認証**: API から取得した JWT をフロントエンドで安全に管理 (例: HttpOnly Cookie (SameSite属性に注意), localStorage + CSRF対策, セキュアな状態管理ライブラリ)。
*   **適した用途**: 動的でリッチなユーザーインターフェース、モバイルアプリとの API 共通化、複雑な状態管理が必要なアプリケーション。

### 16.2 サーバーサイドテンプレートエンジン (Jinja2など)

*   **特徴**: シンプルな構成、バックエンドとの連携が容易（特にPythonエコシステム内）、初期表示速度が速い傾向、SEO に有利な場合も。インタラクティブ性は SPA より制限される。
*   **連携**: FastAPI 内で Jinja2 などのテンプレートエンジンを使用し、サーバー側でHTML をレンダリング。API と同じプロセスで動作可能。
*   **構成**: `app/templates/` (HTMLテンプレート), `app/static/` (CSS, JS, 画像) ディレクトリを追加。FastAPI ルーターが `HTMLResponse` を返す。
*   **認証**: サーバーサイドセッション（例: `starlette-sessions`）または API と同様の JWT フロー（CookieにJWTを格納など）。
*   **適した用途**: 管理画面、比較的静的なコンテンツが多いウェブサイト、プロトタイピング、SEOが重要な公開サイトの一部。

### 16.3 Streamlit

*   **特徴**: Python のみでインタラクティブなデータアプリやダッシュボードを迅速に構築。データサイエンティストや分析者向け。
*   **連携**: Streamlit アプリからバックエンド API を呼び出すか、バックエンドのサービス/リポジトリ層のコードを直接 (または調整して) 利用。
*   **構成**: `streamlit_app/` ディレクトリなどで Streamlit アプリを管理。バックエンドとは別プロセスで実行することが多い。
*   **認証**: Streamlit アプリ自体に認証機構を追加（`streamlit-authenticator`など）するか、バックエンド API へのリクエスト時に認証情報を付与。
*   **適した用途**: データ分析・可視化ダッシュボード、社内ツール、機械学習モデルのデモ、プロトタイピング。

### 16.4 プロジェクト横断の実装・運用上の留意点

*   **API First Design**: どのUIを選択する場合でも、まずはAPIの設計と実装を固めることが重要。APIが安定していれば、UIの変更や追加が容易になる。
*   **認証・認可の一貫性**: UIが異なっても、バックエンドAPIの認証・認可ロジックは共通して適用されるべき。UI側での表示制御と、API側での強制的な権限チェックの両方を実装する。
*   **CORS設定**: SPAなど異なるオリジンからAPIにアクセスする場合は、`app/main.py` でCORSMiddlewareを適切に設定する必要がある。
*   **設定の共通化と分離**: データベース接続情報など、UI層とAPI層で共通の設定が必要な場合でも、機密情報はUI層に直接埋め込まない。UI層はAPIエンドポイントのURLだけを知っていればよい。
*   **開発・デプロイ**: 各層（バックエンドAPI、フロントエンドSPA、Streamlitアプリなど）を独立して開発・テスト・デプロイできる構成を目指す（Docker Composeなどを活用）。
*   **状態管理**: 特にSPAでは、クライアント側の状態管理（ユーザー情報、UIの状態など）の戦略を早期に決定する。
*   **エラーハンドリング**: APIからのエラーレスポンスをUI側で適切にハンドリングし、ユーザーフレンドリーな形で表示する。

---

## 17. 継続的インテグレーション (CI)

KOIKI-FWでは、GitHub Actionsを活用した継続的インテグレーション（CI）パイプラインを実装しています。このCIプロセスにより、コードの品質保証を自動化し、問題を早期に発見できます。

### 🔰 用語解説 (CI/CD)

| 用語 | 説明 |
|------|------|
| **CI (Continuous Integration)** | 開発者がコードを頻繁に共有リポジトリに統合する開発手法。各統合は自動テストやビルドで検証され、問題を早期発見する。 |
| **CD (Continuous Delivery/Deployment)** | CIの延長線上にある概念で、ソフトウェアをいつでもリリース可能な状態に保ち（Delivery）、自動的に本番環境にデプロイ（Deployment）する手法。 |
| **GitHub Actions** | GitHubが提供するCI/CDプラットフォーム。リポジトリ内のイベント（プッシュ、プルリクエストなど）をトリガーにワークフローを実行できる。 |
| **ワークフロー** | GitHub Actionsで定義される自動化プロセス。YAML形式で記述され、特定のイベントで実行される一連のジョブやステップを定義。 |
| **ランナー** | ワークフローのジョブを実行するサーバー環境。GitHub提供のホストランナーや自己ホストランナーがある。 |
| **カバレッジ** | テストがコードのどれだけの部分を実行したかを示す指標。高いカバレッジは潜在的なバグの発見確率を高める。 |

### 17.1 GitHub Actions によるCI

KOIKI-FWのCIパイプラインは、GitHub Actionsを使用して実装されています。この選択には以下の利点があります：

1. **GitHubとの統合**: コードリポジトリと同じプラットフォーム上でCI/CDを実行でき、シームレスな開発体験を提供
2. **設定の簡易さ**: YAMLベースの簡単な設定ファイルで複雑なワークフローを定義可能
3. **豊富なアクション**: 再利用可能なアクションの大規模なエコシステムにアクセス可能
4. **並列実行**: 複数のテストやビルドを並行して実行できるスケーラビリティ

### 17.2 CIパイプラインの構成

CIパイプラインは `.github/workflows/ci.yml` ファイルで定義されており、以下のタイミングで実行されます：

```yaml
on:
  push:
    branches: [master, develop, dev/*, feature/*, bugfix/*]
  pull_request:
    branches: [master, develop]
```

これにより、次のイベントでCIが実行されます：
- **プッシュイベント**: `master`、`develop`、`dev/`、`feature/`、`bugfix/` で始まるブランチへのプッシュ
- **プルリクエスト**: `master`または`develop`ブランチへのプルリクエスト

### 17.3 テスト自動化とカバレッジ

CIパイプラインの主要な機能の一つが自動テストとコードカバレッジの計測です：

```yaml
- name: Run tests with coverage (Poetry 2.x)
  run: |
    # Poetry 2.x: Use dependency groups for testing
    poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing --cov-report=html \
      tests/unit/app/
    # Poetry 2.x: Additional environment check
    poetry show --tree --only=main

- name: Upload HTML coverage report (optional)
  if: ${{ env.ACT != 'true' }}
  uses: actions/upload-artifact@v4
  with:
    name: html-coverage-report
    path: htmlcov
```

このステップにより：

1. **アプリケーション層のテスト実行**: `tests/unit/app/`配下のアプリケーション開発チーム向けの単体テストのみを実行
2. **カバレッジレポートの生成**: `app`および`libkoiki`ディレクトリのコードに対するカバレッジ情報をターミナル出力とHTML形式で生成
3. **レポートのアーティファクト保存**: HTML形式のカバレッジレポートをワークフロー成果物として保存し、後から確認可能
4. **Poetry 2.x最適化**: 依存関係の確認を含むPoetry 2.x機能を活用

**テスト範囲の設計思想:**
- CIでは`tests/unit/app/`のみを対象とし、アプリケーション開発チームのコードに焦点を当てる
- フレームワーク（`libkoiki`）のテストは開発時やローカル環境で実行される想定
- これにより、CIの実行時間を短縮し、アプリケーション開発チームに関連するテスト結果を迅速に提供

カバレッジレポートは、アプリケーションコードのどの部分がテストされているか、またはテストされていないかを視覚的に示し、開発チームがテストを改善するための指針となります。

### 17.4 CI環境の設定

CIワークフローでは、テスト用の一時的な環境が構築されます：

```yaml
services:
  postgres:
    image: postgres:15
    ports:
      - 5432:5432
    env:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

env:
  DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
  ENV_FILE: .env.ci
```

この設定により：

1. **PostgreSQLサービス**: テスト用のPostgreSQLデータベースをDockerコンテナとして起動
2. **ヘルスチェック**: データベースが確実に稼働するまで待機するヘルスチェックを設定
3. **環境変数**: テスト実行に必要な環境変数を設定
4. **Poetry環境**: Poetryを使用した依存関係管理と仮想環境の構築

この一貫した環境構築により、開発者のローカル環境に関係なく、すべてのテストが同一の条件で実行されます。

## 18. まとめ

KOIKI-FW v0.6.0は、認証系APIの充実とセキュリティ監査機能の強化により、エンタープライズWebアプリケーション開発のための包括的なフレームワークとしてさらに進化しました。モジュール構造の明確な分離により、`libkoiki`をコアライブラリとして、`app`をアプリケーション固有の実装として分けることで、高い保守性と再利用性を実現しています。

v0.6.0では、**認証系APIの大幅な拡張**を実施し、JWT認証、リフレッシュトークン、パスワードリセット、ログイン試行制限など、エンタープライズ環境で求められる包括的な認証システムを標準提供しています。また、セキュリティ監査APIにより、認証関連のセキュリティイベントを監視・記録し、不審な活動の検出とアラート機能を実現しました。

さらに、v0.5.0で実施された重要なセキュリティ脆弱性の修正と包括的な依存関係の最新化を継承し、v0.3.1で導入された継続的インテグレーション（CI）による開発プロセスの自動化と品質保証も引き続き強化されています。これにより、開発者はセキュリティと品質を確保しながら、より高度な認証機能を持つアプリケーションを迅速に構築できるようになりました。

このフレームワークは、シンプルなCRUDアプリケーションから複雑なエンタープライズシステムまで、様々な規模と複雑さのプロジェクトに適用できます。特に、実務で求められることの多い機能 - 認証・認可、非同期処理、トランザクション管理、ロギング、モニタリング - を標準で提供することで、開発者が本質的なビジネスロジックに集中できる環境を整えています。

## 19. 今後の拡張・DDDへの布石

| 領域                      | 現構成 (`libkoiki`/`app`)                                  | 拡張方向 (DDD要素の導入)                                                                       |
| :------------------------ | :--------------------------------------------------------- | :------------------------------------------------------------------------------------------------- |
| **ドメインモデル**        | `models/` (主にORMモデルとしてデータ構造を定義)                  | `app/domain/models/` にドメインエンティティと値オブジェクトを配置。DBモデルと分離。|
| **リポジトリ**            | `repositories/` (具象クラス、データアクセスロジック)            | `app/domain/repositories/` にリポジトリインターフェース（抽象）を定義。実装は `app/infrastructure/repositories/` へ。|
| **アプリケーションサービス** | `services/` (ビジネスロジック、ユースケースが混在)             | `app/application/services/` または `app/application/use_cases/` として明確にユースケース単位で整理。|
| **ドメインサービス**        | (サービス層に暗黙的に含まれる可能性あり)                      | `app/domain/services/` に、特定のエンティティに属さないドメインロジックを分離。|
| **ドメインイベント**        | `tasks/` (Celeryタスクがイベントハンドラ的に使われることも)    | `app/domain/events/` にドメインイベントを定義。イベント発行・購読の仕組みを整備。|
| **API層 (コントローラ)**  | `routers/` (リクエスト処理、サービス呼び出し)                   | `app/interfaces/api/` (または `app/presentation/api/`) に配置。アプリケーション層へのデータ変換責務を明確化。|
| **スキーマ (DTO)**        | `schemas/` (Pydanticモデル、APIの入出力と内部利用が混在) | API層とアプリケーションサービス間のデータ転送に特化したDTOを `app/application/dtos/` に分離。|

DDD（ドメイン駆動設計）を本格的に志向する場合、  
- **エンティティや値オブジェクトのドメインモデル分離と命名の厳格化**  
- **ユースケース（アプリケーションサービス）とドメインサービスの分離**  
- **インフラ層・アプリ層・ドメイン層の明確な役割分担**  
- **イベント駆動設計やCQRSパターンの段階的導入**  
- **抽象リポジトリとインフラ実装の分離**  
などが発展的な拡張ポイントとなります。

現状のKOIKI-FW構造はこうした拡張に備えた「足場」として設計されており、今後もコミュニティや実務現場の声を反映しながら進化を続けます。

---

## 20. バージョン履歴

| バージョン | 日付       | 主な変更内容                                                                                 |
|------------|------------|--------------------------------------------------------------------------------------------|
| 0.6.0      | 2025-07-16 | - 認証系APIの充実とセキュリティ監査API強化<br>- ロールベースアクセス制御 (RBAC) の実装<br>- 認証APIテストの包括的実装<br>- ドキュメント強化 (認証系API完全ガイド、セキュリティ強化対応記録、APIテストガイド) |
| 0.5.0      | 2025-06-21 | - 重要セキュリティ脆弱性の修正 (fastapi, python-jose, starlette)<br>- 包括的依存関係モダナイゼーション<br>- Python 3.13 対応<br>- エンタープライズ向け依存性管理戦略の導入 |
| 0.3.1      | 2024-06-XX | - CIパイプライン導入・設計ドキュメント刷新<br>- 認証・依存性の最新実装反映                 |
| 0.3.0      | 2024-05-XX | - `libkoiki/` と `app/` の明確な分離<br>- サービス/リポジトリ/モデル/スキーマ分割          |
| 0.2.x      | 2024-04-XX | - 非同期処理Celery・RBAC・監査ログの導入                                                     |
| 0.1.x      | 2024-03-XX | - FastAPIベースの初期バージョン                                                             |

## おわりに

本ドキュメントは KOIKI-FW の設計思想、ディレクトリ構成、主要機能、CI/CDやテスト戦略まで、実務に即した形で包括的にまとめました。

### ドキュメントと実装の整合性の重要性

KOIKI-FW v0.6.0 では、  
- **認証系APIの包括的実装（JWT、リフレッシュトークン、パスワードリセット、ログイン試行制限）**  
- **セキュリティ監査APIの強化（認証ログ記録、監査レポート、セキュリティアラート）**  
- **実装パスの明確化（例：`libkoiki/core/security.py` への統一）**  
- **依存性注入や設定取得の統一**  
- **CI/CD設計の明文化**  
- **サンプルコードの最新版へのアップデート**  
- **認証系ドキュメントの充実（完全ガイド、セキュリティ強化記録、テストガイド）**  

を徹底し、「設計書と実装に齟齬がないこと」を重視しています。  
設計ドキュメントが常に実装と同期し、現場の開発者が迷わず参照できる状態を維持することで、開発効率と品質の双方が向上します。v0.6.0では特に、エンタープライズ環境で求められる認証・セキュリティ機能を標準提供することで、開発者がセキュアなアプリケーションを迅速に構築できる環境を整えました。

---

### DDD・マルチレイヤ化への今後の展望

- 今後は本設計を土台に、「ドメイン層」「アプリケーション層」「インフラ層」「インターフェース層」のさらなる分割（DDDパターン）に拡張しやすい構成へ進化させていく予定です。
- ドメインモデルやドメインイベント、DTOなど、本格的な業務開発に必要な要素も段階的に取り入れていきます。

---

### 参考リンク

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy公式ドキュメント](https://docs.sqlalchemy.org/)
- [Pydantic公式ドキュメント](https://pydantic-docs.helpmanual.io/)
- [Celery公式ドキュメント](https://docs.celeryproject.org/)
- [structlog公式ドキュメント](https://www.structlog.org/)
- [GitHub Actions公式ドキュメント](https://docs.github.com/ja/actions)
- [pytest公式ドキュメント](https://docs.pytest.org/)

---

## Appendix: コントリビューションとFAQ

### コントリビューションガイド

1. **Issueの報告**  
   バグ・改善提案・質問などはGitHub Issuesへご登録ください。  
2. **Pull Requestの作成**  
   新機能追加やバグ修正は、明確な説明・テストケースを添えてプルリクエストを作成してください。
3. **ドキュメントの改善**  
   設計・導入・実装例などの改善提案も歓迎です。

### FAQ

**Q: サンプルや設計ドキュメントの内容と実際の実装で食い違いがある場合は？**  
A: 本ドキュメント v0.6.0 では、v0.5.0 で実施したパス・設定・依存性・CI/CDの実装差異の精査と記述修正を継承し、さらに認証系APIの充実とセキュリティ監査APIの強化について詳細に反映しています。また、新たに追加された認証機能（JWT、リフレッシュトークン、パスワードリセット、ログイン試行制限）とセキュリティ監査機能の実装についても包括的にドキュメント化しました。  
もし今後も差異を発見した場合は、Issueでご報告ください。

**Q: サンプルコードと実際のリポジトリ構成が異なる場合の対応は？**  
A: 必ず「最新版のリポジトリ実装」に合わせて本ドキュメントのサンプルや説明も追従する運用としています。設計ドキュメントを信頼できる唯一の仕様書とするためです。

**Q: DDD（ドメイン駆動設計）への移行はどのように進めていく？**  
A: まずはサービス・リポジトリ・モデルの責務分割を徹底し、ユースケース単位でのサービス化・DTO導入・リポジトリインターフェース化など、段階的な移行を図ります。

---

**本ドキュメントは、実装と設計の完全な同期を目指し、現場開発者の「迷いゼロ」を実現することを目標としています。**

---
