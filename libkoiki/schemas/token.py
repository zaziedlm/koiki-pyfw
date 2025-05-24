# src/schemas/token.py
from pydantic import BaseModel, Field # Field をインポート
from typing import Optional

class Token(BaseModel):
    """アクセストークンとトークンタイプ"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")

class TokenPayload(BaseModel):
    """JWTトークンのペイロード (内容)"""
    sub: Optional[str] = Field(None, description="Subject of the token (usually user ID)")
    exp: Optional[int] = Field(None, description="Expiration time (Unix timestamp)")

    # 必要に応じて他のクレームを追加
    # iss: Optional[str] = None # Issuer
    # aud: Optional[str] = None # Audience
    # roles: Optional[list[str]] = None # ロール情報など (ペイロードに含める場合)