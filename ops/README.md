# KOIKI-FW セキュリティ権限管理テスト環境

このディレクトリには、KOIKI-FWのセキュリティ監視APIおよび権限管理システムのテスト環境が含まれています。

現在のバックエンド正本は `components/libkoiki` と `components/koiki_ref_app` にあり、root `app/` は互換 wrapper として維持されています。`ops` 配下の手順はこの新構造を前提に読んでください。

## 📁 ディレクトリ構造

```
ops/
├── security/
│   └── roles_permissions.py         # 権限・ロール定義
├── scripts/
│   ├── setup_security.py            # セキュリティデータ初期化
│   ├── run_security_test.sh         # 統合テストスクリプト
│   ├── security_test_manager.sh     # Bash版管理スクリプト
│   ├── security_test_manager.ps1    # PowerShell版管理スクリプト
│   └── run_tests.sh                 # クロスプラットフォームランチャー
├── tests/
│   └── test_security_api.py         # APIテストスクリプト
└── README.md                        # このファイル
```

## 🚀 クイックスタート

### 🎯 最新の推奨方法

```bash
# プロジェクトルートから一発実行
./ops/scripts/run_tests.sh test

# 初回実行（セットアップ付き）
./ops/scripts/run_tests.sh setup
```

### 📋 従来の方法（opsディレクトリから）

```bash
# 1. Docker環境を起動（プロジェクトルートから）
cd /path/to/koiki-pyfw && docker-compose up -d

# 2. opsディレクトリに移動
cd ops

# 3. テスト実行
bash scripts/security_test_manager.sh test
```

### ワンライナー実行（従来）

```bash
# プロジェクトルートから一気に実行
docker-compose up -d && cd ops && bash scripts/security_test_manager.sh test
```

## ⚡ テスト実行方法（OS別）

### 🎯 推奨方法（全OS共通）
```bash
# プロジェクトルートから（最も簡単）
./ops/scripts/run_tests.sh test
```

### 📋 従来方法（OS別）

#### macOS / Linux
```bash
# 基本テスト
bash scripts/security_test_manager.sh test

# 完全セットアップ + テスト
bash scripts/security_test_manager.sh setup && bash scripts/security_test_manager.sh test
```

#### Windows (PowerShell)
```powershell
# 基本テスト
.\scripts\security_test_manager.ps1 test

# 完全セットアップ + テスト
.\scripts\security_test_manager.ps1 setup; .\scripts\security_test_manager.ps1 test
```

#### Windows (Git Bash / WSL)
```bash
# macOS/Linuxと同じ
bash scripts/security_test_manager.sh test
```

## 📋 利用可能なコマンド

| コマンド | 説明 |
|----------|------|
| `help` | ヘルプを表示 |
| `setup` | セキュリティ環境セットアップ |
| `test` | セキュリティAPIテスト実行 |
| `test-full` | 統合テスト実行 |
| `clean` | コンテナ停止 |
| `reset` | 完全リセット（データ削除） |
| `logs` | ログ確認 |
| `db-check` | データベース内容確認 |
| `manual-test` | 手動テスト用情報表示 |

## 🔧 実行例とコマンド対応表

### 🎯 推奨方法（プロジェクトルートから）

```bash
# ヘルプ表示
./ops/scripts/run_tests.sh help

# セキュリティ環境セットアップ（初回実行時）
./ops/scripts/run_tests.sh setup

# セキュリティAPIテスト実行
./ops/scripts/run_tests.sh test

# 統合テスト実行
./ops/scripts/run_tests.sh test-full
```

### 📋 従来方法（opsディレクトリから）

```bash
# ヘルプ表示
bash scripts/security_test_manager.sh help

# セキュリティ環境セットアップ（初回実行時）
bash scripts/security_test_manager.sh setup

# セキュリティAPIテスト実行
bash scripts/security_test_manager.sh test

# 統合テスト実行
bash scripts/security_test_manager.sh test-full
```

### 完全なコマンド対応表

