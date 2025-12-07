# フルスタック統合ガイド

## アーキテクチャ

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Next.js    │    │  FastAPI    │    │ PostgreSQL  │
│  :3000      │◄──►│  :8000      │◄──►│  :5432      │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │
       └──────────────────┼──────────────────┐
                         │                   │
              ┌─────────────┐      ┌─────────────┐
              │   Redis     │      │  Keycloak   │
              │   :6379     │      │   :8090     │
              └─────────────┘      └─────────────┘
```

## Cookie認証フロー

```
1. ユーザー → フロントエンド: ログイン情報入力
2. フロントエンド → /api/auth/login (Route Handler): POST
3. Route Handler: CSRF検証
4. Route Handler → FastAPI /api/v1/auth/login: 認証リクエスト
5. FastAPI → Route Handler: JWT + ユーザー情報
6. Route Handler: HTTPOnly Cookie設定
7. Route Handler → フロントエンド: 認証成功
```

## API統合パターン

### 1. バックエンドAPI (FastAPI)
```python
# libkoiki/api/v1/endpoints/todos.py
@router.get("/", response_model=List[TodoResponse])
async def get_todos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await todo_service.get_user_todos(db, current_user.id)
```

### 2. フロントエンドプロキシ (Route Handler)
```typescript
// frontend/src/app/api/todos/route.ts
export async function GET(request: NextRequest) {
  const response = await fetch(`${getBackendApiUrl()}/todos`, {
    headers: getAuthHeaders(request),
  });
  return NextResponse.json(await response.json());
}
```

### 3. カスタムフック
```typescript
// frontend/src/hooks/use-cookie-todo-queries.ts
export function useTodos() {
  return useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const res = await cookieTodoApi.getAll();
      return res.json();
    },
  });
}
```

### 4. コンポーネント
```typescript
// frontend/src/components/tasks/task-list.tsx
export function TaskList() {
  const { data: todos, isLoading } = useTodos();
  if (isLoading) return <Loading />;
  return todos?.map(todo => <TaskItem key={todo.id} todo={todo} />);
}
```

## CSRF保護

```typescript
// cookie-api-client.ts
class CookieApiClient {
  async fetchWithCredentials(url: string, options: RequestInit) {
    return fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'x-csrf-token': this.csrfToken,
        ...options.headers,
      },
    });
  }
}
```

## SSO統合フロー

```
1. フロントエンド: /api/sso/authorization 呼び出し
2. バックエンド: state/nonce/PKCE生成、認可URL返却
3. フロントエンド: IdP (Keycloak) へリダイレクト
4. IdP: 認証後、authorization_code と共にコールバック
5. フロントエンド: /api/sso/login でコード交換
6. バックエンド: IDトークン検証、ユーザー認証/作成
7. バックエンド: 内部JWT発行
8. フロントエンド: Cookie設定、ダッシュボードへ
```

## 開発環境

```bash
# フルスタック起動（Docker）
docker-compose up --build -d

# 個別起動
# バックエンド
poetry run uvicorn app.main:app --reload --port 8000

# フロントエンド
cd frontend && npm run dev

# Keycloak管理画面
http://localhost:8090 (admin/admin)
```

## 環境変数

### バックエンド (.env)
```
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dbname
SECRET_KEY=your-secret-key
SSO_CLIENT_ID=koiki-app
SSO_AUTHORIZATION_ENDPOINT=http://localhost:8090/realms/koiki/protocol/openid-connect/auth
```

### フロントエンド (frontend/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_PREFIX=/api/v1
NEXT_PUBLIC_SSO_REDIRECT_URI=/sso/callback
```
