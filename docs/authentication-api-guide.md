# KOIKI-FW 認証系API完全ガイド

## 概要

KOIKI-FW v0.6.0における認証系APIの包括的なガイドドキュメントです。本フレームワークは、企業級アプリケーションに求められる堅牢で柔軟な認証システムを提供します。JWT（JSON Web Token）をベースとし、リフレッシュトークン、パスワードリセット、ログイン試行制限など、現代的なセキュリティ要件を満たす機能を実装しています。

## 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [認証フロー](#認証フロー)
3. [API エンドポイント詳細](#api-エンドポイント詳細)
4. [セキュリティ機能](#セキュリティ機能)
5. [データベース設計](#データベース設計)
6. [設定とカスタマイズ](#設定とカスタマイズ)
7. [使用例](#使用例)
8. [トラブルシューティング](#トラブルシューティング)
9. [ベストプラクティス](#ベストプラクティス)

## アーキテクチャ概要

### レイヤー構成

KOIKI-FWの認証システムは、以下の4つのレイヤーで構成されています：

```
┌─────────────────────────────────────────┐
│ API Layer (Endpoints)                   │  ← HTTP リクエスト/レスポンス
├─────────────────────────────────────────┤
│ Service Layer (Business Logic)          │  ← 認証ロジック、セキュリティ制御
├─────────────────────────────────────────┤
│ Repository Layer (Data Access)          │  ← データアクセス、永続化
├─────────────────────────────────────────┤
│ Model Layer (Database Schema)           │  ← データモデル、テーブル定義
└─────────────────────────────────────────┘
```

### 主要コンポーネント

#### **1. API エンドポイント**
- `auth_basic.py`: 基本認証（ログイン、登録、ログアウト、ユーザー情報取得）
- `auth_password.py`: パスワード管理（変更、リセット）
- `auth_token.py`: トークン管理（リフレッシュ、無効化）

#### **2. サービス層**
- `AuthService`: 認証・トークン管理
- `PasswordResetService`: パスワードリセット機能
- `LoginSecurityService`: ログイン試行制限・セキュリティ
- `UserService`: ユーザー管理

#### **3. リポジトリ層**
- `UserRepository`: ユーザーデータアクセス
- `RefreshTokenRepository`: リフレッシュトークン管理
- `PasswordResetRepository`: パスワードリセットトークン管理
- `LoginAttemptRepository`: ログイン試行履歴管理

#### **4. データモデル**
- `UserModel`: ユーザー情報
- `RefreshTokenModel`: リフレッシュトークン
- `PasswordResetModel`: パスワードリセットトークン
- `LoginAttemptModel`: ログイン試行履歴

## 認証フロー

### 基本認証フロー

```mermaid
graph TD
    A[ユーザー] -->|1. ログイン要求| B[API Gateway]
    B -->|2. セキュリティチェック| C[LoginSecurityService]
    C -->|3. 認証| D[UserService]
    D -->|4. トークン生成| E[AuthService]
    E -->|5. アクセストークン + リフレッシュトークン| A
    
    A -->|6. API要求 + アクセストークン| F[Protected Endpoint]
    F -->|7. トークン検証| G[Security Middleware]
    G -->|8. レスポンス| A
```

### リフレッシュトークンフロー

```mermaid
graph TD
    A[クライアント] -->|1. アクセストークン期限切れ| B[API応答 401]
    A -->|2. リフレッシュ要求| C[/auth/refresh]
    C -->|3. トークン検証| D[AuthService]
    D -->|4. 新トークン発行| E[TokenWithRefresh]
    E -->|5. 新しいアクセストークン + リフレッシュトークン| A
```

### パスワードリセットフロー

```mermaid
graph TD
    A[ユーザー] -->|1. リセット要求| B[/auth/password-reset/request]
    B -->|2. トークン生成| C[PasswordResetService]
    C -->|3. メール送信（予定）| D[Email Service]
    D -->|4. リセットリンク| A
    A -->|5. リセット実行| E[/auth/password-reset/confirm]
    E -->|6. パスワード更新| F[UserService]
```

## API エンドポイント詳細

### 基本認証エンドポイント (`auth_basic.py`)

#### **POST /auth/login**

OAuth2互換のログインエンドポイント。メールアドレスとパスワードで認証し、JWTアクセストークンとリフレッシュトークンを発行します。

**リクエスト**
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

**レスポンス**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def50200b8a1c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**セキュリティ機能**
- レート制限: 10回/分
- ログイン試行制限: 5回失敗で15分間ロックアウト
- IP単位制限: 10回失敗で15分間ブロック
- 段階的遅延: 失敗回数に応じた指数関数的遅延
- 全ログイン試行の記録と監査

**エラーレスポンス**
```json
// 認証失敗
{
  "detail": "Incorrect email or password",
  "status_code": 401
}

// アカウントロックアウト
{
  "detail": "Account temporarily locked due to 5 failed attempts",
  "status_code": 429,
  "headers": {
    "Retry-After": "900"
  }
}
```

#### **POST /auth/register**

新規ユーザー登録エンドポイント。

**リクエスト**
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "New User"
}
```

**レスポンス**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 123,
    "email": "newuser@example.com",
    "full_name": "New User",
    "is_active": true,
    "created_at": "2025-07-07T12:00:00Z"
  }
}
```

**バリデーション**
- メールアドレス: 有効な形式、一意性
- パスワード: 8文字以上、複雑性要件
- レート制限: 5回/分

#### **GET /auth/me**

現在認証されているユーザーの情報を取得。

**リクエスト**
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**レスポンス**
```json
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-07-07T12:00:00Z",
  "updated_at": "2025-07-07T12:00:00Z"
}
```

#### **POST /auth/logout**

ログアウト処理。JWTはステートレスなため、主にログ記録とクライアント側処理の統一化に使用。

**リクエスト**
```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**レスポンス**
```json
{
  "message": "Successfully logged out"
}
```

### パスワード管理エンドポイント (`auth_password.py`)

#### **POST /auth/password-change**

認証済みユーザーのパスワード変更。

**リクエスト**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**レスポンス**
```json
{
  "message": "Password changed successfully"
}
```

**セキュリティ**
- 現在のパスワード検証必須
- 新パスワードの複雑性要件チェック
- レート制限: 5回/分

#### **POST /auth/password-reset/request**

パスワードリセット要求。メールアドレスが登録されている場合、リセットトークンを生成。

**リクエスト**
```json
{
  "email": "user@example.com"
}
```

**レスポンス**
```json
{
  "message": "Password reset email sent if account exists"
}
```

**セキュリティ特徴**
- メールアドレス存在有無に関わらず同じレスポンス（情報漏洩防止）
- トークン有効期限: 1時間
- レート制限: 3回/分
- IP・デバイス情報の記録

**開発環境での注意**
現在はメール送信機能は未実装のため、生成されたリセットトークンはログに出力されます。本番環境では必ずメール送信機能と連携してください。

#### **POST /auth/password-reset/confirm**

パスワードリセットの実行。

**リクエスト**
```json
{
  "token": "abc123def456...",
  "new_password": "newpassword789"
}
```

**レスポンス**
```json
{
  "message": "Password reset completed successfully",
  "data": {
    "user_email": "user@example.com"
  }
}
```

**セキュリティ機能**
- トークンの一回限り使用
- 有効期限チェック（1時間）
- パスワード更新後に全リフレッシュトークンを無効化
- レート制限: 5回/分

### トークン管理エンドポイント (`auth_token.py`)

#### **POST /auth/refresh**

リフレッシュトークンを使用してアクセストークンを更新。

**リクエスト**
```json
{
  "refresh_token": "def50200b8a1c3d4e5f6..."
}
```

**レスポンス**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "ghi78900c1b2a3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**セキュリティ機能**
- トークンローテーション: 新しいリフレッシュトークンを発行
- デバイス情報の検証
- 有効期限チェック（7日間）
- レート制限: 10回/分

#### **POST /auth/revoke-all-tokens**

現在のユーザーの全リフレッシュトークンを無効化（全デバイスからログアウト）。

**リクエスト**
```http
POST /auth/revoke-all-tokens
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**レスポンス**
```json
{
  "message": "Successfully revoked 3 refresh tokens",
  "data": {
    "revoked_count": 3
  }
}
```

## セキュリティ機能

### 多層防御システム

KOIKI-FWの認証システムは、複数のセキュリティレイヤーで保護されています：

#### **1. API レベル**
- **レート制限**: slowapi による固定窓アルゴリズム
- **CORS設定**: 設定可能なオリジン制限
- **セキュリティヘッダー**: 設定により追加可能

#### **2. 認証レベル**
- **JWT署名**: HMAC SHA-256アルゴリズム
- **トークンローテーション**: セキュアなセッション管理
- **短い有効期限**: アクセストークン60分（開発）、15分（本番推奨）

#### **3. アプリケーションレベル**
- **ログイン試行制限**: カスタム実装による細密制御
- **段階的遅延**: ブルートフォース攻撃対策
- **監査ログ**: 全認証イベントの記録

#### **4. データレベル**
- **パスワードハッシュ化**: bcrypt自動ソルト生成
- **トークンハッシュ化**: SHA-256による安全な保存
- **暗号化**: 機密データの暗号化保存

### ログイン試行制限詳細

#### **制限ポリシー**

| 制限タイプ | 閾値 | ロックアウト期間 | 対象 |
|------------|------|-----------------|------|
| メールアドレス単位 | 5回失敗 | 15分 | 特定アカウント |
| IP単位 | 10回失敗 | 15分 | 送信元IP |
| 段階的遅延 | 失敗毎 | 指数関数的 | 即座に適用 |

#### **段階的遅延アルゴリズム**

```python
delay = min(2 ** (失敗回数 - 1), 30)  # 最大30秒
```

失敗回数と遅延時間の関係：
- 1回目: 0秒
- 2回目: 2秒
- 3回目: 4秒
- 4回目: 8秒
- 5回目: 16秒
- 6回目以降: 30秒（上限）

#### **監査ログ項目**

全てのログイン試行について以下の情報を記録：

```json
{
  "id": 123,
  "email": "user@example.com",
  "user_id": 456,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "is_successful": true,
  "failure_reason": null,
  "attempted_at": "2025-07-07T12:00:00Z"
}
```

### パスワードセキュリティ

#### **複雑性要件**
- 最小長: 8文字
- 大文字・小文字・数字・記号の組み合わせ
- 空白文字禁止
- 辞書攻撃対策（一般的なパスワードの拒否）

#### **ハッシュ化**
```python
# bcryptによる自動ソルト生成
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
```

### トークンセキュリティ

#### **アクセストークン**
- アルゴリズム: HS256 (HMAC SHA-256)
- 有効期限: 60分（開発）/ 15分（本番推奨）
- ペイロード: ユーザーID、有効期限、発行時刻

#### **リフレッシュトークン**
- 暗号学的に安全な乱数生成
- SHA-256ハッシュ化してデータベース保存
- 有効期限: 7日間
- デバイス情報との紐付け

## データベース設計

### ER図

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ password_reset_tokens : has
    users ||--o{ login_attempts : has
    users ||--o{ todos : owns
    users }|--|| user_roles : has
    roles ||--o{ user_roles : belongs
    roles }|--|| role_permissions : has
    permissions ||--o{ role_permissions : belongs

    users {
        int id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_superuser
        datetime created_at
        datetime updated_at
    }

    refresh_tokens {
        int id PK
        int user_id FK
        string token_hash UK
        datetime expires_at
        boolean is_revoked
        datetime created_at
        datetime revoked_at
        string device_info
    }

    password_reset_tokens {
        int id PK
        int user_id FK
        string token_hash UK
        datetime expires_at
        boolean is_used
        datetime created_at
        datetime used_at
        string ip_address
        text user_agent
    }

    login_attempts {
        int id PK
        string email
        int user_id FK
        string ip_address
        text user_agent
        boolean is_successful
        string failure_reason
        datetime attempted_at
    }
```

### テーブル詳細

#### **users テーブル**
ユーザーの基本情報を格納。

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
```

#### **refresh_tokens テーブル**
リフレッシュトークンの管理。

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    device_info TEXT
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_revoked ON refresh_tokens(is_revoked);
```

#### **password_reset_tokens テーブル**
パスワードリセットトークンの管理。

```sql
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),  -- IPv6対応
    user_agent TEXT
);

CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_tokens_used ON password_reset_tokens(is_used);
```

#### **login_attempts テーブル**
ログイン試行履歴の記録。

```sql
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45) NOT NULL,  -- IPv6対応
    user_agent TEXT,
    is_successful BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_successful ON login_attempts(is_successful);
CREATE INDEX idx_login_attempts_attempted_at ON login_attempts(attempted_at);
```

### データ保持ポリシー

#### **自動クリーンアップ**
- **ログイン試行履歴**: 30日後に自動削除
- **期限切れリフレッシュトークン**: 定期的にクリーンアップ
- **使用済みパスワードリセットトークン**: 24時間後に削除

#### **実装例**
```python
# 定期実行ジョブ（例：毎日実行）
async def cleanup_expired_data():
    # 30日以上古いログイン試行履歴を削除
    await login_security_service.cleanup_old_attempts(db, days=30)
    
    # 期限切れリフレッシュトークンを削除
    await auth_service.cleanup_expired_refresh_tokens(db)
    
    # 使用済みパスワードリセットトークンを削除
    await password_reset_service.cleanup_expired_tokens(db)
```

## 設定とカスタマイズ

### 基本設定 (`libkoiki/core/config.py`)

```python
class Settings(BaseSettings):
    # JWT設定
    SECRET_KEY: str = "development_secret_key"  # 本番では環境変数から取得
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # アクセストークン有効期限
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # リフレッシュトークン有効期限
    
    # レート制限設定
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "10/minute"
    
    # セキュリティ設定
    LOGIN_MAX_ATTEMPTS_EMAIL: int = 5      # メール単位最大試行回数
    LOGIN_MAX_ATTEMPTS_IP: int = 10        # IP単位最大試行回数
    LOGIN_LOCKOUT_DURATION: int = 15       # ロックアウト期間（分）
    
    # パスワード設定
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = True
    
    # データベース設定
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    
    # Redis設定（オプション）
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
```

### 環境別設定

#### **開発環境**
```bash
# .env
APP_ENV=development
SECRET_KEY=development_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=true
LOG_LEVEL=DEBUG
```

#### **本番環境**
```bash
# .env
APP_ENV=production
SECRET_KEY=your_super_secure_random_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=15
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@prod-db:5432/app
REDIS_ENABLED=true
REDIS_HOST=redis-cluster.internal
```

### カスタマイズポイント

#### **1. ログイン試行制限のカスタマイズ**

```python
class CustomLoginSecurityService(LoginSecurityService):
    def __init__(self, login_attempt_repository: LoginAttemptRepository):
        super().__init__(login_attempt_repository)
        
        # カスタム設定
        self.max_attempts_per_email = 3  # より厳格に
        self.max_attempts_per_ip = 20    # より緩和
        self.lockout_duration_minutes = 30  # より長期
```

#### **2. パスワード複雑性要件のカスタマイズ**

```python
from pydantic import validator

class CustomPasswordChangeRequest(PasswordChangeRequest):
    @validator('new_password')
    def validate_password_complexity(cls, v):
        # カスタム複雑性チェック
        if len(v) < 12:  # より長いパスワード要求
            raise ValueError('Password must be at least 12 characters')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        
        # 辞書攻撃対策
        common_passwords = ['password', '123456', 'qwerty']
        if v.lower() in common_passwords:
            raise ValueError('Password too common')
        
        return v
```

#### **3. トークン有効期限の動的設定**

```python
class DynamicTokenService(AuthService):
    async def create_token_pair(self, user: UserModel, **kwargs):
        # ユーザーの役割に応じて有効期限を調整
        if user.is_superuser:
            expires_minutes = 30  # 管理者は短時間
        else:
            expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # トークン生成ロジック...
```

## 使用例

### フロントエンド実装例

#### **React + TypeScript**

```typescript
// types/auth.ts
interface LoginRequest {
  username: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// services/authService.ts
class AuthService {
  private baseURL = '/api/v1/auth';
  
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await fetch(`${this.baseURL}/login`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        throw new Error(`Too many attempts. Try again in ${retryAfter} seconds.`);
      }
      throw new Error('Login failed');
    }
    
    return response.json();
  }
  
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await fetch(`${this.baseURL}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (!response.ok) {
      throw new Error('Token refresh failed');
    }
    
    return response.json();
  }
  
  async resetPassword(email: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/password-reset/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    if (!response.ok) {
      throw new Error('Password reset request failed');
    }
  }
}

// hooks/useAuth.ts
export const useAuth = () => {
  const [tokens, setTokens] = useState<TokenResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const tokenResponse = await authService.login(credentials);
      setTokens(tokenResponse);
      
      // ローカルストレージに保存
      localStorage.setItem('refresh_token', tokenResponse.refresh_token);
      
      // 自動リフレッシュのスケジュール
      scheduleTokenRefresh(tokenResponse.expires_in);
      
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  const scheduleTokenRefresh = (expiresIn: number) => {
    // トークン期限の90%で自動リフレッシュ
    const refreshTime = (expiresIn * 0.9) * 1000;
    
    setTimeout(async () => {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const newTokens = await authService.refreshToken(refreshToken);
          setTokens(newTokens);
          localStorage.setItem('refresh_token', newTokens.refresh_token);
          scheduleTokenRefresh(newTokens.expires_in);
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        // ログイン画面にリダイレクト
      }
    }, refreshTime);
  };
  
  return { tokens, login, isLoading };
};
```

#### **Vue.js + Composition API**

```vue
<template>
  <div class="login-form">
    <form @submit.prevent="handleLogin">
      <input 
        v-model="email" 
        type="email" 
        placeholder="Email" 
        required 
      />
      <input 
        v-model="password" 
        type="password" 
        placeholder="Password" 
        required 
      />
      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
    
    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuth } from '@/composables/useAuth';

const { login, isLoading, error } = useAuth();

const email = ref('');
const password = ref('');

const handleLogin = async () => {
  try {
    await login({
      username: email.value,
      password: password.value,
    });
    // ログイン成功時の処理
  } catch (err) {
    console.error('Login failed:', err);
  }
};
</script>
```

### バックエンド実装例

#### **カスタム認証ミドルウェア**

```python
# middleware/auth_middleware.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

class CustomAuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(self, request: Request):
        # 公開エンドポイントのチェック
        if self.is_public_endpoint(request.url.path):
            return
        
        # トークン取得
        credentials: Optional[HTTPAuthorizationCredentials] = \
            await self.security(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # トークン検証
        try:
            user = await verify_token(credentials.credentials)
            request.state.user = user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def is_public_endpoint(self, path: str) -> bool:
        public_paths = [
            '/auth/login',
            '/auth/register',
            '/auth/password-reset/request',
            '/auth/password-reset/confirm',
            '/docs',
            '/openapi.json',
        ]
        return path in public_paths
```

#### **カスタム権限チェック**

```python
# dependencies/permissions.py
from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import List

def require_permissions(required_permissions: List[str]):
    """指定された権限を要求するデコレータ"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 現在のユーザーを取得
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 権限チェック
            user_permissions = await get_user_permissions(current_user.id)
            
            for permission in required_permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用例
@router.delete("/users/{user_id}")
@require_permissions(["user.delete"])
async def delete_user(
    user_id: int,
    current_user: ActiveUserDep,
    db: DBSessionDep
):
    # 削除処理
    pass
```

### モバイルアプリ実装例

#### **Flutter (Dart)**

```dart
// models/auth_models.dart
class LoginRequest {
  final String username;
  final String password;
  
  LoginRequest({required this.username, required this.password});
  
  Map<String, String> toFormData() {
    return {
      'username': username,
      'password': password,
    };
  }
}

class TokenResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;
  
  TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });
  
  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      tokenType: json['token_type'],
      expiresIn: json['expires_in'],
    );
  }
}

// services/auth_service.dart
class AuthService {
  static const String baseURL = 'https://api.yourapp.com/api/v1/auth';
  late final Dio _dio;
  
  AuthService() {
    _dio = Dio();
    _dio.interceptors.add(AuthInterceptor());
  }
  
  Future<TokenResponse> login(LoginRequest request) async {
    try {
      final response = await _dio.post(
        '$baseURL/login',
        data: request.toFormData(),
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );
      
      return TokenResponse.fromJson(response.data);
    } on DioError catch (e) {
      if (e.response?.statusCode == 429) {
        final retryAfter = e.response?.headers['retry-after']?.first;
        throw AuthException('Too many attempts. Try again in $retryAfter seconds.');
      }
      throw AuthException('Login failed: ${e.message}');
    }
  }
  
  Future<void> requestPasswordReset(String email) async {
    try {
      await _dio.post(
        '$baseURL/password-reset/request',
        data: {'email': email},
      );
    } on DioError catch (e) {
      throw AuthException('Password reset request failed: ${e.message}');
    }
  }
}

// providers/auth_provider.dart
class AuthProvider extends ChangeNotifier {
  TokenResponse? _tokens;
  bool _isLoading = false;
  String? _error;
  
  TokenResponse? get tokens => _tokens;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _tokens != null;
  
  Future<void> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final request = LoginRequest(username: email, password: password);
      final tokenResponse = await AuthService().login(request);
      
      _tokens = tokenResponse;
      
      // セキュアストレージに保存
      await _storeTokens(tokenResponse);
      
      // 自動リフレッシュのスケジュール
      _scheduleTokenRefresh();
      
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> _storeTokens(TokenResponse tokens) async {
    const storage = FlutterSecureStorage();
    await storage.write(key: 'refresh_token', value: tokens.refreshToken);
    await storage.write(key: 'access_token', value: tokens.accessToken);
  }
  
  void _scheduleTokenRefresh() {
    if (_tokens == null) return;
    
    // トークン期限の90%で自動リフレッシュ
    final refreshDuration = Duration(
      seconds: (_tokens!.expiresIn * 0.9).round(),
    );
    
    Timer(refreshDuration, () async {
      try {
        await _refreshToken();
      } catch (e) {
        // リフレッシュ失敗時はログアウト
        await logout();
      }
    });
  }
  
  Future<void> _refreshToken() async {
    if (_tokens?.refreshToken == null) return;
    
    try {
      final newTokens = await AuthService().refreshToken(_tokens!.refreshToken);
      _tokens = newTokens;
      await _storeTokens(newTokens);
      _scheduleTokenRefresh();
      notifyListeners();
    } catch (e) {
      throw Exception('Token refresh failed: $e');
    }
  }
}
```

## トラブルシューティング

### よくある問題と解決方法

#### **1. 認証エラー**

**問題**: "Incorrect email or password"
```json
{
  "detail": "Incorrect email or password",
  "status_code": 401
}
```

**原因と解決方法**:
- メールアドレスやパスワードの入力ミス → 入力内容を確認
- アカウントが無効化されている → 管理者に確認
- パスワードハッシュの問題 → データベースの整合性を確認

**デバッグ手順**:
```python
# ログで詳細を確認
logger.info("Authentication attempt", 
           email=email, 
           user_exists=user is not None,
           password_valid=user and verify_password(password, user.hashed_password))
```

#### **2. アカウントロックアウト**

**問題**: "Account temporarily locked due to failed attempts"
```json
{
  "detail": "Account temporarily locked due to 5 failed attempts",
  "status_code": 429,
  "headers": {"Retry-After": "900"}
}
```

**解決方法**:
1. **待機**: Retry-Afterヘッダーで指定された時間待つ
2. **手動解除**: 管理者権限でロックアウトを解除
3. **設定調整**: 試行制限の閾値を調整

**管理者による手動解除**:
```python
# 特定ユーザーのロックアウト解除
async def unlock_user_account(email: str, db: AsyncSession):
    login_security_service = LoginSecurityService(LoginAttemptRepository())
    login_security_service.login_attempt_repository.session = db
    
    # 失敗試行履歴を削除
    await login_security_service.login_attempt_repository.cleanup_failed_attempts_by_email(email)
```

#### **3. トークン期限切れ**

**問題**: "Token has expired"
```json
{
  "detail": "Token has expired",
  "status_code": 401
}
```

**解決方法**:
1. **自動リフレッシュ**: リフレッシュトークンで新しいアクセストークンを取得
2. **再ログイン**: リフレッシュトークンも期限切れの場合

**実装例**:
```typescript
// 自動リフレッシュ付きAPIクライアント
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      try {
        await refreshToken();
        // 元のリクエストを再実行
        return axios.request(error.config);
      } catch (refreshError) {
        // ログイン画面にリダイレクト
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

#### **4. CORS エラー**

**問題**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**解決方法**:
```python
# settings.pyでCORS設定を確認
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",  # React開発サーバー
    "http://localhost:8080",  # Vue開発サーバー
    "https://yourdomain.com"  # 本番フロントエンド
]

# main.pyでCORSミドルウェアを設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **5. データベース接続エラー**

**問題**: "Database connection failed"

**解決方法**:
1. **接続文字列確認**: DATABASE_URLが正しいか確認
2. **データベースサーバー状態**: PostgreSQLが起動しているか確認
3. **権限確認**: データベースユーザーの権限を確認
4. **マイグレーション**: 最新のマイグレーションが適用されているか確認

```bash
# マイグレーション状態確認
alembic current

# 最新マイグレーション適用
alembic upgrade head

# データベース接続テスト
python -c "
from libkoiki.db.session import get_db
import asyncio
async def test():
    async for db in get_db():
        print('Database connection successful')
        break
asyncio.run(test())
"
```

### ログ分析

#### **重要なログポイント**

```python
# 認証関連のログ例
logger.info("Login attempt", email=email, ip_address=ip, user_agent=user_agent)
logger.warning("Login failed", email=email, reason="invalid_credentials")
logger.info("Login successful", email=email, user_id=user.id)
logger.warning("Account locked", email=email, attempts=5)
logger.info("Password reset requested", email=email)
logger.info("Password reset completed", user_id=user.id)
logger.warning("Token refresh failed", user_id=user.id, reason="expired")
```

#### **ログ監視クエリ例**

```bash
# 失敗ログイン試行の監視
grep "Login failed" /var/log/app.log | tail -100

# アカウントロックアウトの監視
grep "Account locked" /var/log/app.log | tail -20

# 異常なIP からのアクセス
grep "Login attempt" /var/log/app.log | grep -E "(192\.168\.|10\.|172\.)" -v | tail -50
```

### パフォーマンス最適化

#### **1. データベースクエリ最適化**

```python
# N+1クエリ問題の解決
async def get_user_with_permissions(user_id: int, db: AsyncSession):
    query = select(UserModel).options(
        selectinload(UserModel.roles).selectinload(RoleModel.permissions)
    ).where(UserModel.id == user_id)
    
    result = await db.execute(query)
    return result.scalars().first()

# インデックスの活用
# 適切なインデックスが設定されていることを確認
CREATE INDEX CONCURRENTLY idx_login_attempts_email_time 
ON login_attempts(email, attempted_at);
```

#### **2. キャッシュ戦略**

```python
# Redisを使用したユーザー情報キャッシュ
from redis.asyncio import Redis

class CachedUserService:
    def __init__(self, user_service: UserService, redis: Redis):
        self.user_service = user_service
        self.redis = redis
        self.cache_ttl = 300  # 5分
    
    async def get_user(self, user_id: int) -> Optional[UserModel]:
        # キャッシュから取得試行
        cache_key = f"user:{user_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return UserModel.model_validate_json(cached)
        
        # データベースから取得
        user = await self.user_service.get_user(user_id)
        if user:
            # キャッシュに保存
            await self.redis.setex(
                cache_key, 
                self.cache_ttl, 
                user.model_dump_json()
            )
        
        return user
```

#### **3. 接続プール最適化**

```python
# データベース接続プール設定
SQLALCHEMY_DATABASE_URI = "postgresql+asyncpg://user:pass@host/db"
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_size=20,          # 同時接続数
    max_overflow=30,       # プールオーバーフロー
    pool_pre_ping=True,    # 接続の健全性チェック
    pool_recycle=3600,     # 接続の再利用時間
    echo=False             # 本番ではFalse
)
```

## リフレッシュトークン機能の無効化

### 概要

KOIKI-FW v0.6.0では、リフレッシュトークン機能を含む包括的な認証システムが実装されています。
しかし、開発段階やシンプルな認証を望む場合、この機能を無効化してJWTアクセストークンのみの認証システムに変更することが可能です。

### 無効化のメリット・デメリット

#### ✅ **メリット**
- **シンプルさ**: コード量が大幅に削減され、理解・保守が容易
- **パフォーマンス**: データベースアクセスが削減される
- **セキュリティ**: 攻撃対象範囲が縮小される
- **開発効率**: 複雑な状態管理が不要

#### ⚠️ **デメリット**
- **セッション管理**: ログアウト時のトークン無効化ができない
- **長期利用**: アクセストークンの有効期限を延長する必要がある
- **利便性**: 自動ログイン機能がない
- **セキュリティ**: トークンが盗まれた場合の対処が困難

### 影響範囲

#### **必須変更ファイル (3つ)**
1. `libkoiki/api/v1/endpoints/auth_basic.py` - ログインエンドポイントの変更
2. `libkoiki/schemas/token.py` - レスポンススキーマの変更
3. `libkoiki/services/auth_service.py` - トークン生成ロジックの変更

#### **削除可能ファイル (6つ)**
1. `libkoiki/api/v1/endpoints/auth_token.py` - リフレッシュエンドポイント
2. `libkoiki/repositories/refresh_token_repository.py` - リフレッシュトークンリポジトリ
3. `libkoiki/models/refresh_token.py` - リフレッシュトークンモデル
4. `libkoiki/schemas/refresh_token.py` - リフレッシュトークンスキーマ
5. `alembic/versions/2025070702_add_refresh_tokens_table.py` - データベースマイグレーション
6. `libkoiki/api/dependencies.py` - 一部の依存関係削除

#### **部分変更ファイル (3つ)**
1. `libkoiki/api/v1/endpoints/auth.py` - ルーター設定の変更
2. `libkoiki/models/__init__.py` - モデルインポートの削除
3. `libkoiki/core/security.py` - 一部機能の削除

### 変更手順

#### **1. ログインエンドポイントの簡略化**

**`libkoiki/api/v1/endpoints/auth_basic.py`**

変更前:
```python
@router.post("/login", response_model=TokenWithRefresh)
async def login_for_access_token(
    # ... 省略
) -> TokenWithRefresh:
    # ... 省略
    access_token, refresh_token, expires_in = await auth_service.create_token_pair(
        user=user, db=db, device_info=device_info
    )
    
    return TokenWithRefresh(
        access_token=access_token, 
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )
```

変更後:
```python
@router.post("/login", response_model=Token)
async def login_for_access_token(
    # ... 省略
) -> Token:
    # ... 省略
    access_token = await auth_service.create_access_token(user=user)
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )
```

#### **2. スキーマの変更**

**`libkoiki/schemas/token.py`**

変更前:
```python
from libkoiki.schemas.token import TokenWithRefresh
```

変更後:
```python
from libkoiki.schemas.token import Token
```

#### **3. 認証サービスの簡略化**

**`libkoiki/services/auth_service.py`**

変更前:
```python
async def create_token_pair(self, user: UserModel, db: AsyncSession, device_info: Optional[str] = None) -> Tuple[str, str, int]:
    # 複雑なリフレッシュトークン生成ロジック
```

変更後:
```python
async def create_access_token(self, user: UserModel) -> str:
    # シンプルなアクセストークン生成のみ
    return create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=24)  # 長期間有効
    )
```

#### **4. 認証ルーターの更新**

**`libkoiki/api/v1/endpoints/auth.py`**

変更前:
```python
from . import auth_basic, auth_password, auth_token

router.include_router(auth_basic.router, tags=["Authentication - Basic"])
router.include_router(auth_password.router, tags=["Authentication - Password"])
router.include_router(auth_token.router, tags=["Authentication - Token"])
```

変更後:
```python
from . import auth_basic, auth_password

router.include_router(auth_basic.router, tags=["Authentication - Basic"])
router.include_router(auth_password.router, tags=["Authentication - Password"])
# auth_token.router は削除
```

#### **5. データベースマイグレーションの削除**

手順:
1. `alembic/versions/2025070702_add_refresh_tokens_table.py` を削除
2. 既存のデータベースがある場合は、手動でテーブルを削除:
   ```sql
   DROP TABLE IF EXISTS refresh_tokens;
   ```

#### **6. 不要なファイルの削除**

以下のファイルを削除:
```bash
rm libkoiki/api/v1/endpoints/auth_token.py
rm libkoiki/repositories/refresh_token_repository.py
rm libkoiki/models/refresh_token.py
rm libkoiki/schemas/refresh_token.py
rm alembic/versions/2025070702_add_refresh_tokens_table.py
```

#### **7. インポートの整理**

**`libkoiki/models/__init__.py`**

変更前:
```python
from .refresh_token import RefreshTokenModel
```

変更後:
```python
# RefreshTokenModel のインポートを削除
```

### 設定の調整

#### **JWT設定の変更**

**`libkoiki/core/config.py`**

アクセストークンの有効期限を延長:

```python
# 変更前
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

# 変更後（長期間有効）
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24時間
```

### 動作確認テスト

#### **1. インポートテスト**

```bash
python -c "
from libkoiki.api.v1.endpoints.auth import router
from libkoiki.schemas.token import Token
print('✅ Import successful')
"
```

#### **2. エンドポイントテスト**

```bash
python -c "
from libkoiki.api.v1.endpoints.auth import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(router, prefix='/auth')
client = TestClient(app)

# エンドポイント数の確認
openapi_spec = app.openapi()
auth_endpoints = [path for path in openapi_spec.get('paths', {}).keys() if path.startswith('/auth/')]
print(f'認証エンドポイント数: {len(auth_endpoints)}')
for endpoint in sorted(auth_endpoints):
    print(f'  {endpoint}')
"
```

#### **3. スキーマテスト**

```bash
python -c "
from libkoiki.schemas.token import Token

token = Token(access_token='test_token', token_type='bearer')
print('✅ Token schema works')
print(f'Token: {token.model_dump()}')
"
```

### 復元手順

リフレッシュトークン機能を後から復元する場合は、以下の手順で可能:

1. 削除したファイルをGitから復元
2. データベースマイグレーションを実行
3. インポートとルーター設定を復元
4. 設定ファイルを元に戻す

### 推奨事項

#### **開発段階**
- シンプルなJWT認証のみを使用
- アクセストークンの有効期限を24時間に設定
- 必要に応じて後から追加

#### **本番環境**
- リフレッシュトークン機能を有効化
- セキュリティを重視した設定
- 適切な有効期限の設定

### 結論

リフレッシュトークン機能の無効化は、開発段階や単純な認証システムを求める場合に有効です。
コードの簡略化により理解・保守が容易になり、パフォーマンスも向上します。
ただし、セキュリティ面での制約があるため、本番環境では慎重に検討してください。

---

## ベストプラクティス

### セキュリティベストプラクティス

#### **1. 本番環境での必須設定**

```python
# 本番環境設定例
class ProductionSettings(Settings):
    # 強力なランダムキー（32バイト以上）
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # 短いアクセストークン有効期限
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # デバッグ無効
    DEBUG: bool = False
    
    # HTTPS強制
    FORCE_HTTPS: bool = True
    
    # セキュリティヘッダー
    SECURITY_HEADERS: bool = True
    
    # 本番データベース
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # ログレベル
    LOG_LEVEL: str = "WARNING"
```

#### **2. シークレット管理**

```bash
# 環境変数での秘密情報管理
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL="postgresql://user:$(cat /var/secrets/db_password)@db-host:5432/app"
export REDIS_PASSWORD=$(cat /var/secrets/redis_password)

# Docker Secretsの使用
version: '3.8'
services:
  app:
    image: your-app:latest
    secrets:
      - db_password
      - jwt_secret
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/app
secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

#### **3. 監査とモニタリング**

```python
# セキュリティイベントの監査ログ
class SecurityAuditLogger:
    def __init__(self):
        self.audit_logger = structlog.get_logger("security.audit")
    
    async def log_login_attempt(self, email: str, ip: str, success: bool, **kwargs):
        self.audit_logger.info(
            "login_attempt",
            email=email,
            ip_address=ip,
            success=success,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    async def log_password_reset(self, email: str, ip: str, **kwargs):
        self.audit_logger.info(
            "password_reset_requested",
            email=email,
            ip_address=ip,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    async def log_privilege_escalation(self, user_id: int, action: str, **kwargs):
        self.audit_logger.warning(
            "privilege_escalation_attempt",
            user_id=user_id,
            action=action,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
```

### 開発効率化

#### **1. 開発環境でのテストユーザー作成**

```python
# scripts/create_test_users.py
async def create_test_users():
    """開発環境用のテストユーザーを作成"""
    users = [
        {
            "email": "admin@test.com",
            "password": "admin123",
            "full_name": "Admin User",
            "is_superuser": True
        },
        {
            "email": "user@test.com", 
            "password": "user123",
            "full_name": "Regular User",
            "is_superuser": False
        }
    ]
    
    for user_data in users:
        user = await user_service.create_user(
            UserCreate(**user_data), 
            db
        )
        logger.info(f"Created test user: {user.email}")

# 実行
if __name__ == "__main__":
    asyncio.run(create_test_users())
```

#### **2. API テスト自動化**

```python
# tests/test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthAPI:
    def test_user_registration(self):
        """ユーザー登録テスト"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        })
        assert response.status_code == 201
        assert response.json()["message"] == "User registered successfully"
    
    def test_user_login(self):
        """ログインテスト"""
        # 事前にユーザー作成
        self.test_user_registration()
        
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_rate_limiting(self):
        """ログイン試行制限テスト"""
        # 5回失敗試行
        for i in range(5):
            response = client.post("/api/v1/auth/login", data={
                "username": "test@example.com",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # 6回目でロックアウト
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
        assert "retry-after" in response.headers
    
    def test_password_reset_flow(self):
        """パスワードリセットフローテスト"""
        # リセット要求
        response = client.post("/api/v1/auth/password-reset/request", json={
            "email": "test@example.com"
        })
        assert response.status_code == 200
        
        # 実際の環境ではメールからトークンを取得
        # テスト環境ではデータベースから直接取得
        # reset_token = get_latest_reset_token("test@example.com")
        
        # リセット実行
        # response = client.post("/api/v1/auth/password-reset/confirm", json={
        #     "token": reset_token,
        #     "new_password": "newpassword123"
        # })
        # assert response.status_code == 200
```

#### **3. OpenAPI仕様書の活用**

```python
# main.pyでOpenAPI設定をカスタマイズ
app = FastAPI(
    title="KOIKI Framework API",
    description="Enterprise-grade authentication API",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication - Basic",
            "description": "Login, registration, logout, user information"
        },
        {
            "name": "Authentication - Password", 
            "description": "Password management operations"
        },
        {
            "name": "Authentication - Token",
            "description": "Token management operations"
        }
    ]
)

# カスタムOpenAPIスキーマ
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="KOIKI Framework API",
        version="1.0.0",
        description="Complete authentication system with security features",
        routes=app.routes,
    )
    
    # セキュリティスキーマの追加
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 運用ベストプラクティス

#### **1. ヘルスチェック**

```python
# health/auth_health.py
@router.get("/health/auth")
async def auth_health_check(db: DBSessionDep):
    """認証システムのヘルスチェック"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # データベース接続確認
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    try:
        # JWT秘密鍵確認
        if settings.SECRET_KEY == "development_secret_key":
            health_status["checks"]["jwt_secret"] = "warning: using development key"
        else:
            health_status["checks"]["jwt_secret"] = "ok"
    except Exception as e:
        health_status["checks"]["jwt_secret"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis接続確認（有効な場合）
    if settings.REDIS_ENABLED:
        try:
            redis_client = request.app.state.redis
            await redis_client.ping()
            health_status["checks"]["redis"] = "ok"
        except Exception as e:
            health_status["checks"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status
```

#### **2. メトリクス収集**

```python
# monitoring/auth_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# メトリクス定義
login_attempts = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status', 'method']
)

login_duration = Histogram(
    'auth_login_duration_seconds',
    'Login request duration'
)

active_tokens = Gauge(
    'auth_active_tokens_total',
    'Number of active tokens'
)

failed_attempts_by_ip = Counter(
    'auth_failed_attempts_by_ip_total',
    'Failed login attempts by IP',
    ['ip_range']
)

# メトリクス記録例
async def record_login_metrics(success: bool, duration: float, ip: str):
    status = "success" if success else "failure"
    login_attempts.labels(status=status, method="password").inc()
    login_duration.observe(duration)
    
    if not success:
        ip_range = get_ip_range(ip)  # IPレンジの分類
        failed_attempts_by_ip.labels(ip_range=ip_range).inc()
```

#### **3. バックアップ戦略**

```bash
#!/bin/bash
# scripts/backup_auth_data.sh

# 認証関連テーブルのバックアップ
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --table=users \
  --table=refresh_tokens \
  --table=password_reset_tokens \
  --table=login_attempts \
  --table=roles \
  --table=permissions \
  --table=user_roles \
  --table=role_permissions \
  > auth_backup_$(date +%Y%m%d_%H%M%S).sql

# S3へのアップロード
aws s3 cp auth_backup_*.sql s3://your-backup-bucket/auth/

# 古いバックアップの削除（30日以上）
find . -name "auth_backup_*.sql" -mtime +30 -delete
```

---

## まとめ

KOIKI-FWの認証系APIは、現代的なWebアプリケーションに必要な全ての機能を提供します：

### **実装済み機能**
- ✅ JWT ベースの認証
- ✅ リフレッシュトークン管理
- ✅ パスワードリセット機能
- ✅ ログイン試行制限
- ✅ 段階的遅延によるブルートフォース対策
- ✅ 包括的な監査ログ
- ✅ 役割ベースアクセス制御 (RBAC)

### **セキュリティ機能**
- 🛡️ 多層防御アーキテクチャ
- 🛡️ レート制限とアカウントロックアウト
- 🛡️ セキュアなパスワードハッシュ化
- 🛡️ トークンローテーション
- 🛡️ 詳細な監査ログ

### **開発者体験**
- 🚀 FastAPIによる自動OpenAPI仕様生成
- 🚀 型安全なPydanticスキーマ
- 🚀 依存性注入による高いテスタビリティ
- 🚀 構造化ログによる運用性

本ガイドに従って実装することで、企業級のセキュリティ要件を満たす認証システムを構築できます。

## セキュリティ強化対応記録

### 2025年7月8日 - 認証APIセキュリティ強化対応

認証系APIの包括的なセキュリティ強化を実施しました。詳細は [認証APIセキュリティ強化対応記録](./authentication-api-security-fixes.md) を参照してください。

**主要な改善内容**:
- 🔥 **非同期処理の最適化**: `time.sleep()` → `asyncio.sleep()` による性能向上
- 🕒 **タイムゾーン統一**: UTC時間の一貫した使用によるデータ整合性確保
- ⚡ **データベース処理最適化**: バッチ削除による大幅な性能向上
- 🔒 **タイミング攻撃対策**: 一定応答時間による情報漏洩防止
- 📊 **セキュリティログ強化**: 構造化ログによる包括的な監査証跡
- 📈 **監視機能追加**: リアルタイムメトリクス収集と分析
- ⚙️ **設定外部化**: 環境変数による動的設定管理

**新機能**:
- `/security/metrics` - セキュリティメトリクス確認（管理者限定）
- `/security/health` - システムヘルスチェック（認証不要）
- 環境変数での詳細設定（`SECURITY_*` プレフィックス）

これらの改善により、認証システムのセキュリティ、パフォーマンス、運用性が大幅に向上し、本番環境での安全な運用が可能になりました。

---

*最終更新: 2025-07-08*  
*対象バージョン: KOIKI-FW v0.6.0*  
*セキュリティ強化: v0.5.1 対応済み*