| 目的 | 推奨方法（ルートから） | 従来方法（opsから） | Windows PowerShell | 説明 |
|------|---------------------|------------------|-------------------|------|
| ヘルプ | `./ops/scripts/run_tests.sh help` | `bash scripts/security_test_manager.sh help` | `.\scripts\security_test_manager.ps1 help` | 利用可能なコマンド表示 |
| セットアップ | `./ops/scripts/run_tests.sh setup` | `bash scripts/security_test_manager.sh setup` | `.\scripts\security_test_manager.ps1 setup` | 権限データとテストユーザー作成 |
| テスト実行 | `./ops/scripts/run_tests.sh test` | `bash scripts/security_test_manager.sh test` | `.\scripts\security_test_manager.ps1 test` | セキュリティAPIテスト |
| 統合テスト | `./ops/scripts/run_tests.sh test-full` | `bash scripts/security_test_manager.sh test-full` | `.\scripts\security_test_manager.ps1 test-full` | 全てのAPIテスト |
| ログ確認 | `./ops/scripts/run_tests.sh logs` | `bash scripts/security_test_manager.sh logs` | `.\scripts\security_test_manager.ps1 logs` | アプリケーションログ表示 |
| DB確認 | `./ops/scripts/run_tests.sh db-check` | `bash scripts/security_test_manager.sh db-check` | `.\scripts\security_test_manager.ps1 db-check` | データベース内容確認 |
| リセット | `./ops/scripts/run_tests.sh reset` | `bash scripts/security_test_manager.sh reset` | `.\scripts\security_test_manager.ps1 reset` | 全データ削除と再セットアップ |

## 🔧 従来のMakefileからの移行

従来のMakefileコマンドは以下のように置き換えられます：

```bash
# 従来 (Makefile)              # 新方式 (スクリプト)
make setup                   →  ./ops/scripts/run_tests.sh setup
make test                    →  ./ops/scripts/run_tests.sh test
make test-full              →  ./ops/scripts/run_tests.sh test-full
make clean                  →  ./ops/scripts/run_tests.sh clean
make reset                  →  ./ops/scripts/run_tests.sh reset
make logs                   →  ./ops/scripts/run_tests.sh logs
make db-check               →  ./ops/scripts/run_tests.sh db-check
make manual-test            →  ./ops/scripts/run_tests.sh manual-test
```

## 👤 テストユーザー

| Email | Username | Password | ロール | 権限 |
|-------|----------|----------|--------|------|
| admin@example.com | admin | admin123456 | system_admin | 全権限 |
| security@example.com | security | security123456 | security_admin | セキュリティ監視 |
| user_admin@example.com | useradmin | useradmin123456 | user_admin | ユーザー管理 |
| user@example.com | testuser | testuser123456 | todo_user | ToDo操作のみ |

## 🔑 権限システム

### 基本権限

- `read:security_metrics` - セキュリティメトリクス参照
- `manage:security_metrics` - セキュリティメトリクス管理
- `read:users` - ユーザー情報参照
- `write:users` - ユーザー情報編集
- `read:todos` - ToDo項目参照
- `write:todos` - ToDo項目編集
- `admin:system` - システム管理

### ロール定義

- **system_admin** - システム管理者（全権限）
- **security_admin** - セキュリティ管理者
- **user_admin** - ユーザー管理者
- **todo_user** - 一般ユーザー

## 🔗 テスト対象API

### セキュリティ監視API
- `GET /security/metrics` - メトリクス一覧
- `GET /security/metrics/authentication` - 認証メトリクス
- `GET /security/metrics/summary` - メトリクス要約
- `POST /security/metrics/reset` - メトリクスリセット
- `GET /security/health` - ヘルスチェック

### ユーザー管理API
- `GET /api/v1/users` - ユーザー一覧

## 📋 手動テスト手順

### 0. 初期セキュリティデータ投入

unified `prod` profile を使っている場合は、プロジェクトルートから次を実行します。

```powershell
.\start-docker.ps1 unified-prod
docker compose -f docker-compose.unified.yml --profile prod exec app-prod python ops/scripts/setup_security.py
```

投入内容を確認する例:

```powershell
docker compose -f docker-compose.unified.yml --profile prod exec db psql -U koiki_user -d koiki_todo_db -c "SELECT email, username, is_active, is_superuser FROM users ORDER BY email;"
```

