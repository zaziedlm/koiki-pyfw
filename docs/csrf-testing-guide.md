# CSRF検証テストガイド

## 概要
このガイドでは、KOIKI-FWフレームワークのCookie認証実装におけるCSRF（Cross-Site Request Forgery）保護機能をテストする方法を説明します。

## CSRF保護の仕組み

### Double Submit Cookie方式
本システムでは、以下のDouble Submit Cookie方式を採用しています：

1. **CSRFトークンの生成**: サーバーが32文字のランダムなCSRFトークンを生成
2. **クッキーへの保存**: CSRFトークンを`koiki_csrf_token`クッキーに保存
3. **HTTPヘッダーでの送信**: クライアントが`X-CSRF-Token`ヘッダーでトークンを送信
4. **サーバーでの検証**: クッキーの値とヘッダーの値が一致することを確認

### 保護対象エンドポイント
以下のエンドポイントでCSRF検証を実装済み：

- `POST /api/auth/login` - ログイン
- `POST /api/auth/register` - ユーザー登録
- `POST /api/auth/logout` - ログアウト
- `POST /api/auth/refresh` - トークンリフレッシュ
- `POST /api/todos` - Todo作成
- `PUT /api/todos/[id]` - Todo更新
- `DELETE /api/todos/[id]` - Todo削除

## テスト環境の準備

### 1. 必要なサービスの起動

```bash
# 1. バックエンドサーバーの起動（別ターミナル）
python main.py

# 2. フロントエンドサーバーの起動（別ターミナル）
cd frontend
npm run dev
```

### 2. テストユーザーの確認
テストには以下のユーザーアカウントを使用：
- Email: `user@example.com`
- Password: `testuser123456`

ユーザーが存在しない場合は、先にユーザー登録を行ってください。

## テスト方法

### 方法1: 自動テストスクリプト（推奨）

#### スクリプト実行
```bash
# 実行権限を付与（初回のみ）
chmod +x test_csrf.sh

# テスト実行
./test_csrf.sh
```

または

```bash
python3 ops/tests/test_csrf_validation.py
```

#### テスト内容
各エンドポイントに対して以下の4パターンをテスト：

1. **CSRFトークンなし** → `403 Forbidden`を期待
2. **正しいCSRFトークン** → `200 OK`を期待
3. **不正なCSRFトークン** → `403 Forbidden`を期待
4. **空のCSRFトークン** → `403 Forbidden`を期待

#### 期待される結果
```
🎯 テスト結果: 16/16 成功
🎉 全てのCSRF検証テストが成功しました！
🔒 CSRF保護が正しく動作しています。
```

### 方法2: 手動テスト（curlコマンド）

#### 1. CSRFトークンの取得
```bash
curl -c cookies.txt -b cookies.txt \
  -X GET "http://localhost:3000/api/auth/csrf"
```

#### 2. 正常なログイン（CSRFトークン付き）
```bash
# cookiesからCSRFトークンを取得してヘッダーに設定
CSRF_TOKEN=$(grep koiki_csrf_token cookies.txt | cut -f7)

curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -X POST "http://localhost:3000/api/auth/login" \
  -d '{"email":"user@example.com","password":"testuser123456"}'
```

#### 3. CSRF攻撃のシミュレーション（CSRFトークンなし）
```bash
curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:3000/api/auth/login" \
  -d '{"email":"user@example.com","password":"testuser123456"}'
```
→ `403 Forbidden`エラーが返されることを確認

#### 4. 不正なCSRFトークンでの攻撃
```bash
curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: invalid_token_here" \
  -X POST "http://localhost:3000/api/auth/login" \
  -d '{"email":"user@example.com","password":"testuser123456"}'
```
→ `403 Forbidden`エラーが返されることを確認

### 方法3: ブラウザ開発者ツール

#### 1. フロントエンドアプリケーションにアクセス
```
http://localhost:3000
```

#### 2. 開発者ツールでネットワークタブを開く
- F12 → Networkタブ

#### 3. ログイン操作を実行
- ログインフォームから正常ログイン
- ネットワークタブで以下を確認：
  - `POST /api/auth/login`リクエスト
  - `X-CSRF-Token`ヘッダーの存在
  - `koiki_csrf_token`クッキーの存在

#### 4. CSRF攻撃をシミュレーション
```javascript
// コンソールで以下を実行（CSRFヘッダーなし）
fetch('/api/auth/logout', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
```
→ `403 Forbidden`エラーが返されることを確認

## トラブルシューティング

### よくある問題

#### 1. フロントエンドサーバーに接続できない
```
❌ フロントエンドサーバーに接続できません
   http://localhost:3000 が起動していることを確認してください
```

**解決方法:**
- フロントエンドサーバーが起動していることを確認
- ポート3000が他のプロセスに使用されていないか確認
- `cd frontend && npm run dev`でサーバーを再起動

#### 2. ログインに失敗する
```
❌ ログインに失敗しました。テストを中断します。
```

**解決方法:**
- バックエンドサーバーが起動していることを確認
- テストユーザー（user@example.com）が存在することを確認
- データベースの接続状況を確認

#### 3. 一部のテストが失敗する
```
⚠️ 一部のCSRF検証テストが失敗しました。
```

**解決方法:**
- エラーメッセージを確認して該当エンドポイントを調査
- サーバーログでエラー詳細を確認
- CSRF実装コードを再確認

### ログの確認方法

#### フロントエンドログ
フロントエンドサーバーのターミナルで以下のようなログを確認：

```
CSRF token validation failed
POST /api/auth/login 403 in 1986ms
```

#### バックエンドログ
バックエンドサーバーでCSRF関連のログを確認。

## セキュリティ推奨事項

### 実装済み対策
✅ Double Submit Cookie方式の採用
✅ HttpOnlyクッキーの使用
✅ SameSite=Laxの設定
✅ HTTPS環境での Secure属性設定
✅ 32文字以上のランダムトークン

### 追加検討事項
- CSRFトークンのローテーション頻度
- トークンの有効期限設定
- より高度な同期パターン（Synchronized Token Pattern）の検討
- WAF（Web Application Firewall）との連携

## 参考資料

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [RFC 6265 - HTTP State Management Mechanism](https://tools.ietf.org/html/rfc6265)
- [SameSite Cookie Explained](https://web.dev/samesite-cookies-explained/)

---

## テストスクリプトの詳細

### ファイル構成
```
ops/tests/test_csrf_validation.py  # メインテストスクリプト
test_csrf.sh                       # 実行用シェルスクリプト
docs/csrf-testing-guide.md        # このガイド
```

### カスタマイズ可能な設定
テストスクリプト内で以下の設定を変更可能：

```python
# フロントエンドURL
frontend_url = "http://localhost:3000"

# テストユーザー
email = "user@example.com"
password = "testuser123456"

# CSRFトークン長
token_length = 32
```

このガイドを参考に、CSRF保護機能が正しく動作していることを定期的に確認してください。
