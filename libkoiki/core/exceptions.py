# src/core/exceptions.py
from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class BaseAppException(HTTPException):
    """アプリケーション固有の例外の基底クラス"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or self.__class__.__name__.upper() # エラーコードがなければクラス名を大文字にする

# --- 4xx Client Errors ---

class BadRequestException(BaseAppException):
    """汎用的な 400 Bad Request エラー"""
    def __init__(self, detail: str = "Bad Request", error_code: str = "BAD_REQUEST", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, error_code, headers)

class ValidationException(BadRequestException):
    """バリデーションエラー (ビジネスルールなど) (400 Bad Request)"""
    def __init__(self, detail: str = "Validation Failed", error_code: str = "VALIDATION_ERROR", headers: Optional[Dict[str, Any]] = None):
        # status_code は BadRequestException から継承 (400)
        super().__init__(detail, error_code, headers)

class AuthenticationException(BaseAppException):
    """認証エラー (401 Unauthorized)"""
    def __init__(self, detail: str = "Authentication Failed", error_code: str = "AUTHENTICATION_ERROR", headers: Optional[Dict[str, Any]] = None):
        # WWW-Authenticate ヘッダーを追加するのが一般的
        auth_headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            auth_headers.update(headers)
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, error_code, auth_headers)

class AuthorizationException(BaseAppException):
    """認可エラー (権限不足) (403 Forbidden)"""
    def __init__(self, detail: str = "Permission Denied", error_code: str = "AUTHORIZATION_ERROR", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status.HTTP_403_FORBIDDEN, detail, error_code, headers)

class ResourceNotFoundException(BaseAppException):
    """リソースが見つからないエラー (404 Not Found)"""
    def __init__(self, resource_name: str = "Resource", resource_id: Optional[Any] = None, detail: Optional[str] = None, error_code: str = "RESOURCE_NOT_FOUND", headers: Optional[Dict[str, Any]] = None):
        if detail is None:
            detail = f"{resource_name} not found."
            if resource_id is not None:
                detail = f"{resource_name} with ID '{resource_id}' not found."
        super().__init__(status.HTTP_404_NOT_FOUND, detail, error_code, headers)

class ConflictException(BaseAppException):
    """リソースの競合エラー (例: 既に存在する) (409 Conflict)"""
    def __init__(self, detail: str = "Resource conflict", error_code: str = "CONFLICT_ERROR", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status.HTTP_409_CONFLICT, detail, error_code, headers)

# --- 5xx Server Errors ---

class ServiceUnavailableException(BaseAppException):
    """外部サービス利用不可などのエラー (503 Service Unavailable)"""
    def __init__(self, detail: str = "Service temporarily unavailable", error_code: str = "SERVICE_UNAVAILABLE", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, detail, error_code, headers)

class ExternalServiceException(ServiceUnavailableException):
    """外部サービスとの通信エラー"""
    def __init__(self, service_name: str, detail: Optional[str] = None, error_code: str = "EXTERNAL_SERVICE_ERROR", headers: Optional[Dict[str, Any]] = None):
        if detail is None:
            detail = f"Error communicating with external service: {service_name}"
        super().__init__(detail, error_code, headers)

# 使用例:
# raise ResourceNotFoundException(resource_name="User", resource_id=user_id)
# raise ValidationException("Email address is already in use.")
# raise AuthorizationException("You do not have permission to perform this action.")
# raise AuthenticationException()