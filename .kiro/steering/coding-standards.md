# コーディング規約

## 基本原則

KOIKI-FWでは、保守性、可読性、拡張性を重視したコーディング規約を採用しています。

## Python コーディング規約

### PEP 8準拠
- **インデント**: 4スペース（タブ禁止）
- **行長**: 88文字以内（Black準拠）
- **命名規則**: snake_case（関数、変数）、PascalCase（クラス）

### 型ヒント必須
```python
from typing import Optional, List, Dict, Any

def get_user_by_id(user_id: int) -> Optional[User]:
    """ユーザーIDでユーザーを取得"""
    return user_repository.get_by_id(user_id)

async def create_users(users_data: List[Dict[str, Any]]) -> List[User]:
    """複数ユーザーを作成"""
    return await user_service.create_multiple(users_data)
```

### docstring規約
```python
def calculate_total_price(items: List[Item], tax_rate: float = 0.1) -> float:
    """商品リストの合計金額を計算
    
    Args:
        items: 商品リスト
        tax_rate: 税率（デフォルト: 0.1）
        
    Returns:
        税込み合計金額
        
    Raises:
        ValueError: 税率が負の値の場合
    """
    if tax_rate < 0:
        raise ValueError("税率は0以上である必要があります")
    
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

### エラーハンドリング
```python
from libkoiki.core.exceptions import ValidationError, NotFoundError

async def update_user(user_id: int, user_data: UserUpdate) -> User:
    """ユーザー情報を更新"""
    try:
        user = await user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"ユーザーID {user_id} が見つかりません")
        
        updated_user = await user_repository.update(user_id, user_data)
        return updated_user
        
    except ValidationError as e:
        logger.error("ユーザー更新バリデーションエラー", error=str(e))
        raise
    except Exception as e:
        logger.error("ユーザー更新エラー", error=str(e))
        raise
```

## FastAPI 規約

### ルーター構成
```python
from fastapi import APIRouter, Depends, HTTPException, status
from libkoiki.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """ユーザー詳細取得"""
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    return UserResponse.from_orm(user)
```

### Pydanticスキーマ
```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """ユーザーベーススキーマ"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """ユーザー作成スキーマ"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class UserResponse(UserBase):
    """ユーザーレスポンススキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

## TypeScript/React 規約

### 命名規則
```typescript
// コンポーネント: PascalCase
export function UserProfile({ userId }: UserProfileProps) {
  return <div>...</div>;
}

// フック: camelCase with 'use' prefix
export function useUserData(userId: number) {
  return useQuery(['user', userId], () => fetchUser(userId));
}

// 型定義: PascalCase
interface UserProfileProps {
  userId: number;
  onUpdate?: (user: User) => void;
}

// 定数: UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### コンポーネント構造
```typescript
'use client';

import { useState, useEffect } from 'react';
import { User } from '@/types/user';
import { Button } from '@/components/ui/button';

interface UserProfileProps {
  userId: number;
  onUpdate?: (user: User) => void;
}

export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUserData();
  }, [userId]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const userData = await api.get(`/users/${userId}`);
      setUser(userData);
    } catch (err) {
      setError('ユーザーデータの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div>エラー: {error}</div>;
  if (!user) return <div>ユーザーが見つかりません</div>;

  return (
    <div className="user-profile">
      <h2>{user.full_name || user.username}</h2>
      <p>{user.email}</p>
      <Button onClick={() => onUpdate?.(user)}>
        更新
      </Button>
    </div>
  );
}
```

### API型定義
```typescript
// types/api.ts
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

// APIクライアント
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
}
```

## データベース規約

### SQLAlchemyモデル
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from libkoiki.db.base import Base

class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    todos = relationship("Todo", back_populates="owner")
    user_roles = relationship("UserRole", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
```

### マイグレーション規約
```python
"""ユーザーテーブルにfull_nameカラム追加

Revision ID: 001_add_user_full_name
Revises: 000_initial
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_add_user_full_name'
down_revision = '000_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """マイグレーション適用"""
    op.add_column('users', sa.Column('full_name', sa.String(100), nullable=True))

