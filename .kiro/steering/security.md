# セキュリティガイドライン

## セキュリティ原則

KOIKI-FWは、エンタープライズグレードのセキュリティを重視した設計となっています。すべての開発において以下の原則を遵守してください。

## 認証・認可

### JWT認証
- **アクセストークン**: 短期間（30分）の有効期限
- **リフレッシュトークン**: 長期間（7日）の有効期限
- **トークンローテーション**: リフレッシュ時に新しいトークンを発行

### Cookie認証（推奨）
- **HTTPOnly**: JavaScriptからアクセス不可
- **Secure**: HTTPS接続でのみ送信
- **SameSite**: CSRF攻撃を防止
- **CSRF保護**: 全ての状態変更操作でCSRFトークン必須

### RBAC（ロールベースアクセス制御）
```python
# 権限チェックの例
@require_permissions("user:read")
async def get_user(user_id: int):
    pass

@require_roles("admin")
async def admin_only_endpoint():
    pass
```

## データ保護

### パスワード管理
- **ハッシュ化**: bcryptを使用（コスト12以上）
- **ソルト**: 自動生成される一意のソルト
- **最小要件**: 8文字以上、複雑性要件

```python
# パスワードハッシュ化の例
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash(plain_password)
```

### 機密データ
- **環境変数**: 機密情報は環境変数で管理
- **暗号化**: データベース内の機密データは暗号化
- **ログ**: 機密情報をログに出力しない

## 入力検証

### Pydanticスキーマ
```python
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v
```

### SQLインジェクション対策
- **SQLAlchemy ORM**: 常にORMを使用
- **パラメータ化クエリ**: 生のSQLを避ける
- **入力サニタイゼーション**: 全ての入力を検証

## レート制限

### API保護
```python
from slowapi import Limiter

# ログインエンドポイントの例
@limiter.limit("5/minute")
async def login():
    pass

# 一般APIの例
@limiter.limit("100/minute")
async def api_endpoint():
    pass
```

### 設定例
- **ログイン**: 5回/分
- **パスワードリセット**: 3回/時間
- **一般API**: 100回/分
- **管理API**: 50回/分

## HTTPS・TLS

### 本番環境要件
- **TLS 1.2以上**: 古いプロトコルは無効化
- **HSTS**: Strict-Transport-Security ヘッダー
- **証明書**: 有効なSSL/TLS証明書

### セキュリティヘッダー
```python
# middleware.pyで設定
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}
```

## ログ・監査

### セキュリティログ
- **認証イベント**: ログイン成功/失敗
- **認可エラー**: 権限不足のアクセス試行
- **データ変更**: 重要データの作成/更新/削除
- **管理操作**: 管理者権限での操作

### ログ形式
```python
import structlog

logger = structlog.get_logger()

# セキュリティイベントのログ例
logger.info(
    "authentication_success",
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

## 脆弱性対策

### 定期的なセキュリティチェック
```bash
# 依存関係の脆弱性スキャン
poetry run pip-audit

# 静的セキュリティ解析
poetry run bandit -r app/ libkoiki/
```

### OWASP Top 10対策
1. **インジェクション**: ORMとパラメータ化クエリ使用
2. **認証の不備**: 強固な認証システム実装
3. **機密データ露出**: 暗号化と適切なアクセス制御
4. **XXE**: XML処理の制限
5. **アクセス制御の不備**: RBAC実装
6. **セキュリティ設定ミス**: セキュリティヘッダー設定
7. **XSS**: 入力検証とエスケープ処理
8. **安全でないデシリアライゼーション**: 信頼できないデータの検証
9. **既知の脆弱性**: 定期的な依存関係更新
10. **不十分なログ・監視**: 包括的なログ実装

## フロントエンドセキュリティ

### Next.js セキュリティ実装

#### Middleware認証ガード
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('koiki_access_token')?.value;
  
  if (!token && isProtectedRoute(pathname)) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }
  
  return NextResponse.next();
}
```

#### Cookie認証セキュリティ
```typescript
// cookie-utils.ts
export function setAccessTokenCookie(response: NextResponse, token: string) {
  response.cookies.set('koiki_access_token', token, {
    httpOnly: true,        // XSS対策
    secure: true,          // HTTPS必須
    sameSite: 'lax',      // CSRF対策
    maxAge: 30 * 60,      // 30分
    path: '/',
  });
}
```

### XSS対策
- **CSP**: Content Security Policy設定
- **入力サニタイゼーション**: 全ての入力を検証
- **出力エスケープ**: HTMLエスケープ処理
- **HTTPOnly Cookie**: JavaScriptからアクセス不可

### CSRF対策実装
```typescript
// csrf-utils.ts
export function generateCSRFToken(): string {
  return randomBytes(32).toString('hex');
}

export function validateCSRFToken(request: NextRequest): boolean {
  const cookieToken = request.cookies.get('koiki_csrf_token')?.value;
  const headerToken = request.headers.get('x-csrf-token');
  return !!(cookieToken && headerToken && cookieToken === headerToken);
}

// API Route Handler
export async function POST(request: NextRequest) {
  if (!validateCSRFToken(request)) {
    return createCSRFErrorResponse();
  }
  // 処理続行
}
```

### 認証ガード実装
```typescript
// auth-guard.tsx
export function AuthGuard({ children, requireAuth = true }) {
  const { isAuthenticated, isLoading } = useCookieAuth();
  
  if (requireAuth && !isAuthenticated) {
    return <LoginRedirect />;
  }
  
  return <>{children}</>;
}

// 使用例
<AuthGuard requireAuth={true} requiredRoles={['admin']}>
  <AdminPanel />
</AuthGuard>
```

## セキュリティテスト

### 自動テスト
```bash
# セキュリティAPIテストの実行
./run_security_test.sh test

# 権限テストの例
pytest tests/security/test_rbac.py -v
```

### 手動テスト項目
- [ ] 認証バイパス試行
- [ ] 権限昇格試行
- [ ] SQLインジェクション試行
- [ ] XSS攻撃試行
- [ ] CSRF攻撃試行
- [ ] レート制限回避試行

## インシデント対応

### セキュリティインシデント発生時
1. **即座の対応**: 攻撃の停止・システム隔離
2. **影響範囲調査**: ログ解析・被害状況確認
3. **復旧作業**: システム修復・データ復旧
4. **再発防止**: 脆弱性修正・監視強化
5. **報告**: 関係者への報告・文書化

### 緊急連絡先
- セキュリティ担当者
- システム管理者
- 法務担当者（必要に応じて）