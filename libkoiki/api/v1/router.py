# src/api/v1/router.py
from fastapi import APIRouter

from libkoiki.api.v1.endpoints import (  # ★ ToDo エンドポイントをインポート
    auth,
    todos,
    users,
)

api_router = APIRouter()

# 認証ルーター
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# タグは、認証系APIの統合ルーターで設定済
api_router.include_router(auth.router, prefix="/auth")
# ユーザールーター
api_router.include_router(users.router, prefix="/users", tags=["Admin Users"])
# ★ ToDo ルーター ★
api_router.include_router(todos.router, prefix="/todos", tags=["ToDos Sample"])

# 他の機能のルーターもここに追加
# api_router.include_router(items.router, prefix="/items", tags=["Items"])