通常の `docker-compose.yml` 構成を使っている場合は、従来どおり次を使います。

```powershell
docker-compose exec app python ops/scripts/setup_security.py
```

このスクリプトは `ops/security/roles_permissions.py` に定義されたテストユーザーを作り直します。

### 1. ログインとトークン取得

```bash
# 管理者でログイン
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123456"}'

# レスポンス例
# {"access_token": "eyJ...", "token_type": "bearer"}
```

### 2. セキュリティメトリクス取得

```bash
# トークンを使用してアクセス
curl -H "Authorization: Bearer <YOUR_TOKEN>" \
     http://localhost:8000/security/metrics
```

### 3. 権限テスト

```bash
# 一般ユーザーでログイン（権限不足）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testuser123456"}'

# セキュリティメトリクスにアクセス（403エラーになるはず）
curl -H "Authorization: Bearer <TESTUSER_TOKEN>" \
     http://localhost:8000/security/metrics
```

## 🐛 トラブルシューティング

### 1. セットアップ失敗時

```bash
# 通常 docker-compose.yml 構成のデータベースリセット
docker-compose down -v
docker-compose up -d

# セキュリティデータ再セットアップ
docker-compose exec app python ops/scripts/setup_security.py
```

unified `prod` profile の場合:

```powershell
.\start-docker.ps1 unified-prod-down
docker compose -f docker-compose.unified.yml --profile prod down -v
.\start-docker.ps1 unified-prod
docker compose -f docker-compose.unified.yml --profile prod exec app-prod python ops/scripts/setup_security.py
```

### 2. 権限データ確認

```bash
# 通常 docker-compose.yml 構成の権限一覧確認
docker-compose exec db psql -U koiki_user -d koiki_todo_db -c "
SELECT p.name, p.description, p.resource, p.action 
FROM permissions p ORDER BY p.name;
"

# ユーザーロール確認
docker-compose exec db psql -U koiki_user -d koiki_todo_db -c "
SELECT u.email, r.name as role_name, p.name as permission_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON r.id = ur.role_id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
ORDER BY u.email, p.name;
"
```

unified `prod` profile の場合は、`docker compose -f docker-compose.unified.yml --profile prod exec db ...` を使います。

### 3. API応答確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# セキュリティAPI ヘルスチェック
curl http://localhost:8000/security/health

# API仕様確認
curl http://localhost:8000/docs
```

## 📊 期待される結果

### 正常な権限制御

- **admin** - 全てのAPIにアクセス可能
- **security** - セキュリティメトリクスのみアクセス可能
- **useradmin** - ユーザー情報のみアクセス可能
- **testuser** - セキュリティAPI拒否（403エラー）

### テスト成功例

```
✅ admin (system_admin): アクセス許可 [HTTP 200]
✅ security (security_admin): アクセス許可 [HTTP 200]
🚫 useradmin (user_admin): アクセス拒否 [HTTP 403]
🚫 testuser (todo_user): アクセス拒否 [HTTP 403]
```

## 🔄 継続的な更新

権限やロールを追加する場合：

1. `ops/security/roles_permissions.py` を編集
2. unified `prod` では `docker compose -f docker-compose.unified.yml --profile prod exec app-prod python ops/scripts/setup_security.py` を実行
3. 通常 compose では `docker-compose exec app python ops/scripts/setup_security.py` を実行
4. `python ops/tests/test_security_api.py` またはコンテナ内の `ops/tests/test_security_api.py` でテスト

## 📞 サポート

問題が発生した場合は、以下を確認：

1. Docker環境の状態 (`docker compose -f docker-compose.unified.yml --profile prod ps` または `docker-compose ps`)
2. アプリケーションログ (`docker compose -f docker-compose.unified.yml --profile prod logs -f app-prod` または `docker-compose logs -f app`)
3. データベース接続 (`docker compose -f docker-compose.unified.yml --profile prod exec db psql...` または `docker-compose exec db psql...`)
4. セキュリティ設定 (権限・ロール・ユーザー)