def downgrade() -> None:
    """マイグレーション取り消し"""
    op.drop_column('users', 'full_name')
```

## テスト規約

### pytest規約
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from libkoiki.models.user import User
from tests.conftest import test_db_session

class TestUserAPI:
    """ユーザーAPI テストクラス"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

    @pytest.fixture
    async def test_user(self, test_db_session: AsyncSession):
        """テスト用ユーザー"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        return user

    async def test_get_user_success(self, client: TestClient, test_user: User):
        """ユーザー取得成功テスト"""
        response = client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    async def test_get_user_not_found(self, client: TestClient):
        """ユーザー取得失敗テスト"""
        response = client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "ユーザーが見つかりません" in response.json()["detail"]
```

## ログ規約

### 構造化ログ
```python
import structlog

logger = structlog.get_logger(__name__)

async def create_user(user_data: UserCreate) -> User:
    """ユーザー作成"""
    logger.info(
        "ユーザー作成開始",
        username=user_data.username,
        email=user_data.email
    )
    
    try:
        user = await user_repository.create(user_data)
        logger.info(
            "ユーザー作成成功",
            user_id=user.id,
            username=user.username
        )
        return user
        
    except Exception as e:
        logger.error(
            "ユーザー作成失敗",
            username=user_data.username,
            error=str(e),
            exc_info=True
        )
        raise
```

## コードレビュー規約

### レビューポイント
- [ ] 型ヒントが適切に設定されている
- [ ] エラーハンドリングが実装されている
- [ ] セキュリティ要件を満たしている
- [ ] テストが適切に書かれている
- [ ] ドキュメントが更新されている
- [ ] パフォーマンスに問題がない
- [ ] 命名規則に従っている

### コミットメッセージ規約
```
feat: ユーザー管理機能を追加
fix: ログイン時のバリデーションエラーを修正
docs: APIドキュメントを更新
test: ユーザー作成テストを追加
refactor: 認証ミドルウェアをリファクタリング

# フルスタック対応
feat(frontend): ダッシュボードUIを追加
feat(backend): ユーザーAPIエンドポイントを追加
fix(integration): Cookie認証の統合問題を修正
```

## フルスタック開発規約

### API統合規約

#### バックエンドAPI実装
```python
# libkoiki/api/v1/endpoints/users.py
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """ユーザー詳細取得"""
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return UserResponse.from_orm(user)
```

#### フロントエンドAPI Route Handler
```typescript
// frontend/src/app/api/users/[id]/route.ts
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${getBackendApiUrl()}/users/${params.id}`, {
    credentials: 'include',
    headers: getAuthHeaders(request),
  });
  
  return NextResponse.json(await response.json(), {
    status: response.status,
  });
}
```

#### TypeScript型定義
```typescript
// frontend/src/types/user.ts
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserResponse extends User {
  roles?: Role[];
}
```

### 統合テスト規約

#### E2Eテスト（Playwright）
```typescript
// frontend/tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('ログインフロー', async ({ page }) => {
  await page.goto('/auth/login');
  
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password123');
  await page.click('[data-testid="login-button"]');
  
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
});
```

#### 統合テスト（pytest + httpx）
```python
# tests/integration/test_auth_integration.py
async def test_login_flow(client: AsyncClient):
    """ログインフローの統合テスト"""
    # ユーザー作成
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    
    # ログイン
    login_response = await client.post("/api/v1/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

### 状態管理規約

#### TanStack Query使用規約
```typescript
// frontend/src/hooks/use-user-queries.ts
export function useUser(userId: number) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => userApi.getById(userId),
    staleTime: 5 * 60 * 1000, // 5分
    enabled: !!userId,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: userApi.update,
    onSuccess: (data) => {
      queryClient.setQueryData(['user', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

### エラーハンドリング統合規約

#### バックエンドエラー
```python
# libkoiki/core/exceptions.py
class APIException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
```

#### フロントエンドエラー処理
```typescript
// frontend/src/lib/error-handler.ts
export function handleApiError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return String(error.detail);
  }
  
  return '予期しないエラーが発生しました';
}
```