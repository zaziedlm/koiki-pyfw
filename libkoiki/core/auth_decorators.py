# src/core/auth_decorators.py
import functools
from typing import Callable, Any
from fastapi import HTTPException, status
import structlog

from libkoiki.core.exceptions import AuthenticationException, ValidationException

logger = structlog.get_logger(__name__)

def handle_auth_errors(endpoint_name: str = ""):
    """
    認証系エンドポイント用の共通エラーハンドリングデコレータ
    
    Args:
        endpoint_name: エンドポイント名（ログ用）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
                
            except ValidationException as e:
                logger.warning(
                    f"{endpoint_name} failed - validation error", 
                    error=str(e),
                    endpoint=endpoint_name
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
                
            except AuthenticationException as e:
                logger.warning(
                    f"{endpoint_name} failed - authentication error", 
                    error=str(e),
                    endpoint=endpoint_name
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            except HTTPException:
                # HTTPExceptionはそのまま再発生
                raise
                
            except Exception as e:
                logger.error(
                    f"{endpoint_name} failed - unexpected error", 
                    error=str(e),
                    endpoint=endpoint_name,
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{endpoint_name} failed" if endpoint_name else "Operation failed"
                )
                
        return wrapper
    return decorator

def log_auth_event(event_type: str, **kwargs):
    """
    認証イベントのログ記録ヘルパー
    
    Args:
        event_type: イベントタイプ
        **kwargs: ログに含める追加情報
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs_inner) -> Any:
            # 関数実行前ログ
            logger.info(f"{event_type} attempt", **kwargs)
            
            try:
                result = await func(*args, **kwargs_inner)
                
                # 成功ログ
                logger.info(f"{event_type} successful", **kwargs)
                return result
                
            except Exception as e:
                # 失敗ログ
                logger.warning(f"{event_type} failed", error=str(e), **kwargs)
                raise
                
        return wrapper
    return decorator