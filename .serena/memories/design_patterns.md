# 設計パターンとアーキテクチャガイドライン

## アーキテクチャパターン

### 1. レイヤー分離アーキテクチャ（Clean Architecture準拠）

```
┌─────────────────────────────────────────┐
│ Frontend (Next.js + TypeScript)        │ ← Presentation Layer
├─────────────────────────────────────────┤
│ API Layer (FastAPI Endpoints)          │ ← Interface Layer
├─────────────────────────────────────────┤
│ Service Layer (Business Logic)         │ ← Application Layer
├─────────────────────────────────────────┤
│ Repository Layer (Data Access)         │ ← Infrastructure Layer
├─────────────────────────────────────────┤
│ Model Layer (Database Models)          │ ← Domain Layer
└─────────────────────────────────────────┘
```

### 2. 依存性注入パターン（FastAPI Depends）

```python
# サービス層での依存性注入例
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.repository = repository
        self.event_publisher = event_publisher

# APIエンドポイントでの依存性注入
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserServiceDep,  # 自動注入
    db: DBSessionDep,              # 自動注入
):
    return await user_service.create_user(user_data, db)
```

## 重要な設計原則

### 1. 非同期ファーストアプローチ

```python
# 全てのI/O処理は非同期で実装
async def get_user_by_id(
    self, 
    user_id: int, 
    db: AsyncSession
) -> Optional[UserModel]:
    """非同期でのデータベースアクセス"""
    self.repository.set_session(db)
    return await self.repository.get(user_id)
```

### 2. 型安全性の徹底

```python
# 完全な型ヒント使用
from typing import Optional, Sequence

async def get_users(
    self, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession
) -> Sequence[UserModel]:
    """型安全なメソッド定義"""
    pass
```

### 3. 構造化ログパターン

```python
import structlog

logger = structlog.get_logger(__name__)

class UserService:
    async def create_user(self, user_data: UserCreate, db: AsyncSession):
        logger.info("Starting user creation", username=user_data.username)
        
        try:
            # ビジネスロジック実行
            user = await self._create_user_logic(user_data, db)
            logger.info("User created successfully", 
                       user_id=user.id, 
                       username=user.username)
            return user
        except Exception as e:
            logger.error("User creation failed", 
                        username=user_data.username, 
                        error=str(e))
            raise
```

## セキュリティ設計パターン

### 1. 多層セキュリティアーキテクチャ

```python
# 認証レイヤー
@router.post("/protected")
async def protected_endpoint(
    current_user: CurrentUserDep,  # JWT認証
    _: Annotated[None, Depends(has_permission("read:users"))],  # 権限認可
    request: Request,
    limiter: LimiterDep = Depends(get_limiter),  # レートリミット
):
    # ビジネスロジック
    pass
```

### 2. RBAC（Role-Based Access Control）実装

```python
# 権限チェックデコレータ
def has_permission(required_permission: str):
    async def check_permission(
        current_user: UserModel = Depends(get_current_active_user)
    ):
        if not user_has_permission(current_user, required_permission):
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions"
            )
        return current_user
    return check_permission
```

### 3. セキュリティ監査ログ

```python
# セキュリティイベントの統一ログ
class SecurityLogger:
    def log_auth_attempt(self, username: str, success: bool, ip: str):
        self.audit_logger.info(
            "Authentication attempt",
            event_type="auth_attempt",
            username=username,
            success=success,
            client_ip=ip,
            timestamp=datetime.utcnow().isoformat()
        )
```

## フロントエンド設計パターン

### 1. コンポーネント設計パターン

```typescript
// 単一責任の原則に従ったコンポーネント設計
interface LoginFormProps {
  onLogin: (credentials: LoginCredentials) => Promise<void>
  isLoading?: boolean
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, isLoading = false }) => {
  // コンポーネントロジック
}
```

### 2. カスタムフック パターン

