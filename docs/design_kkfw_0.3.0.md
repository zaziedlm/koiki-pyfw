
---

# KOIKI-FW v0.3

本ドキュメントは、エンタープライズ向けFastAPIベースのWebアプリケーション開発フレームワーク「KOIKI-FW」のバージョン 0.3 に対応した機能設計・構成ガイドです。
このバージョンでは、ライブラリ構成が `libkoiki/` に整理され、より再利用性の高い構成が導入されました。

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
    - [10.5 app/models/todo_model.py](#105-appmodelstodo_modelpy)
    - [10.6 app/schemas/todo_schema.py](#106-appschemastodo_schemapy)
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
- [17. まとめ](#17-まとめ)
- [18. 今後の拡張・DDDへの布石](#18-今後の拡張dddへの布石)
- [おわりに](#おわりに)

## 01. はじめに

KOIKI-FW は、FastAPI による堅牢かつ拡張可能な Web アプリケーションを構築するためのエンタープライズ向けテンプレートフレームワークです。

本フレームワークは以下のような目的で設計されています：

- エンジニアが業務アプリケーションを迅速に立ち上げられる **開発基盤の提供**
- インフラとロジックを明確に分離し、**保守性・再利用性・テスト容易性** を実現
- 非同期処理やJWT認証など、**実務要件に即した機能モジュールの標準搭載**
- 将来的な DDD（ドメイン駆動設計）導入を視野に入れた、拡張可能な構造

KOIKI-FW v0.3 では、フレームワーク機能を `libkoiki/` に明確に分離し、開発者が `/app` 以下にアプリケーション本体を実装できる構成を正式化しました。

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

-   **APIレイヤー** (`app/routers/`, `libkoiki/api/`):
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
-   **モデルレイヤー** (`app/models/`, `libkoiki/models/`, `app/schemas/`, `libkoiki/schemas/`):
    *   `models/`: SQLAlchemy を用いたデータベーステーブル定義 (ORM モデル)。
    *   `schemas/`: Pydantic を用いた API のリクエスト/レスポンスデータ構造定義、およびバリデーションルール。
-   **コア・インフラストラクチャレイヤー** (`libkoiki/core/`, `libkoiki/db/`, `libkoiki/auth/`, `libkoiki/tasks/`):
    *   設定 (`config.py`)、セキュリティ (`auth/jwt.py`)、カスタム例外 (`exceptions.py`)、トランザクション管理 (`transaction.py`)、ロギング (`logging.py`)、データベース接続 (`db/session.py`)、非同期タスクキュー (Celery) など、アプリケーション全体で共通の基盤機能を提供。

### 2.2 依存関係の流れ

以下に、主要コンポーネント間の依存関係の流れをテキストベースで示します。

```
[Client / External System]
  |
  (HTTP Request)
  V
[API Layer (FastAPI Routers in app/ or libkoiki/api/)]
  |  -------------------------------------------------------> [Authentication/Authorization (libkoiki/auth/)]
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
- DB Models (SQLAlchemy in app/models/, libkoiki/models/) - Used by Repository Layer
- Data Schemas (Pydantic in app/schemas/, libkoiki/schemas/) - Used by API and Service Layers
```

-   **依存の方向**: 矢印は依存の方向を示します。例えば、APIレイヤーはサービスレイヤーに依存しますが、サービスレイヤーはAPIレイヤーを知りません。これにより、内側のレイヤーの再利用性が高まります。
-   **依存性注入 (DI)**: FastAPI の `Depends` 機能により、上位レイヤーは下位レイヤーの具体的な実装ではなく、抽象（または依存性解決関数）に依存します。これにより、テスト容易性やコンポーネントの差し替えが容易になります。
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
│   ├── models/              # アプリケーション固有のDBモデル
│   │   └── todo_model.py
│   ├── repositories/        # アプリケーション固有のリポジトリ
│   │   └── todo_repository.py
│   ├── routers/             # アプリケーション固有のAPIルーター
│   │   └── todo_router.py
│   ├── schemas/             # アプリケーション固有のPydanticスキーマ
│   │   └── todo_schema.py
│   ├── services/            # アプリケーション固有のサービス
│   │   └── todo_service.py
│   └── main.py              # アプリケーションのエントリポイント
├── libkoiki/                # フレームワークコアライブラリ
│   ├── __init__.py
│   ├── api/                 # 共通DI、ルーター設定など
│   │   └── dependencies.py
│   ├── auth/                # 認証・認可関連
│   │   ├── jwt.py
│   │   └── rbac.py
│   ├── core/                # コアユーティリティ
│   │   ├── config.py
│   │   ├── error_handlers.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── monitoring.py
│   │   └── transaction.py
│   ├── db/                  # データベース関連
│   │   ├── base.py          # SQLAlchemy Base と共通モデル
│   │   └── session.py
│   ├── models/              # 共通DBモデル (User, Role, Permissionなど)
│   │   ├── __init__.py
│   │   ├── associations.py
│   │   ├── permission.py
│   │   ├── role.py
│   │   └── user.py
│   ├── repositories/        # 共通リポジトリ (BaseRepository, UserRepositoryなど)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── user_repository.py
│   ├── schemas/             # 共通Pydanticスキーマ (User, Tokenなど)
│   │   ├── __init__.py
│   │   ├── token.py
│   │   └── user.py
│   ├── services/            # 共通サービス (UserServiceなど)
│   │   ├── __init__.py
│   │   └── user_service.py
│   ├── tasks/               # Celeryタスク関連
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── example_task.py
│   └── pyproject.toml       # libkoikiのパッケージ情報
├── alembic/                 # DBマイグレーションスクリプト
├── tests/                   # テストコード (unit, integration)
├── .env.example             # 環境変数サンプル
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### 3.1 libkoiki (フレームワークコア)
`libkoiki/` は、アプリケーション横断的に利用される共通機能や基盤部品を配置します。この部分は独立した Python ライブラリとして管理され、他のプロジェクトでも再利用可能です。

- `libkoiki/core/`: 設定、ロギング、エラーハンドリング、ミドルウェア、トランザクション管理など。
- `libkoiki/db/`: SQLAlchemyのベース設定、DBセッション管理。
- `libkoiki/models/`: 汎用的な User, Role, Permission などのDBモデル。
- `libkoiki/schemas/`: User, Token などの汎用的なPydanticスキーマ。
- `libkoiki/repositories/`: `BaseRepository` や `UserRepository` などの汎用リポジトリ。
- `libkoiki/services/`: `UserService` などの汎用サービス。
- `libkoiki/auth/`: JWT認証、RBAC関連のロジック。
- `libkoiki/tasks/`: Celeryの基本設定や共通タスク。

### 3.2 app (アプリケーション固有)
`app/` は、特定のビジネスドメインに特化したコードを配置します。例えば、ToDo管理アプリケーションであれば、ToDoに関するモデル、スキーマ、リポジトリ、サービス、APIルーターなどがここに置かれます。

- `app/main.py`: FastAPIアプリケーションインスタンスの生成、`libkoiki`の機能の組み込み、`app/`固有ルーターの登録など。
- `app/routers/`: アプリケーション固有のAPIエンドポイント定義。
- `app/services/`: アプリケーション固有のビジネスロジック。
- `app/repositories/`: アプリケーション固有のデータアクセスロジック。
- `app/models/`, `app/schemas/`: アプリケーション固有のデータ構造定義。

この構成により、`libkoiki` を pip install 可能なフレームワークとして外部提供しながら、
`app/` 側では個別のユースケースやドメインに特化した開発を進めることができます。

---

## 04. 設定（Config）と依存性注入（DI）

この章では、アプリケーションを柔軟に構成する「設定管理」と、各処理で必要な機能を簡潔に使えるようにする「依存性注入（DI）」の仕組みについて解説します。

### 🔰 用語解説

- **設定（Config）**: アプリケーションを実行する際に、接続するデータベースや外部サービスの情報を `.env` ファイルなどから動的に読み込めるようにする仕組みです。環境ごとに設定を変えたい場合に便利です。
- **依存性注入（DI: Dependency Injection）**: あるクラスや関数が必要とする機能（例：DB接続やサービス）を「外から渡す」ことで、再利用性とテストのしやすさを高める設計パターンです。FastAPIでは、`Depends()` を使って自然にこのDIの仕組みを実現できます。

### 4.1 設定管理 (config.py)

アプリケーションの設定は `pydantic` の `BaseSettings` を使用して管理します。環境変数や `.env` ファイルから値を読み込み、型検証も行います。

**`libkoiki/core/config.py` の実装例:**
```python
# libkoiki/core/config.py
import os
from pydantic import BaseSettings, PostgresDsn, AnyHttpUrl, validator
from typing import Optional, Dict, Any, List, Union
from functools import lru_cache

class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "KOIKI-FW"
    APP_ENV: str = "development" # 例: development, staging, production
    DEBUG: bool = False
    SECRET_KEY: str # ★本番では必ず環境変数で設定★
    API_PREFIX: str = "/api/v1"

    # --- JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    ALGORITHM: str = "HS256"

    # --- Database ---
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "koiki_db"
    DATABASE_URL: Optional[PostgresDsn] = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg", # 非同期ドライバ
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        ))

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str): return v
        password_part = f":{values.get('REDIS_PASSWORD')}@" if values.get('REDIS_PASSWORD') else ""
        return f"redis://{password_part}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"

    # --- Celery ---
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # --- Rate Limiting (slowapi) ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_STRATEGY: str = "fixed-window"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = os.getenv("ENV_FILE", ".env") # 環境変数 `ENV_FILE` で .env ファイルを指定可能
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # .env ファイルが見つからなくてもエラーにしない
        # 必須項目は Settings クラスのフィールド定義で型ヒントのみ（デフォルト値なし）にすることで対応
        # 例: SECRET_KEY: str (デフォルト値なし) -> 環境変数または.envにないと起動時エラー
        # env_ignore_missing = True # Python-dotenv v1.0.0+

@lru_cache() # 設定オブジェクトをキャッシュして再利用
def get_settings() -> Settings:
    return Settings()

# settings = get_settings() # グローバルにインスタンスを作るより、get_settings()経由で取得を推奨
```
**環境設定の優先順位:**
1. OS環境変数
2. `.env` ファイル（`ENV_FILE`で指定されたもの、またはデフォルトの `.env`）
3. `Settings` クラスのフィールドで定義されたデフォルト値

**シークレット管理:**
`SECRET_KEY` や本番DBのパスワードなどの機密情報は、`.env` ファイルに直接記述せず、HashiCorp Vault, AWS Secrets Manager などのシークレット管理サービスや、Docker Secrets/Kubernetes Secrets を利用し、環境変数経由でアプリケーションに渡すことを強く推奨します。

### 4.2 依存性注入 (dependencies.py)

FastAPI の `Depends` を活用し、コンポーネント間の依存関係を解決します。これにより、コードの再利用性やテスト容易性が向上します。

**`libkoiki/api/dependencies.py` の実装例 (共通の依存性):**
```python
# libkoiki/api/dependencies.py
from typing import AsyncGenerator, Annotated, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis as AsyncRedis # redis.asyncioからRedisをインポート
from slowapi import Limiter
from slowapi.util import get_remote_address

from libkoiki.db.session import get_db_session # 非同期セッション取得関数
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.services.user_service import UserService
from libkoiki.auth.jwt import get_current_user_from_token # JWTからユーザー取得
from libkoiki.models.user import UserModel
from libkoiki.core.config import Settings, get_settings
# from libkoiki.events.publisher import EventPublisher # イベントシステムを使う場合

# --- 基本的な依存性 ---
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# --- Redis クライアント (アプリケーション状態から取得) ---
async def get_redis_client(request: Request) -> AsyncRedis:
    if not hasattr(request.app.state, 'redis') or not request.app.state.redis:
        raise HTTPException(status_code=503, detail="Redis connection not available")
    return request.app.state.redis
RedisClientDep = Annotated[AsyncRedis, Depends(get_redis_client)]

# --- イベントパブリッシャー (オプション) ---
# async def get_event_publisher(redis: RedisClientDep) -> EventPublisher:
# return EventPublisher(redis_client=redis)
# EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]

# --- レートリミッター (アプリケーション状態から取得) ---
async def get_limiter(request: Request) -> Limiter:
    if not hasattr(request.app.state, 'limiter') or not request.app.state.limiter:
         raise RuntimeError("Rate limiter not configured in application state")
    return request.app.state.limiter
LimiterDep = Annotated[Limiter, Depends(get_limiter)]

# --- リポジトリ (サービス内でインスタンス化することも多い) ---
# def get_user_repository() -> UserRepository:
# return UserRepository() # セッションはサービス/トランザクションデコレータ経由で設定

# --- サービス ---
def get_user_service(
    # event_publisher: Optional[EventPublisherDep] = None # イベント発行する場合
) -> UserService:
    user_repo = UserRepository() # サービス内でリポジトリを初期化
    # return UserService(repository=user_repo, event_publisher=event_publisher)
    return UserService(repository=user_repo)
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# --- 認証・認可 ---
CurrentUserDep = Annotated[UserModel, Depends(get_current_user_from_token)]

def get_current_active_user(current_user: CurrentUserDep) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
ActiveUserDep = Annotated[UserModel, Depends(get_current_active_user)]

def get_current_active_superuser(current_user: ActiveUserDep) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
SuperUserDep = Annotated[UserModel, Depends(get_current_active_superuser)]
```
FastAPIのDIシステムは、エンドポイント関数のシグネチャで `Depends` を使用して依存性を宣言すると、FastAPIがその依存性（関数やクラス）を実行またはインスタンス化し、結果を引数として渡します。これにより、コンポーネントは依存性の作成方法を知る必要がなく、自身のロジックに集中できます。テスト時には `app.dependency_overrides` を使ってこれらの依存性をモックに置き換えることが容易になります。

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
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from libkoiki.db.base import Base
# from libkoiki.models.associations import user_roles # 多対多関連テーブル

class UserModel(Base):
    # __tablename__ = "users" # CustomBaseで自動設定されるので不要な場合もある

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # roles = relationship("RoleModel", secondary=user_roles, back_populates="users")
    # todos = relationship("TodoModel", back_populates="owner") # アプリケーション固有モデルとの関連
```
(RoleModel, PermissionModel, associations.py なども同様に `libkoiki/models/` に定義)

アプリケーション固有のモデル (例: `TodoModel`) は `app/models/` に配置します (詳細は [10. アプリケーション実装例と起動方法 (app/)](#10-アプリケーション実装例と起動方法-app) を参照)。

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
        orm_mode = True # SQLAlchemyモデルからPydanticモデルへの変換を許可
```
(Tokenスキーマなども同様に `libkoiki/schemas/` に定義)

アプリケーション固有のスキーマ (例: `TodoSchema`) は `app/schemas/` に配置します。

---

## 06. リポジトリ層

リポジトリ（Repository）層は、データベースアクセスの詳細を隠蔽し、サービス層からは「データ取得・保存」という操作として扱えるようにする役割を担います。

### 🔰 用語解説

- **リポジトリパターン**: データベースへのアクセス処理を専用クラスに切り出すことで、アプリのビジネスロジックを簡潔かつテストしやすく保つ設計手法です。
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
このベースリポジトリは、コンストラクタで操作対象のモデルクラスを受け取り、`set_session` メソッドで非同期DBセッションを設定します。サービス層（またはトランザクションデコレータ）がこのセッション管理を行います。

### 6.2 具体的なリポジトリ実装
ベースリポジトリを継承し、モデル固有のクエリメソッドなどを追加します。

**`libkoiki/repositories/user_repository.py` の実装例:**
```python
# libkoiki/repositories/user_repository.py
from typing import Optional
from sqlalchemy.future import select
from libkoiki.models.user import UserModel
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
    # async def get_user_with_roles_permissions(self, user_id: int) -> Optional[UserModel]:
    #     from sqlalchemy.orm import selectinload
    #     from libkoiki.models.role import RoleModel # 循環参照を避けるためインポート位置に注意
    #     result = await self.db.execute(
    #         select(UserModel)
    #         .options(
    #             selectinload(UserModel.roles).selectinload(RoleModel.permissions)
    #         )
    #         .where(UserModel.id == user_id)
    #     )
    #     return result.scalar_one_or_none()
```
アプリケーション固有のリポジトリ (例: `TodoRepository`) は `app/repositories/` に配置します。

---

## 07. サービス層

サービス層は、ビジネスロジック（＝「どう処理すべきか」というルール）をまとめる場所です。

### 🔰 用語解説

- **サービス（Service）**: アプリケーションが提供する機能をまとめたクラスや関数群です。コントローラー（API層）とデータ層（リポジトリ）との橋渡し役を担います。
- たとえば「Todo を更新する」処理では、まずデータを取得し、必要な変更を加え、再保存するという一連の流れをこのサービス層で処理します。

この層を設けることで、APIルーティングやUIからの呼び出しが非常にシンプルになります。

### 7.1 サービスクラスの実装
サービスクラスは、コンストラクタで必要なリポジトリや他のサービスを受け取り（DI経由）、ビジネスロジックを実行するメソッドを提供します。

**`libkoiki/services/user_service.py` の実装例:**
```python
# libkoiki/services/user_service.py
from typing import Optional, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate, UserUpdate
from libkoiki.auth.jwt import get_password_hash, verify_password, check_password_complexity
# from libkoiki.events.publisher import EventPublisher # イベントシステムを使う場合
from libkoiki.core.exceptions import ValidationException, ResourceNotFoundException
from libkoiki.core.transaction import transactional # トランザクションデコレータ

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
        return await self.repository.delete(user_id) # deleteがオブジェクトを返す場合

    async def authenticate_user(self, email: str, password: str, db: AsyncSession) -> Optional[UserModel]:
        self.repository.set_session(db)
        user = await self.repository.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
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
from typing import Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import Depends # デコレータ内でDependsを使うのは推奨されないことが多い

# from libkoiki.db.session import get_db_session # DBセッション取得関数を直接使わない
from libkoiki.core.logging import get_logger

logger = get_logger(__name__)

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

**`libkoiki/auth/jwt.py` の実装例:**
```python
# libkoiki/auth/jwt.py
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Annotated, Union # Union を追加
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.core.config import Settings, get_settings
from libkoiki.models.user import UserModel
# from libkoiki.repositories.user_repository import UserRepository # リポジトリを使う場合
from libkoiki.db.session import get_db_session # 直接セッション取得

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# settings: Settings = get_settings() # グローバルではなく依存性経由で取得推奨

class TokenPayload(BaseModel):
    sub: Optional[int] = None # user_id
    exp: Optional[datetime] = None

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None, settings: Settings = Depends(get_settings)
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# OAuth2PasswordBearer は tokenUrl を API Prefix に合わせる
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().API_PREFIX}/auth/login")
# 設定がロードされるタイミングの問題があるので、関数内で初期化するか、DIで渡す
def get_oauth2_scheme(settings: Settings = Depends(get_settings)): # settingsをDIで受け取る
    return OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_user_from_token_payload(
    payload: dict, db: AsyncSession, settings: Settings # settingsも引数で受け取る
) -> Optional[UserModel]:
    try:
        token_data = TokenPayload(**payload)
        if token_data.exp is None or token_data.exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        if token_data.sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # リポジトリを使う場合
    # user_repo = UserRepository()
    # user_repo.set_session(db)
    # user = await user_repo.get(int(token_data.sub))

    # 直接DBアクセスする場合 (リポジトリパターンからは逸脱するが、認証専用なら許容も)
    from sqlalchemy.future import select
    user = (await db.execute(select(UserModel).where(UserModel.id == int(token_data.sub)))).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_from_token(
    token: Annotated[str, Depends(get_oauth2_scheme)], # oauth2_schemeをDependsで取得
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)] # settingsをDIで取得
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = await get_user_from_token_payload(payload, db, settings) # settingsを渡す
        if user is None: # get_user_from_token_payloadが例外を出すので不要かもしれない
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# パスワード複雑性チェック (UserServiceへ移動、またはここで共有ヘルパーとして定義)
import re
def check_password_complexity(password: str) -> bool:
    if len(password) < 8: return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"\d", password): return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False
    return True
```

### 8.2 認証APIエンドポイント
ユーザー認証とトークン発行を行う `/auth/login` エンドポイント。

**`app/routers/auth_router.py` (アプリケーション側で定義する例):**
```python
# app/routers/auth_router.py (または libkoiki/api/routers/auth.py)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from libkoiki.schemas.token import Token
from libkoiki.services.user_service import UserService # UserServiceDepを使うか直接注入
from libkoiki.auth.jwt import create_access_token
from libkoiki.core.config import Settings, get_settings
from libkoiki.api.dependencies import DBSessionDep, UserServiceDep # 共通の依存性

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSessionDep,
    user_service: UserServiceDep, # サービスを注入
    settings: Annotated[Settings, Depends(get_settings)] # settingsをDIで取得
):
    user = await user_service.authenticate_user(email=form_data.username, password=form_data.password, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token = create_access_token(subject=user.id, settings=settings) # settingsを渡す
    return {"access_token": access_token, "token_type": "bearer"}
```

### 8.3 ロールベースアクセス制御 (RBAC)
ユーザーにロールを割り当て、ロールに権限を紐付けることでアクセス制御を行います。
詳細は [15. ロールと権限](#15-ロールと権限) を参照。

---

## 09. 非同期処理（Celery & Redis）

非同期処理とは、「ユーザーの待ち時間を減らす」ために、重い処理を裏で行う仕組みです。

### 🔰 用語解説

- **非同期処理**: ユーザーが待たずに操作できるように、裏側で別スレッドやプロセスで処理を実行する仕組み。Webアプリケーションでは、メール送信や重い計算処理を非同期で行うことで応答性を保ちます。
- **Celery**: Pythonで定番の非同期タスクキューライブラリ。
- **Redis**: Celeryと連携し、タスクの待ち行列を管理する役割を担う高速なインメモリデータストア。

### 9.1 Celeryによる非同期タスク
時間のかかる処理（メール送信、レポート生成など）をバックグラウンドで実行します。

**`libkoiki/tasks/celery_app.py`:**
```python
# libkoiki/tasks/celery_app.py
from celery import Celery
from libkoiki.core.config import get_settings # get_settings() 経由で取得

settings = get_settings()

celery_app = None
if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    celery_app = Celery(
        "worker", # Celeryアプリケーション名
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        # include=['libkoiki.tasks.example_task', 'app.tasks.my_app_task'] # タスクモジュールをリストで指定
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
else:
    print("Celery broker or backend URL not configured. Celery tasks disabled.")

# @celery_app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(10.0, some_task.s('hello'), name='add every 10')
```

**`libkoiki/tasks/example_task.py` (共通タスク例):**
```python
# libkoiki/tasks/example_task.py
from libkoiki.tasks.celery_app import celery_app # celery_appインスタンスをインポート
from libkoiki.core.logging import get_logger

logger = get_logger(__name__)

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

```
アプリケーション固有のタスクは `app/tasks/` に配置します。
`app/tasks/__init__.py` を作成し、`app.tasks.your_task_module` のようにCeleryが検出できるようにします。

### 9.2 イベントシステム (オプション)
Redis Pub/Sub を利用したシンプルなイベント駆動アーキテクチャを構築することも可能です。
サービス層でビジネスイベントを発行し、別のコンポーネント（イベントハンドラ）がそれを購読して非同期に処理します。
v0.2 の `src/events/` ディレクトリの実装 (EventPublisher, EventHandler) は、必要に応じて `libkoiki/events/` として導入できます。

### 9.3 Celeryの本番運用に関する考慮事項
- **リトライ戦略**: タスク失敗時の自動リトライ（`autoretry_for`, `retry_kwargs`, `max_retries`など）。
- **監視**: Flowerなどのツールでタスクの実行状況、キューの長さを監視。Prometheusと連携してメトリクス収集。
- **ワーカ管理**: SupervisorやSystemdでワーカプロセスをデーモン化し、自動再起動を設定。負荷に応じたワーカ数の調整（スケーリング）。
- **デッドレターキュー**: 処理に失敗し続けるタスクを隔離する仕組み。
- **冪等性**: タスクが複数回実行されても問題ないように設計（特にリトライ時）。
- **タスクの分割**: 長時間実行されるタスクは、小さなサブタスクに分割することを検討。
- **結果バックエンド**: 結果が不要なタスクではバックエンド設定を省略してパフォーマンス向上。必要な場合でも、結果のTTLを設定してRedisのメモリを圧迫しないようにする。

---

## 10. アプリケーション実装例と起動方法 (app/)

このセクションでは、`libkoiki` フレームワークを利用して、具体的なアプリケーション (`app/` ディレクトリ以下) をどのように構築するかの例として、シンプルなToDo管理APIを示します。

### 10.1 app/main.py
アプリケーションのエントリポイント。FastAPIインスタンスの初期化、ミドルウェアの設定、ルーターの登録などを行います。

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler # slowapi のデフォルトハンドラ
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as aioredis # redis.asyncio をインポート

from libkoiki.core.config import get_settings, Settings
from libkoiki.core.logging import setup_logging, get_logger
from libkoiki.core.error_handlers import setup_exception_handlers
from libkoiki.db.session import connect_db, disconnect_db
# from libkoiki.core.monitoring import setup_monitoring # Prometheus使う場合
# from libkoiki.core.middleware import SecurityHeadersMiddleware, AuditLogMiddleware # 必要なら

# アプリケーション固有のルーターをインポート
from app.routers import todo_router # ToDoルーター
from app.routers import auth_router # 認証ルーター (libkoiki側ではなくapp側で定義する場合)

logger = get_logger(__name__) # ロガーを取得
settings_instance = get_settings() # 設定インスタンスを取得 (mainモジュールレベルで一度取得)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- アプリケーション起動時 ---
    # logging.pyから直接settingsを参照しないように、引数で渡す
    setup_logging(
        log_level_str=settings_instance.LOG_LEVEL,
        app_env=settings_instance.APP_ENV,
        debug=settings_instance.DEBUG
    )
    logger.info(f"Starting application: {settings_instance.APP_NAME} in {settings_instance.APP_ENV} mode")

    await connect_db() # DB接続確認

    # Redisクライアント初期化 (レートリミット、キャッシュ、Pub/Sub用)
    if settings_instance.REDIS_URL:
        try:
            # aioredis.from_url は aioredis.Redis.from_url に変更されている場合がある
            app.state.redis = aioredis.Redis.from_url(settings_instance.REDIS_URL, encoding="utf-8", decode_responses=True)
            await app.state.redis.ping() # 接続確認
            logger.info("Redis connection successful.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}", exc_info=True)
            app.state.redis = None # 失敗した場合はNoneに設定
    else:
        app.state.redis = None
        logger.warning("Redis URL not configured. Redis client not initialized.")


    # レートリミッター初期化
    if settings_instance.RATE_LIMIT_ENABLED:
        # Redisが利用可能ならRedisストレージを使う
        storage_uri = settings_instance.REDIS_URL if app.state.redis else None # Redis URLをストレージURIとして使用
        limiter = Limiter(
            key_func=get_remote_address,
            enabled=True, # settings_instance.RATE_LIMIT_ENABLED を直接使う
            default_limits=[settings_instance.RATE_LIMIT_DEFAULT],
            strategy=settings_instance.RATE_LIMIT_STRATEGY,
            storage_uri=storage_uri # Redis URLを渡す
        )
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # slowapiデフォルトハンドラ
        # グローバルに適用する場合はミドルウェアも追加
        # app.add_middleware(SlowAPIMiddleware) # これを使う場合、limiterはstateから自動で取得される
        logger.info(f"Rate limiter initialized (Storage: {'Redis' if storage_uri else 'memory'}).")
    else:
        app.state.limiter = Limiter(key_func=get_remote_address, enabled=False) # 明示的に無効化
        logger.info("Rate limiter disabled.")

    # setup_monitoring(app) # Prometheusメトリクス設定 (有効にする場合)

    yield # アプリケーション実行

    # --- アプリケーション終了時 ---
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed.")
    await disconnect_db()
    logger.info("Application shutdown.")

app = FastAPI(
    title=settings_instance.APP_NAME,
    debug=settings_instance.DEBUG,
    lifespan=lifespan # lifespanコンテキストマネージャを登録
)

# グローバル例外ハンドラー設定
setup_exception_handlers(app)

# ミドルウェア設定
# from libkoiki.core.middleware import AuditLogMiddleware, SecurityHeadersMiddleware # インポート
# app.add_middleware(AuditLogMiddleware) # 監査ログ (DBアクセスに注意)
# app.add_middleware(SecurityHeadersMiddleware) # セキュリティヘッダ
if settings_instance.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings_instance.BACKEND_CORS_ORIGINS], # 文字列リストに
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーター登録
app.include_router(auth_router.router, prefix=settings_instance.API_PREFIX) # 認証ルーター
app.include_router(todo_router.router, prefix=f"{settings_instance.API_PREFIX}/todos", tags=["Todos"]) # ToDoルーター

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "Application is healthy"}

# Celeryを使う場合、celery_appをFastAPIインスタンスから参照できるようにする (オプション)
# from libkoiki.tasks.celery_app import celery_app as koiki_celery_app
# app.state.celery_app = koiki_celery_app

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

from libkoiki.api.dependencies import DBSessionDep, ActiveUserDep # 共通の依存性
from libkoiki.models.user import UserModel # UserModelをインポート

from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema, TodoResponseSchema
from app.services.todo_service import TodoService # アプリケーション固有のサービス
from app.api.dependencies import get_todo_service # アプリケーション固有のDI

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

from libkoiki.core.transaction import transactional
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException # 使用する場合はインポート
from app.repositories.todo_repository import TodoRepository
from app.models.todo_model import TodoModel
from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema

class TodoService:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    @transactional
    async def create_todo(self, todo_data: TodoCreateSchema, db: AsyncSession, owner_id: int) -> TodoModel:
        self.repository.set_session(db)
        # owner_idをTodoModelのコンストラクタに渡す
        todo = TodoModel(**todo_data.dict(), owner_id=owner_id)
        return await self.repository.create(todo)

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
            return None # ルーターで404処理
        if todo.owner_id != owner_id:
            return None # ルーターで404または403処理
        return todo

    @transactional
    async def update_todo(
        self, todo_id: int, todo_data: TodoUpdateSchema, db: AsyncSession, owner_id: int
    ) -> Optional[TodoModel]:
        self.repository.set_session(db)
        todo = await self.repository.get(todo_id) # まず取得
        if not todo:
            return None
        if todo.owner_id != owner_id: # 所有者チェック
            return None # Not authorized
        
        update_data = todo_data.dict(exclude_unset=True)
        return await self.repository.update(todo, update_data) # 取得したオブジェクトを更新

    @transactional
    async def delete_todo(self, todo_id: int, db: AsyncSession, owner_id: int) -> bool:
        self.repository.set_session(db)
        todo = await self.repository.get(todo_id) # まず取得
        if not todo:
            return False
        if todo.owner_id != owner_id: # 所有者チェック
            return False # Not authorized
        
        await self.repository.delete(todo_id) # IDで削除 (deleteメソッドの実装による)
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

### 10.5 app/models/todo_model.py
ToDoのデータベースモデルを定義します。`libkoiki`の`Base`を継承します。

```python
# app/models/todo_model.py
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base # libkoikiのBaseをインポート
# from libkoiki.models.user import UserModel # 循環参照を避けるため、型ヒントは文字列で

class TodoModel(Base): # libkoikiのBaseを継承
    # __tablename__ = "todos" # CustomBaseで自動設定される

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    
    # UserModelの主キーを参照する外部キー
    # テーブル名はUserModelの__tablename__ (小文字のスネークケース) に合わせる
    owner_id = Column(Integer, ForeignKey("usermodel.id")) # "usermodel" はUserModelのテーブル名

    # UserModel側にもリレーションシップを定義する必要がある
    # owner = relationship("UserModel", back_populates="todos")
```
**注意:** `libkoiki/models/user.py` の `UserModel` にも `todos = relationship("TodoModel", back_populates="owner")` のようなリレーション定義が必要です (双方向リレーションの場合)。`TodoModel` は `app` 側にあるため、`libkoiki` 側から直接インポートするのは避けるべきです。この場合、`"app.models.todo_model.TodoModel"` のように完全修飾名で指定するか、`back_populates` のみで片方向リレーションにするか、リレーションを `app` 側で動的に設定するなどの工夫が必要です。ここでは、`TodoModel` から `UserModel` への片方向参照のみを示しています。

### 10.6 app/schemas/todo_schema.py
ToDoのPydanticスキーマを定義します。

```python
# app/schemas/todo_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TodoBaseSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="ToDoのタイトル")
    description: Optional[str] = Field(None, max_length=500, description="ToDoの詳細説明")

class TodoCreateSchema(TodoBaseSchema):
    pass # 基本的にBaseと同じだが、作成時特有のフィールドがあれば追加

class TodoUpdateSchema(BaseModel): # 更新時は全フィールドオプショナルが一般的
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

class TodoResponseSchema(TodoBaseSchema):
    id: int
    completed: bool
    owner_id: int # どのユーザーのToDoかを示す
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # SQLAlchemyモデルインスタンスからの変換を許可
```

### 10.7 app/api/dependencies.py (アプリケーション固有の依存性)
アプリケーション固有の依存性（DI）を定義します。

```python
# app/api/dependencies.py
from typing import Annotated
from fastapi import Depends

from app.services.todo_service import TodoService
from app.repositories.todo_repository import TodoRepository

def get_todo_repository() -> TodoRepository:
    """ToDoリポジトリのインスタンスを返す依存性関数。"""
    return TodoRepository()

def get_todo_service(
    # リポジトリをDIで注入
    repo: Annotated[TodoRepository, Depends(get_todo_repository)]
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
# __init__.py で Base を公開し、各モデルをインポートしているなら、それで足りる場合もある
import libkoiki.models.user # 例
import libkoiki.models.role # 例
import libkoiki.models.permission # 例
import libkoiki.models.associations # 例

# app のモデルをインポートしてAlembicに認識させる
import app.models.todo_model # 例

# target_metadata の設定
# libkoiki と app で同じ Base インスタンスを共有している場合は、どちらか一方でよい
# from libkoiki.db.base import Base
# target_metadata = Base.metadata
# または、それぞれの metadata を結合する (より複雑)
# ここでは、上記のようにモデルをインポートすることで、
# それぞれのモデルが自身のBase.metadataに登録されることを期待する。
# Alembicは最終的に target_metadata = None のまま、
# context.configure() に渡す target_metadata を動的に設定する。
# config.set_main_option("sqlalchemy.url", settings.DATABASE_URL) の settings.DATABASE_URL は同期URL (postgresql://...) にする必要がある。
# ...

# run_migrations_online 関数の target_metadata 設定箇所
# from libkoiki.db.base import Base as LibKoikiBase # libkoikiのBase
# from app.models.todo_model import Base as AppBase # appのBase
# metadata_list = [LibKoikiBase.metadata, AppBase.metadata] # もしBaseが別なら
# target_metadata = LibKoikiBase.metadata # もしBaseが共通なら
# context.configure(connection=connection, target_metadata=target_metadata)
# ↓
from libkoiki.db.base import Base # プロジェクトで共有されるBaseインスタンス
target_metadata = Base.metadata
# ...
```
Alembicが正しく動作するためには、`alembic.ini` の `sqlalchemy.url` が設定されていること、そして `env.py` 内で `target_metadata` が全てのテーブルを含むように設定されることが重要です。
`libkoiki.db.base.Base` が `app` 側でも共通して使われていれば、`target_metadata = Base.metadata` で問題ありません。

マイグレーションコマンド:
- `alembic revision --autogenerate -m "create_todos_table"`
- `alembic upgrade head`

### 10.9 起動方法

```bash
# 依存関係インストール (プロジェクトルートで)
# pip install -r requirements.txt (もしあれば)
# poetry install (poetry を使用している場合)
# pip install ".[dev]" (pyproject.tomlにdev依存がある場合)

# .envファイル作成 (プロジェクトルートに.env.exampleをコピーして編集)
# SECRET_KEY を必ず設定！
# cp .env.example .env
# nano .env # または任意のエディタで編集

# DBマイグレーション (データベースが起動していること)
alembic upgrade head

# FastAPIアプリケーション起動 (プロジェクトルートから)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker 起動 (プロジェクトルートから、Celery設定が有効な場合)
# .envファイルで CELERY_BROKER_URL と CELERY_RESULT_BACKEND を設定しておくこと
# 例: celery -A libkoiki.tasks.celery_app worker --loglevel=info
# autodiscover_tasks を使用している場合、-A オプションの指定はcelery_appインスタンスを持つモジュール
# (例: libkoiki.tasks.celery_app または app.main (もしそこでcelery_appをインポート・設定している場合))
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
from typing import Optional # Optionalをインポート

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

from libkoiki.core.exceptions import BaseAppException, ResourceNotFoundException, ValidationException as BusinessValidationException
from libkoiki.core.logging import get_logger # get_loggerをインポート

logger = get_logger(__name__) # ロガーを取得

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

# slowapiのデフォルトハンドラ (_rate_limit_exceeded_handler) を使う場合は、このカスタムハンドラは不要
# async def rate_limit_exception_handler_custom(request: Request, exc: RateLimitExceeded):
#     logger.warning(f"Rate Limit Exceeded for {request.client.host if request.client else 'unknown'}: {exc.detail}", extra={"client_host": request.client.host if request.client else 'unknown_client', "path": str(request.url)})
#     response = JSONResponse(
#          {"detail": f"Rate limit exceeded: {exc.detail}", "error_code": "RATE_LIMIT_EXCEEDED"},
#          status_code=status.HTTP_429_TOO_MANY_REQUESTS
#     )
#     # slowapiの prepare_response を呼び出してヘッダーなどを付与する場合
#     # response = await exc.limiting_strategy.prepare_response(response, exc, request, exc.limiter) # Limiterインスタンスが必要
#     return response

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
    # RateLimitExceeded は app.main の lifespan で slowapi の _rate_limit_exceeded_handler を登録することが多い
    # app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler_custom) # カスタムする場合
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
from structlog.types import Processor # Processorをインポート
from typing import Optional # Optionalをインポート

# from libkoiki.core.config import get_settings # 循環参照を避けるため直接は使わない

# settings = get_settings() # グローバルインスタンスは避ける

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

def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger: # 返り値の型を明示
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
`app/main.py` の `lifespan` 内で `setup_logging(settings_instance.LOG_LEVEL, settings_instance.APP_ENV, settings_instance.DEBUG)` のように呼び出します。

### 12.2 監査ログ
セキュリティ上重要な操作を記録します。ミドルウェアで基本的な情報を記録し、サービス層で詳細情報を補足できます。

**`libkoiki/core/middleware.py` に監査ログミドルウェアの例:**
```python
# libkoiki/core/middleware.py
import time
import json # jsonをインポート
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from datetime import datetime, timezone # timezone をインポート
import structlog

# from libkoiki.auth.jwt import get_current_user_from_token_if_present # トークンからユーザー情報を安全に取得する関数(要実装)
# from libkoiki.db.session import get_db_session # DBセッションが必要な場合

# 監査ログ専用のロガーを取得 (logging.pyで設定されていれば同じ設定が使われる)
# もし監査ログを別ファイルなどに出力したい場合は、logging.pyで専用のハンドラとフォーマッタを設定する
audit_logger = structlog.get_logger("koiki.audit") # "koiki.audit"など専用名が良い

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # ユーザー情報の取得 (例: トークンからユーザーIDをデコード)
        # 注意: ここでのDBアクセスはパフォーマンスに影響する可能性があるため、
        # トークンペイロードのデコードのみで済む情報（user_idなど）に留めるか、
        # リクエストコンテキストを通じて他の場所で取得した情報を利用するなどの工夫が必要。
        user_id: Optional[str] = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1]
            try:
                # ここではJWTライブラリを使ってデコードする例（簡易版）
                # 実際は libkoiki.auth.jwt の関数を使うべき
                from jose import jwt
                from libkoiki.core.config import get_settings # settings取得
                settings = get_settings()
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}) # 有効期限切れでもIDは取る例
                user_id = payload.get("sub")
            except Exception: # jwt.ExpiredSignatureError, JWTErrorなど
                user_id = "invalid_token" # またはNone

        response = await call_next(request) # 次の処理（エンドポイント実行など）
        process_time_ms = (time.time() - start_time) * 1000

        log_entry = {
            "event_type": "api_request", # 監査ログの種別
            "timestamp": datetime.now(timezone.utc).isoformat(), # ISO形式のタイムスタンプ
            "client_ip": request.client.host if request.client else "unknown_ip",
            "user_id": user_id, # 取得できればユーザーID
            "http_method": request.method,
            "http_path": request.url.path,
            "http_query_params": str(request.query_params) if request.query_params else None,
            "http_status_code": response.status_code,
            "outcome": "success" if 200 <= response.status_code < 400 else "failure",
            "duration_ms": int(process_time_ms),
            "user_agent": request.headers.get("User-Agent"),
            "request_id": request.headers.get("X-Request-ID"), # もしあれば
        }
        
        # リクエスト/レスポンスボディのログ記録はデータ量と機密性に注意して選択的に行う
        # if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
        #     try:
        #         req_body_bytes = await request.body()
        #         # request.stream() を消費すると後続処理で読めなくなるため、再度ストリームを生成する
        #         request._stream = lambda: asyncio.BytesIO(req_body_bytes)
        #         if req_body_bytes: # 機密情報はマスキング処理が必要
        #             log_entry["request_body_preview"] = json.loads(req_body_bytes.decode())[:1024] # 先頭1KBなど
        #     except Exception:
        #         log_entry["request_body_preview"] = "[Failed to parse or too large]"

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
from prometheus_fastapi_instrumentator import Instrumentator # Instrumentatorをインポート
# from prometheus_client import Counter # カスタムメトリクス用 (例)

# カスタムメトリクスの例 (必要に応じて定義)
# user_creations_total = Counter(
#     "koiki_user_creations_total", # メトリクス名 (プレフィックスを付けると良い)
#     "Total number of users created through the API."
# )

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
    
    # カスタムメトリクスを登録したい場合はここで行う
    # 例: instrumentator.add(some_custom_metric_function)
    # または、グローバルに定義したCounterなどを直接インクリメントする
    # (例: ユーザー作成サービス内で user_creations_total.inc())

    # FastAPIのロガーを取得して、モニタリング設定完了をログに出力
    from libkoiki.core.logging import get_logger
    logger = get_logger(__name__)
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

### 🔰 用語解説 (セキュリティ一般)

- **セキュリティ**: アプリケーションを不正アクセスやデータ漏洩から守るための技術全般。
- **レートリミット**: 一定時間内に許可されるAPIリクエスト数を制限し、総当たり攻撃やDoS攻撃を防ぐ。
- **セキュリティヘッダ**: ブラウザのセキュリティ機能を有効化し、XSSやクリックジャッキングなどの攻撃を緩和するHTTPレスポンスヘッダ。
- **入力バリデーション**: 不正な入力データによる脆弱性を防ぐため、入力値を検証・無害化すること。

### 13.1 レートリミット (slowapi)
`slowapi` を使用してAPIエンドポイントへのリクエスト数を制限します。

- **設定**: `app/main.py` の `lifespan` 内で `Limiter` を初期化し、`app.state.limiter` に格納。Redisをストレージとして使用推奨。
- **適用**:
    - グローバル: `app.add_middleware(SlowAPIMiddleware)` (Limiterはstateから取得)。
    - エンドポイントごと: `Depends(RateLimitDep("5/minute"))` (`RateLimitDep` は `libkoiki.api.dependencies` で `LimiterDep` を使って定義)。
- **例外処理**: `RateLimitExceeded` をグローバル例外ハンドラで処理 (通常は `slowapi` のデフォルトハンドラを使用)。

(実装例は `app/main.py` の `lifespan` および `libkoiki/api/dependencies.py` の `LimiterDep` を参照)

### 13.2 セキュリティヘッダ
ミドルウェアを使用してHTTPレスポンスにセキュリティ関連ヘッダを追加します。

**`libkoiki/core/middleware.py` に `SecurityHeadersMiddleware` の例:**
```python
# libkoiki/core/middleware.py
# (AuditLogMiddleware と同じファイル内でも良い)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

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
        
        # X-XSS-Protection は現代のブラウザでは非推奨 (CSPで代替)
        # response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
```
`app/main.py` で `app.add_middleware(SecurityHeadersMiddleware)` として登録。CSPの設定は特に注意が必要で、フロントエンドの構成や使用する外部リソースによって細かく調整する必要があります。

### 13.3 入力バリデーション
- **Pydantic**: API層での型チェックと形式検証（メールアドレス、URL、数値範囲など）。スキーマ定義で `Field` を使って詳細なバリデーションルール（最小/最大長、正規表現など）を指定可能。
- **サービス層**: ビジネスルールに基づいたより複雑な検証（例: 関連データの存在チェック、状態遷移の妥当性）。カスタム例外 (`ValidationException`) を使用してエラーを通知。
- **サニタイズ**:
    - **SQLインジェクション**: SQLAlchemyなどのORMは、パラメータ化クエリ（プリペアドステートメント）を内部で使用するため、適切に使用されていれば基本的に安全です。生のSQL文字列を組み立てる場合は細心の注意が必要です。
    - **XSS (クロスサイトスクリプティング)**:
        - APIレスポンスとしてJSONを返す場合は、クライアント側（フロントエンド）がHTMLにデータを埋め込む際の処理が重要です。React, VueなどのモダンなフレームワークはデフォルトでXSS対策が施されています。
        - サーバーサイドでHTMLを生成する場合（Jinja2など）、テンプレートエンジンが提供する自動エスケープ機能を必ず有効にします。
    - **その他**: ファイルアップロード時のファイル名や種類、外部コマンド実行時の引数など、ユーザー入力を元にする場合は常に検証と無害化を意識します。

### 🔰 用語解説 (パスワードセキュリティ)

- **パスワードポリシー**: 安全なパスワード設定をユーザーに強制するための規則群（長さ、文字種など）。
- **ハッシュ化**: パスワードを元の値に戻せない（または極めて困難な）一方向関数で変換すること。保存時は必ずハッシュ化されたパスワードを格納する。`bcrypt` や `argon2` が推奨されるアルゴリズム。
- **ソルト**: ハッシュ化の際にパスワード毎に付加されるランダムなデータ。同じパスワードでも異なるハッシュ値が生成され、レインボーテーブル攻撃への耐性を高める。`passlib` は自動でソルトを扱います。

### 13.4 パスワードポリシー
安全なパスワード設定を強制します。

- **実装**: パスワード設定・変更APIを受け付けるサービス層 (`UserService`) でポリシーをチェックします。
- **ヘルパー関数**: `libkoiki/auth/jwt.py` の `check_password_complexity` で基本的な複雑性（長さ、文字種）をチェック。
- **ポリシー例**:
    - 最小文字数（例: 12文字以上を推奨）
    - 文字種（大文字、小文字、数字、記号をそれぞれ1つ以上含む）
    - よく使われるパスワードの禁止（辞書攻撃対策、Have I Been Pwned API連携など）
    - パスワード履歴（過去N回のパスワードの再利用禁止）
    - アカウントロックアウト（ログイン試行回数制限を超えた場合に一時的にアカウントをロック）
- **フレームワーク提供**: 基本的な文字種と長さのチェックを提供。より高度なポリシー（辞書チェック、履歴管理など）はプロジェクト要件に応じて追加実装が必要です。

(実装例は `libkoiki/auth/jwt.py` および `libkoiki/services/user_service.py` を参照)

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
from typing import AsyncGenerator, Generator # Generatorをインポート
import pytest
import pytest_asyncio # pytest-asyncio をインポート
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool # テストではNullPoolを使うことが多い

from libkoiki.core.config import get_settings, Settings
from libkoiki.db.base import Base as CombinedBase # libkoikiとappで共有されるBase
from app.main import app # FastAPIアプリケーションインスタンス
from libkoiki.db.session import get_db_session # DI用のDBセッション取得関数

# テスト用のDB URL (環境変数やテスト専用設定ファイルから取得推奨)
# settings_instance = get_settings() # ここで取得すると他のテストに影響する可能性があるので注意
# TEST_DATABASE_URL = getattr(settings_instance, "TEST_DATABASE_URL", None) or \
#                     settings_instance.DATABASE_URL.replace("_db", "_test_db") if settings_instance.DATABASE_URL else \
#                     "postgresql+asyncpg://test_user:test_password@localhost:5433/test_koiki_db" # ポートも変えるなど

# ここでは固定値とするが、実際は環境変数などで上書きできるようにする
DEFAULT_TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/koiki_test_db"

# --- Pytest Event Loop (pytest-asyncio v0.19.0以降は不要なことが多い) ---
# @pytest.fixture(scope="session")
# def event_loop(request) -> Generator[asyncio.AbstractEventLoop, None, None]:
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

# --- Database Fixtures ---
@pytest_asyncio.fixture(scope="session")
async def db_engine(event_loop): # event_loopフィクスチャを受け取る (pytest-asyncio < 0.19)
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
    
    # get_db_session 依存性をテスト用セッションでオーバーライドする関数
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # FastAPIアプリケーションの依存性をオーバーライド
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    # httpx.AsyncClient をアプリケーションインスタンスと共に初期化
    async with AsyncClient(app=app, base_url="http://testserver") as async_client: # base_urlは任意
        yield async_client
    
    # テスト終了後にオーバーライドを元に戻す (クリーンアップ)
    del app.dependency_overrides[get_db_session]

# --- 認証済みクライアントのフィクスチャ (オプション) ---
# from libkoiki.services.user_service import UserService # 実際のサービスを使用
# from libkoiki.repositories.user_repository import UserRepository
# from libkoiki.schemas.user import UserCreate
# from libkoiki.auth.jwt import create_access_token
#
# @pytest_asyncio.fixture(scope="function")
# async def authenticated_user(db_session: AsyncSession, settings: Settings): # settingsもDIで取得したい
#     """テスト用の認証済みユーザーを作成し、返すフィクスチャ。"""
#     # ここで settings を取得する方法を検討 (例: get_settings() を直接呼ぶか、別のフィクスチャ経由)
#     # current_settings = get_settings() # この例では直接呼び出す
#
#     user_repo = UserRepository() # リポジトリをインスタンス化
#     user_service = UserService(repository=user_repo) # サービスをインスタンス化
#     
#     test_user_email = "authtest@example.com"
#     test_user_password = "AuthTestP@sswOrd1!"
#     # 既存ユーザーがいれば削除または取得 (冪等性のため)
#     existing_user = await user_service.get_user_by_email(test_user_email, db_session)
#     if existing_user:
#         # 必要なら削除して再作成、またはそのまま利用
#         # await user_service.delete_user(existing_user.id, db_session)
#         return existing_user
#
#     user_data = UserCreate(email=test_user_email, password=test_user_password, full_name="Auth Test User")
#     user = await user_service.create_user(user_in=user_data, db=db_session)
#     return user
#
# @pytest_asyncio.fixture(scope="function")
# async def authenticated_client(client: AsyncClient, authenticated_user: UserModel):
#     """認証済みユーザーのトークンをヘッダーに設定したHTTPクライアントを返す。"""
#     current_settings = get_settings() # settings取得
#     token = create_access_token(subject=authenticated_user.id, settings=current_settings)
#     client.headers["Authorization"] = f"Bearer {token}"
#     yield client
#     # 後処理 (ヘッダー削除など)
#     del client.headers["Authorization"]
```

### 14.2 単体テスト例
サービス層のロジックなどを、依存性をモック化 (`unittest.mock.AsyncMock`) してテストします。

**`tests/unit/services/test_app_todo_service.py` の実装例:**
```python
# tests/unit/services/test_app_todo_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch # patchを追加
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.todo_service import TodoService
from app.repositories.todo_repository import TodoRepository # モック対象
from app.models.todo_model import TodoModel # 返り値の型として使用
from app.schemas.todo_schema import TodoCreateSchema, TodoUpdateSchema
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException # 例外のテスト用

@pytest.fixture
def mock_todo_repo() -> MagicMock: # 型ヒントを明確に
    repo = MagicMock(spec=TodoRepository) # specでメソッド存在チェック
    repo.set_session = MagicMock() # set_sessionもモック化
    repo.create = AsyncMock()      # DB操作メソッドはAsyncMock
    repo.get = AsyncMock()
    repo.get_multi_by_owner = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo

@pytest.fixture
def mock_db_session() -> AsyncMock: # 型ヒントを明確に
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
def todo_service(mock_todo_repo: TodoRepository) -> TodoService: # 型ヒント
    return TodoService(repository=mock_todo_repo)

@pytest.mark.asyncio
async def test_create_todo_success(
    todo_service: TodoService, 
    mock_todo_repo: MagicMock, # 型ヒント
    mock_db_session: AsyncMock  # 型ヒント
):
    """ToDo作成が成功するケースの単体テスト"""
    todo_data = TodoCreateSchema(title="Unit Test Todo", description="Test description")
    owner_id = 1
    
    # リポジトリのcreateメソッドが返すダミーのTodoModelインスタンス
    expected_created_todo = TodoModel(id=1, title=todo_data.title, description=todo_data.description, owner_id=owner_id, completed=False)
    mock_todo_repo.create.return_value = expected_created_todo

    # @transactional デコレータを考慮し、dbセッションを渡す
    # デコレータ内のロガーをモック化 (オプション)
    with patch('libkoiki.core.transaction.logger') as mock_transaction_logger:
        created_todo = await todo_service.create_todo(todo_data=todo_data, db=mock_db_session, owner_id=owner_id)

    assert created_todo is not None
    assert created_todo.id == 1
    assert created_todo.title == "Unit Test Todo"
    assert created_todo.owner_id == owner_id
    
    # リポジトリメソッドの呼び出し確認
    mock_todo_repo.set_session.assert_called_once_with(mock_db_session)
    mock_todo_repo.create.assert_called_once()
    # mock_transaction_logger.debug.assert_any_call("Starting transaction for create_todo") # ログ呼び出し確認

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

- **モック (Mock)**: テスト対象のコードが依存している外部コンポーネント（DB、外部APIなど）の振る舞いを模倣する偽のオブジェクト。これにより、依存関係を切り離してテスト対象のロジックのみを検証できる。`unittest.mock` ライブラリの `MagicMock` や `AsyncMock` を使用する。

### 14.3 統合テスト例
APIエンドポイントからDBまでを連携させてテストします。`client` フィクスチャを使用します。

**`tests/integration/api/test_app_todos_api.py` の実装例:**
```python
# tests/integration/api/test_app_todos_api.py
import pytest
from httpx import AsyncClient # AsyncClient をインポート
from fastapi import status   # HTTPステータスコード

from libkoiki.core.config import get_settings # API Prefix を使用するため
from libkoiki.models.user import UserModel    # テスト用ユーザー作成のため
from libkoiki.auth.jwt import create_access_token # テスト用トークン生成

# API Prefix を取得 (テスト実行時に設定が読み込まれる)
API_PREFIX = get_settings().API_PREFIX
TODO_API_BASE_URL = f"{API_PREFIX}/todos" # /api/v1/todos など

# --- Fixtures for this test module ---
@pytest.fixture(scope="module") # ユーザー作成はモジュールスコープで効率化
async def test_user(db_engine): # db_engineフィクスチャを使用して独立したセッションを作成
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from libkoiki.services.user_service import UserService
    from libkoiki.repositories.user_repository import UserRepository
    from libkoiki.schemas.user import UserCreate

    AsyncTestSession = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        async with session.begin(): # トランザクション管理
            user_repo = UserRepository()
            user_service = UserService(repository=user_repo)
            
            user_email = "todo_api_user@example.com"
            user_pass = "TestTodoP@ss1"
            
            existing_user = await user_service.get_user_by_email(user_email, session)
            if existing_user:
                # 冪等性のために既存ユーザーがいればそれを使うか、削除して再作成
                # ここでは簡単のため、既存ユーザーを返す
                return existing_user

            user_data = UserCreate(email=user_email, password=user_pass, full_name="Todo API Test User")
            user = await user_service.create_user(user_in=user_data, db=session)
            await session.commit() # ユーザー作成をコミット
            return user


@pytest.fixture
async def auth_headers(test_user: UserModel): # UserModelを受け取るように変更
    """認証済みユーザーのアクセストークンを含むヘッダーを返すフィクスチャ。"""
    current_settings = get_settings() # テスト実行時の設定を使用
    token = create_access_token(subject=test_user.id, settings=current_settings)
    return {"Authorization": f"Bearer {token}"}

# --- Integration Tests ---
@pytest.mark.asyncio
async def test_create_todo_api_success(client: AsyncClient, auth_headers: dict):
    """ToDo作成APIが正常に動作するケース (201 Created)"""
    todo_payload = {"title": "Integration Test My Todo", "description": "This is an integration test."}
    response = await client.post(TODO_API_BASE_URL + "/", json=todo_payload, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == todo_payload["title"]
    assert data["description"] == todo_payload["description"]
    assert "id" in data
    assert data["completed"] is False # デフォルト値の確認

@pytest.mark.asyncio
async def test_create_todo_api_unauthenticated(client: AsyncClient):
    """未認証でToDo作成APIを呼ぶとエラー (401 Unauthorized)"""
    todo_payload = {"title": "Unauthorized Todo"}
    response = await client.post(TODO_API_BASE_URL + "/", json=todo_payload) # auth_headersなし
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_my_todos_api_success(client: AsyncClient, auth_headers: dict, test_user: UserModel):
    """自分のToDo一覧を取得するAPIが正常に動作するケース"""
    # 事前にテストユーザーのToDoをいくつか作成 (このテスト専用)
    await client.post(TODO_API_BASE_URL + "/", json={"title": "My Todo Item 1"}, headers=auth_headers)
    await client.post(TODO_API_BASE_URL + "/", json={"title": "My Todo Item 2"}, headers=auth_headers)
    
    response = await client.get(TODO_API_BASE_URL + "/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    todos = response.json()
    assert isinstance(todos, list)
    assert len(todos) >= 2 # 少なくとも2つはあるはず
    for todo in todos:
        assert todo["owner_id"] == test_user.id # 自分のToDoのみが返されていることを確認

@pytest.mark.asyncio
async def test_get_todo_by_id_api_not_found_or_unauthorized(client: AsyncClient, auth_headers: dict):
    """存在しない、または他人のToDo IDで取得しようとするとエラー (404 Not Found)"""
    # このIDのToDoは存在しないか、他人のものであると仮定
    non_existent_todo_id = 99999 
    response = await client.get(f"{TODO_API_BASE_URL}/{non_existent_todo_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_my_todo_api_success(client: AsyncClient, auth_headers: dict):
    """自分のToDoを更新するAPIが正常に動作するケース"""
    # 1. 更新対象のToDoを作成
    create_response = await client.post(TODO_API_BASE_URL + "/", json={"title": "Todo Before Update"}, headers=auth_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    todo_id_to_update = create_response.json()["id"]

    # 2. ToDoを更新
    update_payload = {"title": "Todo After Update", "completed": True}
    update_response = await client.put(f"{TODO_API_BASE_URL}/{todo_id_to_update}", json=update_payload, headers=auth_headers)
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["title"] == update_payload["title"]
    assert updated_data["completed"] == update_payload["completed"]

@pytest.mark.asyncio
async def test_delete_my_todo_api_success(client: AsyncClient, auth_headers: dict):
    """自分のToDoを削除するAPIが正常に動作するケース"""
    # 1. 削除対象のToDoを作成
    create_response = await client.post(TODO_API_BASE_URL + "/", json={"title": "Todo To Be Deleted"}, headers=auth_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    todo_id_to_delete = create_response.json()["id"]

    # 2. ToDoを削除
    delete_response = await client.delete(f"{TODO_API_BASE_URL}/{todo_id_to_delete}", headers=auth_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT # 成功時はNo Content

    # 3. 削除されたことを確認 (GETで404になるはず)
    get_response_after_delete = await client.get(f"{TODO_API_BASE_URL}/{todo_id_to_delete}", headers=auth_headers)
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
from sqlalchemy import Column, String, Integer # Table, ForeignKeyはassociations.pyで使用
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
# roles = relationship(
# "RoleModel",
# secondary=user_roles_association,
# back_populates="users",
# lazy="selectin" # Eager loading strategy (optional, for performance)
# )
```
`lazy="selectin"` などのEager Loading戦略は、特に認証時にユーザーのロールや権限を頻繁に参照する場合にパフォーマンス改善に繋がることがあります。

### 15.2 権限チェックの実装
`libkoiki/api/dependencies.py` (または `libkoiki/auth/rbac.py`) で権限チェック用の依存性ヘルパーを定義します。

```python
# libkoiki/api/dependencies.py (または libkoiki/auth/rbac.py に分離推奨)
from typing import Annotated # Annotatedをインポート
from fastapi import Depends, HTTPException, status # 必要なものをインポート
from libkoiki.models.user import UserModel # ActiveUserDepで使用
# from libkoiki.api.dependencies import ActiveUserDep # 循環参照を避けるため、ActiveUserDepはここで定義しない想定
# ActiveUserDep は get_current_active_user から取得される

# 権限チェックのための依存性関数
def require_permission(required_permission: str):
    """
    指定された権限をユーザーが持っているか確認する依存性。
    持っていない場合はHTTP 403 Forbiddenを返す。
    """
    async def permission_checker(
        # ActiveUserDep は get_current_active_user で取得したユーザーを想定
        # get_current_active_user は get_current_user_from_token に依存し、
        # get_current_user_from_token 内でロールと権限をEager Loadingする必要がある。
        current_user: Annotated[UserModel, Depends(get_current_active_user)] # get_current_active_userを直接使用
    ):
        if not hasattr(current_user, 'roles') or not current_user.roles:
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: '{required_permission}'"
            )
        return current_user # 権限があればユーザーオブジェクトを返す (他の処理で使えるように)
    
    return Depends(permission_checker) # Dependsでラップして返す

# 使用例 (ルーターの dependencies 引数に指定)
# from libkoiki.api.dependencies import require_permission
# @router.post("/", dependencies=[require_permission("todos:create")])
# async def create_item(...):
#     ...
```
**重要:**
`get_current_user_from_token` (in `libkoiki/auth/jwt.py`) 内で、ユーザー取得時に `selectinload` を使って `roles` および `roles.permissions` リレーションをEager Loadingするように修正する必要があります。

**`libkoiki/auth/jwt.py` の `get_user_from_token_payload` 修正例:**
```python
# libkoiki/auth/jwt.py (get_user_from_token_payload 内のユーザー取得部分)
    # ... (token_data検証後)
    from sqlalchemy.orm import selectinload
    from libkoiki.models.role import RoleModel # RoleModelをインポート

    # user = (await db.execute(select(UserModel).where(UserModel.id == int(token_data.sub)))).scalar_one_or_none()
    # ↓ Eager loading を追加
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.roles).selectinload(RoleModel.permissions)
        )
        .where(UserModel.id == int(token_data.sub))
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    # ... (user is None のチェック)
```
これにより、`current_user` オブジェクトには既にロールと権限情報がロードされた状態で `require_permission` 依存性に渡されます。

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
*   **構成**: フロントエンドプロジェクトをバックエンドとは別のリポジトリ/ディレクトリで管理することが一般的。Docker Compose で統合して開発・デプロイ可能。
*   **認証**: API から取得した JWT をフロントエンドで安全に管理 (例: HttpOnly Cookie (SameSite属性に注意), localStorage + CSRF対策, セキュアな状態管理ライブラリ)。
*   **適した用途**: 動的でリッチなユーザーインターフェース、モバイルアプリとの API 共通化、複雑な状態管理が必要なアプリケーション。

### 16.2 サーバーサイドテンプレートエンジン (Jinja2など)

*   **特徴**: シンプルな構成、バックエンドとの連携が容易（特にPythonエコシステム内）、初期表示速度が速い傾向、SEO に有利な場合も。インタラクティブ性はSPAに劣ることがある。
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
*   **認証・認可の一貫性**: UIが異なっても、バックエンドAPIの認証・認可ロジックは共通して適用されるべき。UI側での表示制御と、API側での強制的なアクセス制御の両方が必要。
*   **CORS設定**: SPAなど異なるオリジンからAPIにアクセスする場合は、`app/main.py` でCORSMiddlewareを適切に設定する必要がある。
*   **設定の共通化と分離**: データベース接続情報など、UI層とAPI層で共通の設定が必要な場合でも、機密情報はUI層に直接埋め込まない。UI層はAPIエンドポイントのみを知り、必要な設定はAPI経由で取得するか、環境変数でUIのビルド時に注入する。
*   **開発・デプロイ**: 各層（バックエンドAPI、フロントエンドSPA、Streamlitアプリなど）を独立して開発・テスト・デプロイできる構成を目指す（Docker Compose、モノレポ戦略など）。
*   **状態管理**: 特にSPAでは、クライアント側の状態管理（ユーザー情報、UIの状態など）の戦略を早期に決定する。
*   **エラーハンドリング**: APIからのエラーレスポンスをUI側で適切にハンドリングし、ユーザーフレンドリーな形で表示する。

---

## 17. まとめ

KOIKI-FW v0.3 は、FastAPI をベースとしたエンタープライズ向けアプリケーション基盤を提供します。`libkoiki/` に共通機能を分離し、`app/` にアプリケーション固有ロジックを実装する構造を採用することで、再利用性と保守性を高めました。

**本フレームワークの活用により、開発者は以下のメリットを得られます:**

*   堅牢でスケーラブルなアプリケーションの迅速な構築。
*   標準化された構造によるコードの保守性と可読性の向上。
*   レイヤードアーキテクチャとDIによるテストの容易化と品質の確保。
*   JWT認証、RBAC、トランザクション管理、非同期処理（Celery）、構造化ロギング、Prometheusモニタリング、レートリミットなど、エンタープライズ用途で求められる多くの機能が組み込み済み、または容易に導入可能。
*   セキュリティと監視機能の組み込みによる運用負荷の軽減。

本ドキュメントを参考に、プロジェクトの要件に合わせて各コンポーネントをカスタマイズ・拡張し、効果的なアプリケーション開発を進めてください。

---

## 18. 今後の拡張・DDDへの布石

| 領域                      | 現構成 (`libkoiki`/`app`)                                  | 拡張方向 (DDD要素の導入)                                                                                                                              |
| :------------------------ | :--------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ドメインモデル**        | `models/` (主にORMモデルとしてデータ構造を定義)                  | `app/domain/models/` にドメインエンティティと値オブジェクトを明確に定義。永続化の詳細は意識せず、ビジネスルールと振る舞いを持つ。ORMモデルはインフラ層のデータマッパーとして利用。 |
| **リポジトリ**            | `repositories/` (具象クラス、データアクセスロジック)            | `app/domain/repositories/` にリポジトリインターフェース（抽象）を定義。具象クラスは `app/infrastructure/persistence/` などに配置し、DIで注入。ドメイン層はインターフェースにのみ依存。 |
| **アプリケーションサービス** | `services/` (ビジネスロジック、ユースケースが混在)             | `app/application/services/` または `app/application/use_cases/` としてユースケースを明確に分離。ドメインモデルとリポジトリを操作し、DTO（Data Transfer Object）でAPI層とやり取り。 |
| **ドメインサービス**        | (サービス層に暗黙的に含まれる可能性あり)                      | `app/domain/services/` に、特定のエンティティに属さないドメイン固有のロジックや、複数のエンティティを跨る複雑なビジネスルールを集約。                                               |
| **ドメインイベント**        | `tasks/` (Celeryタスクがイベントハンドラ的に使われることも)    | `app/domain/events/` にドメインイベントを定義。イベント発行（パブリッシュ）と購読（サブスクライブ）の仕組みを導入し、モジュール間の疎結合性を高める。Celeryはイベントハンドラや非同期処理の手段として活用。 |
| **API層 (コントローラ)**  | `routers/` (リクエスト処理、サービス呼び出し)                   | `app/interfaces/api/` (または `app/presentation/api/`) に配置。アプリケーションサービスの呼び出しと、HTTPリクエスト/レスポンスへの変換に責務を特化。                               |
| **スキーマ (DTO)**        | `schemas/` (Pydanticモデル、APIの入出力と内部利用が混在) | API層とアプリケーションサービス間のデータ転送に特化したDTOを `app/application/dtos/` に定義。ドメインモデルとPydanticスキーマの相互変換を明確にする。                                |

この拡張により、ドメインロジックの純粋性が高まり、テスト容易性、保守性、ビジネスの変化への追従性がさらに向上します。KOIKI-FWの現行アーキテクチャは、これらのDDDの概念を段階的に導入していくための良い出発点となります。

---

## おわりに

本バージョン（v0.3）は、`libkoiki` と `app` の分離を明確にし、ドキュメントと実装の同期を図りました。
これにより、導入チームや運用チームにおける習得性・保守性が大幅に向上し、より大規模な開発にも対応しやすくなっています。
初心者にも理解しやすい用語解説と、経験者にも役立つ技術詳細の両立を目指しました。
今後のフィードバックや改善提案を歓迎いたします。