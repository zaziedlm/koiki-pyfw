# src/api/v1/endpoints/auth.py
"""
認証系APIの統合ルーター

機能別に分割されたエンドポイントを統合します：
- auth_basic: ログイン、登録、ログアウト、現在ユーザー取得
- auth_password: パスワード変更、パスワードリセット
- auth_token: トークンリフレッシュ、全トークン無効化
"""
from fastapi import APIRouter

from . import auth_basic, auth_password, auth_token

router = APIRouter()

# 基本認証機能
router.include_router(auth_basic.router, tags=["Authentication - Basic"])

# パスワード管理機能  
router.include_router(auth_password.router, tags=["Authentication - Password"])

# トークン管理機能
router.include_router(auth_token.router, tags=["Authentication - Token"])

