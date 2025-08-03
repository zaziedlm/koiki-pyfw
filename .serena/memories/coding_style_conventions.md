# コードスタイルと規約

## Python コーディング規約

### 基本スタイル
- **型ヒント**: 必須 - 全ての関数・メソッドに型ヒントを記述
- **docstring**: クラスとメソッドには日本語のdocstringを記述
- **インポート順序**: 標準ライブラリ → サードパーティ → ローカルモジュール

### ネーミング規約
```python
# クラス: PascalCase
class UserService:
    pass

# 関数・変数: snake_case
async def get_user_by_id(user_id: int) -> Optional[UserModel]:
    pass

# 定数: UPPER_SNAKE_CASE
REDIS_AVAILABLE = True

# プライベート: アンダースコア接頭辞
_logging_configured = False
```

### 依存性注入パターン
```python
# サービスクラスの典型的な構造
class UserService:
    """ユーザー関連のビジネスロジックを処理するサービスクラス"""
    
    def __init__(
        self,
        repository: UserRepository,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.repository = repository
        self.event_publisher = event_publisher
```

### 非同期処理規約
- **async/await**: 全てのI/O処理は非同期で実装
- **型ヒント**: `AsyncSession`, `AsyncGenerator`等の適切な使用
- **トランザクション**: `@transactional`デコレータを使用

### ログ出力規約
```python
import structlog

logger = structlog.get_logger(__name__)

# 構造化ログで情報を記録
logger.debug("Service: Getting user by ID", user_id=user_id)
logger.info("User successfully created", user_id=user.id, username=user.username)
```

### エラーハンドリング
```python
# カスタム例外の使用
from libkoiki.core.exceptions import ResourceNotFoundException, ValidationException

# 適切な例外の使い分け
if not user:
    raise ResourceNotFoundException(resource_name="User", resource_id=user_id)
```

## TypeScript/JavaScript コーディング規約

### 基本スタイル
- **TypeScript**: 厳密な型定義を使用
- **関数型コンポーネント**: React Hook使用
- **ES6+**: モダンなJavaScript構文

### ファイル構成（Next.js）
```
src/
├── app/              # App Router (Next.js 13+)
├── components/       # 再利用可能なコンポーネント
│   ├── ui/          # 基本UIコンポーネント
│   ├── auth/        # 認証関連コンポーネント
│   └── layout/      # レイアウトコンポーネント
├── hooks/           # カスタムフック
├── lib/             # ユーティリティ・設定
├── stores/          # 状態管理（Zustand）
└── types/           # TypeScript型定義
```

### ネーミング規約
```typescript
// コンポーネント: PascalCase
const LoginForm = () => {}

// 関数・変数: camelCase
const getUserData = async () => {}

// 定数: UPPER_SNAKE_CASE
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

// 型定義: PascalCase (T接頭辞なし)
interface User {
  id: number
  username: string
}
```

## エディタ設定（.editorconfig）

```ini
# 全ファイル共通
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

# Python特有設定
[*.py]
indent_size = 4

# TypeScript/JavaScript
[*.{ts,tsx,js,jsx}]
indent_size = 2

# JSON・YAML
[*.{json,yml,yaml}]
indent_size = 2

# Markdownは末尾スペース保持
[*.md]
trim_trailing_whitespace = false
```

## プロジェクト構造規約

### レイヤー分離（Python）
```
API層 (FastAPI endpoints)
    ↓
サービス層 (Business Logic)
    ↓  
リポジトリ層 (Data Access)
    ↓
モデル層 (Database Models)
```

### コンポーネント設計（React）
- **単一責任の原則**: 1コンポーネント1責任
- **Propsの型定義**: 厳密なTypeScript型
- **カスタムフック**: ロジックの分離・再利用

## テストファイル規約

### Python テスト
```python
# テストファイル名: test_*.py
# テストクラス: Test*
# テストメソッド: test_*

class TestUserService:
    async def test_get_user_by_id_success(self):
        # Arrange, Act, Assert パターン
        pass
```

### TypeScript テスト
```typescript
// テストファイル名: *.test.ts, *.spec.ts
describe('UserService', () => {
  it('should get user by id successfully', () => {
    // テスト実装
  })
})
```

## Git コミットメッセージ規約

```
# 推奨フォーマット
feat: 新機能追加の説明
fix: バグ修正の説明
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
test: テスト追加・修正
chore: ビルド・設定変更
```