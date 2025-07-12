# src/api/v1/endpoints/security_monitor.py
"""
セキュリティ監視用のエンドポイント
管理者がセキュリティメトリクスやログを確認するためのAPI
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from libkoiki.api.dependencies import ActiveUserDep, has_permission
from libkoiki.core.security_metrics import security_metrics
from libkoiki.models.user import UserModel

router = APIRouter()


@router.get("/metrics", response_model=Dict[str, Any], dependencies=[has_permission("read:security_metrics")])
async def get_security_metrics() -> Dict[str, Any]:
    """
    セキュリティメトリクス全体を取得
    
    管理者権限が必要
    """
    return security_metrics.get_metrics()


@router.get("/metrics/authentication", response_model=Dict[str, Any], dependencies=[has_permission("read:security_metrics")])
async def get_authentication_stats() -> Dict[str, Any]:
    """
    認証統計情報を取得
    
    管理者権限が必要
    """
    return security_metrics.get_authentication_stats()


@router.get("/metrics/summary", response_model=Dict[str, Any], dependencies=[has_permission("read:security_metrics")])
async def get_security_summary() -> Dict[str, Any]:
    """
    セキュリティサマリーを取得
    
    管理者権限が必要
    """
    return security_metrics.get_security_summary()


@router.post("/metrics/reset", dependencies=[has_permission("manage:security_metrics")])
async def reset_security_metrics() -> Dict[str, str]:
    """
    セキュリティメトリクスをリセット
    
    管理者権限が必要
    """
    security_metrics.reset_metrics()
    return {"message": "Security metrics reset successfully"}


@router.get("/health")
async def security_health_check() -> Dict[str, Any]:
    """
    セキュリティシステムのヘルスチェック
    
    認証不要（システム監視用）
    """
    summary = security_metrics.get_security_summary()
    
    # 基本的なヘルスチェック条件
    health_status = "healthy"
    issues = []
    
    # 高い失敗率をチェック
    auth_stats = security_metrics.get_authentication_stats()
    if auth_stats.get("failure_rate", 0) > 50:  # 50%以上の失敗率
        health_status = "warning"
        issues.append("High authentication failure rate")
    
    # 大量のロックアウトをチェック
    if summary.get("lockouts", 0) > 100:  # 100回以上のロックアウト
        health_status = "warning"
        issues.append("High number of account lockouts")
    
    # 疑わしい活動をチェック
    if summary.get("suspicious_activities", 0) > 50:
        health_status = "warning"
        issues.append("High suspicious activity count")
    
    return {
        "status": health_status,
        "timestamp": summary.get("last_updated"),
        "issues": issues,
        "metrics_summary": summary,
    }