```typescript
// ビジネスロジックの分離・再利用
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  
  const login = useCallback(async (credentials: LoginCredentials) => {
    // 認証ロジック
  }, [])
  
  const logout = useCallback(() => {
    // ログアウトロジック
  }, [])
  
  return { user, login, logout }
}
```

### 3. 状態管理パターン（Zustand）

```typescript
// 型安全な状態管理
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  token: null,
  login: async (credentials) => {
    // ログイン処理
  },
  logout: () => {
    // ログアウト処理
  }
}))
```

## エラーハンドリングパターン

### 1. バックエンド例外処理

```python
# カスタム例外の階層的設計
from libkoiki.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    AuthenticationException
)

class UserService:
    async def get_user_by_id(self, user_id: int) -> UserModel:
        user = await self.repository.get(user_id)
        if not user:
            raise ResourceNotFoundException(
                resource_name="User", 
                resource_id=user_id
            )
        return user
```

### 2. フロントエンド エラーハンドリング

```typescript
// 統一されたエラーハンドリング
export const useApiError = () => {
  const handleError = useCallback((error: unknown) => {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          // 認証エラー処理
          break
        case 403:
          // 認可エラー処理
          break
        case 404:
          // リソース未発見エラー処理
          break
        default:
          // 一般的なエラー処理
      }
    }
  }, [])
  
  return { handleError }
}
```

## パフォーマンス最適化パターン

### 1. データベース最適化

```python
# N+1問題の回避
async def get_users_with_roles(self) -> Sequence[UserModel]:
    query = select(UserModel).options(
        selectinload(UserModel.roles).selectinload(RoleModel.permissions)
    )
    result = await self.session.execute(query)
    return result.scalars().all()
```

### 2. キャッシュ戦略

```python
# Redisキャッシュパターン
async def get_user_cached(self, user_id: int) -> Optional[UserModel]:
    cache_key = f"user:{user_id}"
    
    # キャッシュから取得試行
    cached_user = await self.redis_client.get(cache_key)
    if cached_user:
        return UserModel.parse_raw(cached_user)
    
    # データベースから取得してキャッシュに保存
    user = await self.repository.get(user_id)
    if user:
        await self.redis_client.set(
            cache_key, 
            user.json(), 
            ex=3600  # 1時間のTTL
        )
    return user
```

## テスト設計パターン

### 1. テスト分離パターン

```python
# 単体テスト：モックを使用した分離テスト
@pytest.mark.asyncio
async def test_user_service_create_user_success(mock_user_repo):
    # Arrange
    user_service = UserService(repository=mock_user_repo)
    user_data = UserCreate(username="test", email="test@example.com")
    
    # Act
    result = await user_service.create_user(user_data, mock_db_session)
    
    # Assert
    assert result.username == "test"
    mock_user_repo.create.assert_called_once()
```

### 2. 統合テストパターン

```python
# 統合テスト：実際のデータベースを使用
@pytest.mark.asyncio
async def test_auth_api_integration(test_client, test_db):
    # 実際のHTTPリクエストでAPIをテスト
    response = await test_client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 拡張性・保守性の考慮

### 1. プラグインアーキテクチャ

```python
# イベントドリブン設計による疎結合
class EventPublisher:
    async def publish(self, event_type: str, payload: dict):
        # イベントの発行（Redis Pub/Sub）
        await self.redis_client.publish(event_type, json.dumps(payload))

# 他のサービスでイベント購読
async def handle_user_created(payload: dict):
    # ユーザー作成イベントの処理
    await send_welcome_email_task.delay(payload["user_id"])
```

### 2. 設定ベースの機能切り替え

```python
# 機能フラグパターン
class Settings(BaseSettings):
    REDIS_ENABLED: bool = True
    EMAIL_ENABLED: bool = True
    MONITORING_ENABLED: bool = True
    
    # 環境ごとの設定切り替え
    class Config:
        env_file = ".env"
```