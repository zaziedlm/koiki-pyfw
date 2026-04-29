# 🚀 KOIKI-FW セキュリティテスト - クイックガイド

**たった1コマンドでセキュリティAPIテストを実行**

## ⚡ 最速テスト実行（推奨）

```bash
# プロジェクトルートから一発実行
./ops/scripts/run_tests.sh test
```

## 🔄 従来の方法

```bash
# 環境起動
docker-compose up -d

# テスト実行
cd ops
bash scripts/security_test_manager.sh test
```

## 🎯 完全版（初回実行推奨）

```bash
# プロジェクトルートから（推奨）
./ops/scripts/run_tests.sh setup

# または従来の方法
docker-compose up -d

# ops ディレクトリに移動
cd ops

# セキュリティ環境セットアップ（権限・ロール・ユーザー作成）
bash scripts/security_test_manager.sh setup

# セキュリティAPIテスト実行
bash scripts/security_test_manager.sh test
```

## 🔍 何がテストされるのか？

- ✅ **認証システム**: 4つのテストユーザーでのログイン
- ✅ **権限制御**: ロール別のAPIアクセス権限
- ✅ **セキュリティAPI**: メトリクス取得・管理機能
- ✅ **ユーザー管理API**: ユーザー情報の参照権限
- ✅ **ToDo API**: 基本的なCRUD操作権限

## 👤 テストユーザー

| ユーザー | パスワード | 権限レベル | 主な機能 |
|----------|------------|------------|-----------|
| admin@example.com | admin123456 | システム管理者 | 全API（管理・セキュリティ・ユーザー・ToDo） |
| security@example.com | security123456 | セキュリティ管理 | セキュリティAPI（メトリクス管理） |
| user_admin@example.com | useradmin123456 | ユーザー管理 | ユーザー管理・ToDo API |
| user@example.com | testuser123456 | 一般ユーザー | ToDo APIのみ |

## 🛠 Windows ユーザー向け

### Git Bash / WSL の場合
```bash
# 上記と同じコマンドが使用可能
./ops/scripts/run_tests.sh test
```

### PowerShell の場合
```powershell
# PowerShell専用スクリプトを使用
cd ops
.\scripts\security_test_manager.ps1 test
```

## 📋 その他の便利コマンド

```bash
# ヘルプ表示
./ops/scripts/run_tests.sh help

# ログ確認
./ops/scripts/run_tests.sh logs

# 完全リセット（データ削除）
./ops/scripts/run_tests.sh reset

# 従来の方法（opsディレクトリから）
cd ops
bash scripts/security_test_manager.sh help
bash scripts/security_test_manager.sh db-check
```

## ⚠ トラブルシューティング

### エラーが発生した場合

1. **Docker環境の確認**
   ```bash
   docker-compose ps
   ```

2. **ログの確認**
   ```bash
   ./ops/scripts/run_tests.sh logs
   # または
   docker-compose logs app
   ```

3. **データベースリセット**
   ```bash
   ./ops/scripts/run_tests.sh reset
   ```

## 📚 詳細情報

- 詳細なテスト手順: `ops/README.md`
- API仕様: http://localhost:8000/docs （環境起動後）
- システム設計: `docs/design_kkfw_0.6.0.md`

---
**🎉 Happy Testing with KOIKI-FW!**
