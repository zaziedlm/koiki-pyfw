# app/api/v1/router.py
"""
アプリケーション固有 API v1 ルーター

libkoikiの標準APIに加えて、アプリケーション固有のAPIエンドポイントを統合
現在はSSO認証機能（OIDC・SAML）を提供
"""
from fastapi import APIRouter

from .endpoints import sso_auth, saml_auth

# アプリケーション固有のAPIルーター
router = APIRouter()

# SSO認証エンドポイント（OIDC）
router.include_router(
    sso_auth.router,
    prefix="/auth",
    tags=["SSO Authentication"]
)

# SAML認証エンドポイント
router.include_router(
    saml_auth.router,
    prefix="/auth",
    tags=["SAML Authentication"]
)

# 今後の拡張用:
# - アプリ固有の管理機能
# - カスタムダッシュボード
# - 外部サービス連携
# - 特殊レポート機能
# 等を追加予定