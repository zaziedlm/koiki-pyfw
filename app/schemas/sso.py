# app/schemas/sso.py
"""
SSO (Single Sign-On) 認証関連のPydanticスキーマ

OpenID Connect (OIDC) による外部認証サービスとの連携で使用する
リクエスト・レスポンス・データ転送オブジェクトを定義
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field



class SSOLoginRequest(BaseModel):
    """
    SSO ログインリクエスト

    BFF 側で ID トークン検証を済ませ、本 API にはリソースサーバー向けの OAuth2 アクセストークンのみを渡す想定。
    JSON ボディまたは `application/x-www-form-urlencoded` でアクセストークンを受け取る。
    """
    access_token: str = Field(..., description="OAuth 2.0 access token")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }



class SSOUserInfo(BaseModel):
    """
    SSO ユーザー情報
    
    IDトークンから抽出されるユーザー情報を表現
    OpenID Connect 標準クレームに基づく
    """
    sub: str = Field(..., description="SSOサービスでの一意ユーザー識別子")
    email: str = Field(..., description="メールアドレス")
    email_verified: bool = Field(default=False, description="メールアドレス検証済みフラグ")
    name: Optional[str] = Field(None, description="フルネーム")
    given_name: Optional[str] = Field(None, description="名")
    family_name: Optional[str] = Field(None, description="姓") 
    preferred_username: Optional[str] = Field(None, description="希望ユーザー名")
    picture: Optional[str] = Field(None, description="プロフィール画像URL")
    locale: Optional[str] = Field(None, description="ロケール設定")

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "1234567890",
                "email": "user@example.com",
                "email_verified": True,
                "name": "山田太郎",
                "given_name": "太郎",
                "family_name": "山田"
            }
        }


class SSOLinkResponse(BaseModel):
    """
    SSO 連携結果レスポンス
    
    ユーザーとSSO連携の作成・更新結果を返す
    """
    message: str = Field(..., description="処理結果メッセージ")
    user_id: int = Field(..., description="連携されたユーザーID") 
    sso_subject_id: str = Field(..., description="SSO識別子")
    is_new_user: bool = Field(..., description="新規ユーザー作成フラグ")
    linked_at: datetime = Field(..., description="連携日時")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "SSO authentication successful",
                "user_id": 123,
                "sso_subject_id": "1234567890",
                "is_new_user": False,
                "linked_at": "2024-01-15T10:30:00Z"
            }
        }


class SSOUserInfoResponse(BaseModel):
    """
    SSO連携ユーザー情報レスポンス
    """
    user_id: int = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    full_name: Optional[str] = Field(None, description="フルネーム")
    sso_subject_id: str = Field(..., description="SSO識別子")
    sso_provider: str = Field(..., description="SSOプロバイダー")
    last_sso_login: Optional[datetime] = Field(None, description="最終SSO ログイン日時")
    created_at: datetime = Field(..., description="連携作成日時")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "email": "user@example.com",
                "full_name": "山田太郎",
                "sso_subject_id": "1234567890",
                "sso_provider": "oidc",
                "last_sso_login": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T09:00:00Z"
            }
        }