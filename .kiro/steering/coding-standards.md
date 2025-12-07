# コーディング規約

## Python

### 基本ルール
- **PEP 8準拠**: インデント4スペース、行長88文字（Black準拠）
- **型ヒント必須**: 全ての関数に型アノテーション
- **命名規則**: snake_case（関数/変数）、PascalCase（クラス）

### 例
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_id(
    user_id: int, 
    db: AsyncSession
) -> Optional[UserModel]:
    """ユーザーIDでユーザーを取得"""
    return await user_repository.get_by_id(db, user_id)
```

### FastAPI エンドポイント
```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """ユーザー詳細取得"""
    ...
```

### Pydantic スキーマ
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上')
        return v
```

## TypeScript/React

### 命名規則
- **コンポーネント**: PascalCase (`UserProfile.tsx`)
- **フック**: camelCase + use prefix (`useAuth.ts`)
- **型定義**: PascalCase (`interface UserProps`)
- **定数**: UPPER_SNAKE_CASE

### コンポーネント構造
```typescript
'use client';

import { useState } from 'react';
import { User } from '@/types/user';

interface UserProfileProps {
  userId: number;
}

export function UserProfile({ userId }: UserProfileProps) {
  const { data, isLoading } = useUser(userId);
  
  if (isLoading) return <Loading />;
  return <div>{data?.name}</div>;
}
```

### API統合パターン
```typescript
// hooks/use-user-queries.ts
export function useUser(userId: number) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
    staleTime: 5 * 60 * 1000,
  });
}
```

## インポート規則

### Python（絶対インポート推奨）
```python
from libkoiki.models.user import UserModel
from libkoiki.services.auth_service import AuthService
from app.services.sso_service import SSOService
```

### TypeScript
```typescript
import { config } from '@/lib/config';
import { User } from '@/types/user';
import { Button } from '@/components/ui/button';
```

## エラーハンドリング

### バックエンド
```python
from libkoiki.core.exceptions import ValidationException
from fastapi import HTTPException, status

try:
    result = await service.process(data)
except ValidationException as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### フロントエンド
```typescript
try {
  const response = await cookieApiClient.fetchWithCredentials(url);
  if (!response.ok) throw new Error('API Error');
} catch (error) {
  // エラー通知
}
```

## ログ規約

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("処理開始", user_id=user.id, action="create")
logger.error("処理失敗", error=str(e), exc_info=True)
```

## コミットメッセージ

```
feat: ユーザー管理機能を追加
fix: ログイン時のバリデーションエラーを修正
docs: APIドキュメントを更新
test: ユーザー作成テストを追加
refactor: 認証ミドルウェアをリファクタリング
```
