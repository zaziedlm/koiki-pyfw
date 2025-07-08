# src/core/security_metrics.py
"""
セキュリティ関連のメトリクス収集・監視機能
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class SecurityMetrics:
    """セキュリティメトリクス収集クラス"""
    
    def __init__(self):
        # メモリ内でメトリクスを保持（本番環境ではRedisやPrometheusを使用）
        self._metrics: Dict[str, Any] = {
            "authentication_attempts": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "failed_by_email": {},
                "failed_by_ip": {},
            },
            "lockouts": {
                "total": 0,
                "by_email": 0,
                "by_ip": 0,
            },
            "suspicious_activities": {
                "total": 0,
                "by_type": {},
            },
            "rate_limits": {
                "total": 0,
                "by_endpoint": {},
            },
            "last_updated": None,
        }
    
    def record_authentication_attempt(
        self, 
        success: bool, 
        email: str, 
        ip_address: str,
        failure_reason: Optional[str] = None
    ) -> None:
        """認証試行のメトリクスを記録"""
        try:
            self._metrics["authentication_attempts"]["total"] += 1
            
            if success:
                self._metrics["authentication_attempts"]["success"] += 1
            else:
                self._metrics["authentication_attempts"]["failed"] += 1
                
                # メール別の失敗回数
                email_failures = self._metrics["authentication_attempts"]["failed_by_email"]
                email_failures[email] = email_failures.get(email, 0) + 1
                
                # IP別の失敗回数
                ip_failures = self._metrics["authentication_attempts"]["failed_by_ip"]
                ip_failures[ip_address] = ip_failures.get(ip_address, 0) + 1
            
            self._update_timestamp()
            
        except Exception as e:
            logger.error("Failed to record authentication metrics", error=str(e))
    
    def record_lockout(self, lockout_type: str, identifier: str) -> None:
        """ロックアウトのメトリクスを記録"""
        try:
            self._metrics["lockouts"]["total"] += 1
            
            if lockout_type == "email":
                self._metrics["lockouts"]["by_email"] += 1
            elif lockout_type == "ip":
                self._metrics["lockouts"]["by_ip"] += 1
            
            self._update_timestamp()
            
        except Exception as e:
            logger.error("Failed to record lockout metrics", error=str(e))
    
    def record_suspicious_activity(self, activity_type: str) -> None:
        """疑わしい活動のメトリクスを記録"""
        try:
            self._metrics["suspicious_activities"]["total"] += 1
            
            by_type = self._metrics["suspicious_activities"]["by_type"]
            by_type[activity_type] = by_type.get(activity_type, 0) + 1
            
            self._update_timestamp()
            
        except Exception as e:
            logger.error("Failed to record suspicious activity metrics", error=str(e))
    
    def record_rate_limit_exceeded(self, endpoint: str) -> None:
        """レート制限超過のメトリクスを記録"""
        try:
            self._metrics["rate_limits"]["total"] += 1
            
            by_endpoint = self._metrics["rate_limits"]["by_endpoint"]
            by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
            
            self._update_timestamp()
            
        except Exception as e:
            logger.error("Failed to record rate limit metrics", error=str(e))
    
    def get_metrics(self) -> Dict[str, Any]:
        """現在のメトリクスを取得"""
        return self._metrics.copy()
    
    def get_authentication_stats(self) -> Dict[str, Any]:
        """認証統計を取得"""
        auth_metrics = self._metrics["authentication_attempts"]
        total = auth_metrics["total"]
        
        if total == 0:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
            }
        
        success_rate = (auth_metrics["success"] / total) * 100
        failure_rate = (auth_metrics["failed"] / total) * 100
        
        return {
            "total_attempts": total,
            "successful_attempts": auth_metrics["success"],
            "failed_attempts": auth_metrics["failed"],
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "top_failed_emails": self._get_top_items(auth_metrics["failed_by_email"]),
            "top_failed_ips": self._get_top_items(auth_metrics["failed_by_ip"]),
        }
    
    def get_security_summary(self) -> Dict[str, Any]:
        """セキュリティサマリーを取得"""
        return {
            "authentication_attempts": self._metrics["authentication_attempts"]["total"],
            "failed_attempts": self._metrics["authentication_attempts"]["failed"],
            "lockouts": self._metrics["lockouts"]["total"],
            "suspicious_activities": self._metrics["suspicious_activities"]["total"],
            "rate_limit_violations": self._metrics["rate_limits"]["total"],
            "last_updated": self._metrics["last_updated"],
        }
    
    def reset_metrics(self) -> None:
        """メトリクスをリセット"""
        self.__init__()
        logger.info("Security metrics reset")
    
    def _update_timestamp(self) -> None:
        """更新タイムスタンプを設定"""
        self._metrics["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    def _get_top_items(self, data: Dict[str, int], limit: int = 5) -> list:
        """トップアイテムを取得"""
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        return [{"item": item, "count": count} for item, count in sorted_items[:limit]]


# グローバルインスタンス
security_metrics = SecurityMetrics()