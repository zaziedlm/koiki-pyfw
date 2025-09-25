# app/schemas/sso.py
"""
SSO (Single Sign-On) 認証関連のPydanticスキーマ

OpenID Connect (OIDC) による外部認証サービスとの連携で使用する
リクエスト・レスポンス・データ転送オブジェクトを定義
"""
from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, Field


class SSOLoginRequest(BaseModel):
    """
    SSO ログインリクエスト

    Authorization Code Flow (PKCE) で得たコードをサーバー側で交換し、
    IDトークンを検証した上で内部認証を成立させる
    """

    authorization_code: str = Field(..., description="Authorization Code Flow で取得したコード")
    code_verifier: str = Field(..., description="PKCE用のcode_verifier")
    redirect_uri: AnyHttpUrl = Field(..., description="認可リクエストで使用したredirect_uri")
    nonce: str = Field(..., description="認可リクエストで用いたnonce")
    state: str = Field(..., description="認可リクエスト時に発行されたstateトークン")

    class Config:
        json_schema_extra = {
            "example": {
                "authorization_code": "SplxlOBeZQQYbYS6WxSbIA",
                "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
                "redirect_uri": "https://app.example.com/sso/callback",
                "nonce": "n-0S6_WzA2Mj",
                "state": "eyJub25jZSI6ICJuLTBTNl9XekEyTWoiLCAidHMiOiAxNzMyMzAxNjAwfQ.ygIh2L4y-4V..."
            }
        }


class SSOAuthorizationInitResponse(BaseModel):
    """認可リクエスト開始時に必要な情報"""

    authorization_endpoint: AnyHttpUrl = Field(..., description="HENNGE SSOの認可エンドポイント")
    authorization_base_url: AnyHttpUrl = Field(..., description="code_challengeを付与する前提の基本URL")
    response_type: str = Field(..., description="レスポンスタイプ。通常は 'code'")
    client_id: str = Field(..., description="OIDCクライアントID")
    redirect_uri: AnyHttpUrl = Field(..., description="使用されるredirect_uri")
    scope: str = Field(..., description="付与されるスコープ")
    state: str = Field(..., description="署名済みstateトークン")
    nonce: str = Field(..., description="認可リクエストで利用するnonce")
    expires_at: datetime = Field(..., description="state/nonceの有効期限")
    code_challenge_method: str = Field(..., description="推奨するPKCE code_challenge_method")

    class Config:
        json_schema_extra = {
            "example": {
                "authorization_endpoint": "https://idp.example.com/oauth2/authorize",
                "authorization_base_url": "https://idp.example.com/oauth2/authorize?response_type=code&client_id=client-id&redirect_uri=https%3A%2F%2Fapp.example.com%2Fsso%2Fcallback&scope=openid+email+profile&state=eyJub25jZSI6Ii4uLiIsInRzIjoxNzMyMzA3MjAwfQ.abc&nonce=nonce-value",
                "response_type": "code",
                "client_id": "client-id",
                "redirect_uri": "https://app.example.com/sso/callback",
                "scope": "openid email profile",
                "state": "eyJub25jZSI6Ii4uLiIsInRzIjoxNzMyMzA3MjAwfQ.abc",
                "nonce": "nonce-value",
                "expires_at": "2024-11-01T12:00:00Z",
                "code_challenge_method": "S256",
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
