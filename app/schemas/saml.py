# app/schemas/saml.py
"""
SAML認証関連のPydanticスキーマ定義

SAML 2.0 認証フローで使用するリクエスト・レスポンス・ユーザー情報のスキーマを定義
OIDCのスキーマパターンに合わせて設計
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, AnyHttpUrl


class SAMLAuthorizationInitResponse(BaseModel):
    """SAML認可リクエスト開始時に必要な情報"""

    sso_url: AnyHttpUrl = Field(..., description="SAML IdP SSOエンドポイント")
    saml_request: str = Field(..., description="Base64エンコードされたSAML AuthnRequest")
    relay_state: str = Field(..., description="署名済みRelayState（セッション状態トークン）")
    expires_at: datetime = Field(..., description="RelayStateの有効期限")
    sso_binding: str = Field(default="HTTP-Redirect", description="SAML Binding方式")
    redirect_url: str = Field(..., description="RelayStateを付与済みのIdPリダイレクトURL")

    class Config:
        json_schema_extra = {
            "example": {
                "sso_url": "https://idp.example.com/saml/sso",
                "saml_request": "PHNhbWxwOkF1dGhuUmVxdWVzdCB4bWxuczpzYW1scD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOnByb3RvY29s...",
                "relay_state": "eyJub25jZSI6Ii4uLiIsInJlcSI6ImF1dGhuXzEyMyIsInRzIjoxNzMyMzA3MjAwfQ.abc",
                "expires_at": "2024-11-01T12:00:00Z",
                "sso_binding": "HTTP-Redirect",
                "redirect_url": "https://idp.example.com/saml/sso?SAMLRequest=...&RelayState=eyJub25jZSI6Ii4uLiJ9.abc"
            }
        }


class SAMLLoginTicketRequest(BaseModel):
    """SAMLログインチケット交換リクエスト"""

    login_ticket: str = Field(..., description="ACS処理で発行されたログインチケット")

    class Config:
        json_schema_extra = {
            "example": {
                "login_ticket": "ZXlKaGJHY2lPaUpTVXpJMU5pSjkuLi4"
            }
        }


class SAMLUserInfo(BaseModel):
    """
    SAML Assertionから抽出されたユーザー情報

    OIDCのSSOUserInfoと同等の役割を果たす
    """

    subject_id: str = Field(..., description="SAML NameID - ユーザーの一意識別子")
    email: str = Field(..., description="メールアドレス")
    email_verified: bool = Field(default=True, description="メール検証済みフラグ（SAMLでは通常IdP側で検証済み）")
    name: Optional[str] = Field(None, description="表示名")
    given_name: Optional[str] = Field(None, description="名")
    family_name: Optional[str] = Field(None, description="姓")
    preferred_username: Optional[str] = Field(None, description="優先ユーザー名")
    picture: Optional[str] = Field(None, description="プロフィール画像URL")
    locale: Optional[str] = Field(None, description="ロケール")
    session_index: Optional[str] = Field(None, description="SAML SessionIndex")
    attributes: Optional[Dict[str, Any]] = Field(None, description="追加のSAML属性")

    class Config:
        json_schema_extra = {
            "example": {
                "subject_id": "user@example.com",
                "email": "user@example.com",
                "email_verified": True,
                "name": "田中 太郎",
                "given_name": "太郎",
                "family_name": "田中",
                "preferred_username": "tanaka",
                "picture": None,
                "locale": "ja-JP",
                "session_index": "s2session1234567890",
                "attributes": {
                    "department": "Engineering",
                    "employee_id": "EMP001"
                }
            }
        }


class SAMLLinkResponse(BaseModel):
    """
    SAML ユーザー連携レスポンス

    OIDCのSSOLinkResponseと同等
    """

    message: str = Field(..., description="処理結果メッセージ")
    user_id: int = Field(..., description="連携されたユーザーID")
    saml_subject_id: str = Field(..., description="SAML NameID")
    is_new_user: bool = Field(..., description="新規ユーザー作成フラグ")
    linked_at: datetime = Field(..., description="連携日時")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "SAML authentication successful",
                "user_id": 123,
                "saml_subject_id": "user@example.com",
                "is_new_user": False,
                "linked_at": "2024-11-01T12:00:00Z"
            }
        }


class SAMLUserInfoResponse(BaseModel):
    """
    SAML ユーザー情報取得レスポンス

    認証済みユーザーのSAML関連情報を返す
    """

    user_info: SAMLUserInfo = Field(..., description="SAMLユーザー情報")
    saml_provider: str = Field(..., description="SAMLプロバイダー名")
    linked_at: datetime = Field(..., description="SAML連携日時")
    last_login: Optional[datetime] = Field(None, description="最終SAML ログイン日時")

    class Config:
        json_schema_extra = {
            "example": {
                "user_info": {
                    "subject_id": "user@example.com",
                    "email": "user@example.com",
                    "email_verified": True,
                    "name": "田中 太郎",
                    "given_name": "太郎",
                    "family_name": "田中"
                },
                "saml_provider": "saml",
                "linked_at": "2024-10-01T10:00:00Z",
                "last_login": "2024-11-01T12:00:00Z"
            }
        }


class SAMLHealthCheckResponse(BaseModel):
    """
    SAML ヘルスチェックレスポンス

    SAML設定とIdP接続性の確認結果
    """

    status: str = Field(..., description="SAML サービス状態")
    saml_configured: bool = Field(..., description="SAML設定完了フラグ")
    idp_metadata_accessible: bool = Field(..., description="IdPメタデータアクセス可能フラグ")
    required_settings_valid: bool = Field(..., description="必須設定有効フラグ")
    message: str = Field(..., description="詳細メッセージ")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "saml_configured": True,
                "idp_metadata_accessible": True,
                "required_settings_valid": True,
                "message": "SAML service is properly configured and IdP is accessible"
            }
        }


class SAMLMetadataResponse(BaseModel):
    """
    SAML SP メタデータレスポンス

    Service Provider メタデータXMLの返却用
    """

    metadata_xml: str = Field(..., description="SAML SP メタデータXML")
    entity_id: str = Field(..., description="SP エンティティID")
    generated_at: datetime = Field(..., description="メタデータ生成日時")

    class Config:
        json_schema_extra = {
            "example": {
                "metadata_xml": "<?xml version=\"1.0\"?><md:EntityDescriptor xmlns:md=\"urn:oasis:names:tc:SAML:2.0:metadata\"...",
                "entity_id": "https://app.example.com/saml/metadata",
                "generated_at": "2024-11-01T12:00:00Z"
            }
        }
