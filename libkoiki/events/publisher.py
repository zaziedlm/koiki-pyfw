# src/events/publisher.py
import json
from typing import Dict, Any, Optional
import structlog

# 条件付きインポート
try:
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Dummy Redis class for compatibility
    class Redis:
        """Redis client stub when redis package is not available"""
        async def publish(self, *args, **kwargs):
            return 0
        
        async def ping(self):
            return True
        
        async def close(self):
            pass

logger = structlog.get_logger(__name__)

class EventPublisher:
    """Redis Pub/Sub を使用してイベントを発行するクラス"""
    def __init__(self, redis_client: Optional[object]):
        if redis_client is None:
             logger.warning("Redis client is not provided to EventPublisher. Publishing will be disabled.")
        self.redis = redis_client

    async def publish(self, channel: str, data: Dict[str, Any]):
        """指定されたチャンネルにイベントデータ (JSON) を発行する"""
        if not self.redis:
             logger.warning("Cannot publish event: Redis client is not available.", channel=channel)
             return False # 発行失敗

        try:
            message = json.dumps(data)
            # publish は成功したクライアント数を返す
            num_clients = await self.redis.publish(channel, message)
            logger.info("Event published", channel=channel, data=data, received_by_clients=num_clients)
            return num_clients > 0 # 1つ以上のクライアントが受け取れば成功とする
        except TypeError as e:
            logger.error("Failed to serialize event data to JSON", channel=channel, data=data, exc_info=True)
            return False
        except ConnectionError:
             logger.error("Failed to publish event: Redis connection error.", channel=channel, exc_info=False)
             return False
        except Exception as e:
            logger.error("Failed to publish event", channel=channel, data=data, exc_info=True)
            return False

# 使用例 (サービス層などから)
# publisher = EventPublisher(redis_client)
# await publisher.publish("user_created", {"user_id": 1, "email": "test@example.com"})