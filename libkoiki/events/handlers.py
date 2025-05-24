# src/events/handlers.py
import asyncio
import json
from typing import Callable, Dict, Any, Optional
import structlog

# 条件付きインポート
try:
    from redis.asyncio import Redis, PubSub
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Redis stub
    class Redis:
        """Redis client stub when redis package is not available"""
        def pubsub(self, **kwargs):
            return PubSub()
            
        async def ping(self):
            return True
        
    # PubSub stub
    class PubSub:
        """PubSub stub when redis package is not available"""
        async def subscribe(self, *args):
            pass
            
        async def get_message(self, **kwargs):
            return None
            
        async def unsubscribe(self):
            pass
            
        async def close(self):
            pass

logger = structlog.get_logger(__name__)

class EventHandler:
    """Redis Pub/Sub を使用してイベントを購読し、ハンドラーを実行するクラス"""
    def __init__(self, redis_client: object):
        self.redis = redis_client
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.pubsub: Optional[PubSub] = None
        self._stop_event = asyncio.Event()

    def register(self, channel: str, handler: Callable[[Dict[str, Any]], Any]):
        """指定されたチャンネルにイベントハンドラーを登録する"""
        self.handlers[channel] = handler
        logger.info("Event handler registered", channel=channel, handler=handler.__name__)

    async def _listen(self):
        """内部リスニングループ"""
        if not self.redis:
            logger.error("Redis client not available for event listening.")
            return

        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        try:
            if not self.handlers:
                 logger.warning("No event handlers registered, stopping listener.")
                 return

            await self.pubsub.subscribe(*self.handlers.keys())
            logger.info("Subscribed to event channels", channels=list(self.handlers.keys()))

            while not self._stop_event.is_set():
                try:
                    # timeoutを設定してstop_eventを定期的にチェック
                    message = await asyncio.wait_for(self.pubsub.get_message(timeout=1.0), timeout=1.1)
                    if message:
                        channel = message['channel']
                        data_str = message['data']
                        logger.debug("Received message", channel=channel, data_str=data_str)

                        if channel in self.handlers:
                            try:
                                data_dict = json.loads(data_str)
                                handler = self.handlers[channel]
                                # ハンドラーを非同期に実行 (エラーハンドリングを含む)
                                asyncio.create_task(self._run_handler(handler, data_dict, channel))
                            except json.JSONDecodeError:
                                logger.error("Failed to decode JSON message", channel=channel, data=data_str)
                            except Exception as e:
                                # ハンドラー呼び出し前のエラー
                                logger.error(f"Error processing message for channel {channel}", exc_info=True)
                        else:
                             logger.warning("Received message for unregistered channel", channel=channel)

                except asyncio.TimeoutError:
                    # タイムアウトは正常、ループを継続して停止フラグを確認
                    continue
                except ConnectionError:
                     logger.error("Redis connection lost during listening. Attempting to reconnect...", exc_info=False)
                     await asyncio.sleep(5) # 再接続試行前に待機
                     # 再購読処理が必要になる場合がある
                     await self.pubsub.subscribe(*self.handlers.keys())
                except Exception as e:
                    logger.error("Error in event listener loop", exc_info=True)
                    # ループ継続のために少し待つ
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error("Exception in _listen setup or main loop", exc_info=True)
        finally:
            if self.pubsub:
                try:
                    await self.pubsub.unsubscribe()
                    await self.pubsub.close()
                    logger.info("Unsubscribed from channels and closed pubsub.")
                except Exception as e:
                    logger.error("Error closing pubsub", exc_info=True)
            self.pubsub = None # クリーンアップ

    async def _run_handler(self, handler: Callable, data: Dict[str, Any], channel: str):
        """ハンドラー関数を安全に実行する"""
        try:
            logger.info("Running event handler", handler=handler.__name__, channel=channel, data=data)
            await handler(data) # ハンドラーは async def である想定
            logger.debug("Event handler finished successfully", handler=handler.__name__, channel=channel)
        except Exception as e:
            logger.error(
                f"Exception in event handler '{handler.__name__}' for channel '{channel}'",
                exc_info=True,
                handler_data=data # エラー発生時のデータもログに残す
            )
            # ここでエラー通知やリトライ処理などを追加可能

    async def start_listening(self):
        """イベントリスニングを開始する"""
        if self.pubsub:
            logger.warning("Listener already running or starting.")
            return
        logger.info("Starting event listener...")
        self._stop_event.clear()
        # バックグラウンドタスクとしてリスニングループを実行
        asyncio.create_task(self._listen())

    async def stop_listening(self):
        """イベントリスニングを停止する"""
        if not self.pubsub:
            logger.warning("Listener is not running.")
            return
        logger.info("Stopping event listener...")
        self._stop_event.set()
        # _listen ループが終了するのを待つ (タイムアウト付き推奨)
        # try:
        #     # asyncio.wait_for(self._listen_task, timeout=5.0) # _listenタスクを保持しておく必要あり
        #     pass
        # except asyncio.TimeoutError:
        #     logger.warning("Timeout waiting for listener to stop.")
        # ループが self.pubsub をクローズするのを待つ
        while self.pubsub is not None:
             await asyncio.sleep(0.1)
        logger.info("Event listener stopped.")


# --- サンプルイベントハンドラー ---
async def user_created_handler(data: Dict[str, Any]):
    """'user_created' イベントを処理するハンドラー"""
    user_id = data.get("user_id")
    email = data.get("email")
    logger.info(f"Handling 'user_created' event", user_id=user_id, email=email)
    # ここでメール送信タスクをキューに入れる、統計データを更新するなどの非同期処理を行う
    try:
        from libkoiki.tasks.email import send_welcome_email_task # Celeryタスクを呼び出す例
        # Celeryが設定されているか確認
        if send_welcome_email_task:
            send_welcome_email_task.delay(user_id, email)
            logger.info("Scheduled welcome email task", user_id=user_id, email=email)
        else:
            logger.warning("Celery not configured, skipping welcome email task.", user_id=user_id)
    except ImportError:
         logger.warning("Celery tasks module not found, skipping welcome email task.", user_id=user_id)
    except Exception as e:
         logger.error("Failed to schedule welcome email task", user_id=user_id, exc_info=True)

# 他のハンドラー例
# async def order_placed_handler(data: Dict[str, Any]): ...
# async def data_updated_handler(data: Dict[str, Any]): ...

