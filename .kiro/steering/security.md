# セキュリティガイドライン

## 認証システム

### JWT認証
- **アクセストークン**: 30分有効
- **リフレッシュトークン**: 7日有効、デバイス追跡付き
- **トークンローテーション**: リフレッシュ時に新トークン発行

### Cookie認証（フロントエンド）
```typescript
// HTTPOnly + Secure + SameSite設定
response.cookies.set('koiki_access_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  maxAge: 30 * 60,
});
```

### CSRF保護
- 全ての状態変更操作でCSRFトークン必須
- `x-csrf-token` ヘッダーで送信
- Cookie + ヘッダーの二重検証

## セキュリティ機能

### ログイン試行制限
- `LoginAttemptModel`: IP追跡、失敗分析
- `LoginSecurityService`: 不審なパターン検出

### パスワード要件
- 8文字以上
- 複雑性チェック（`check_password_complexity`）
- bcryptハッシュ化

### レート制限
```python
@limiter.limit("5/minute")  # ログイン
@limiter.limit("100/minute")  # 一般API
```

## セキュリティヘッダー

```python
# SecurityHeadersMiddleware で自動付与
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## フロントエンド認証ガード

```typescript
// middleware.ts
const PROTECTED_ROUTES = ['/dashboard', '/profile', '/admin'];
// トークン存在 + JWT形式検証
```

## セキュリティ監査

```bash
# 脆弱性スキャン
poetry run pip-audit

# 静的解析
poetry run bandit -r app/ libkoiki/

# セキュリティAPIテスト
./run_security_test.sh test
```

## SSO/SAML セキュリティ

- PKCE (S256) によるコード交換
- state/nonce による CSRF/リプレイ攻撃防止
- JWKS による署名検証
- at_hash 検証（アクセストークンハッシュ）
- ドメイン制限チェック
