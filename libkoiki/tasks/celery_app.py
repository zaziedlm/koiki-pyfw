# src/tasks/celery_app.py
from celery import Celery
import structlog
import os

# structlog をインポートしてロガーを取得
logger = structlog.get_logger(__name__)

# --- Celery アプリケーションインスタンス ---
# アプリケーション名 ('worker' など)
# include にタスクが定義されているモジュールのリストを指定
# broker と backend は設定から読み込む

celery_app: Optional[Celery] = None

def create_celery_app() -> Optional[Celery]:
    """Celeryアプリケーションインスタンスを作成・設定します"""
    global celery_app
    # 環境変数を読み込む (config.py を直接インポートしない方が良い場合もある)
    # 代わりに os.getenv を使うか、Celery設定ファイルを使う
    # from libkoiki.core.config import settings # タスク内での循環参照を避ける

    broker_url = os.getenv("CELERY_BROKER_URL")
    backend_url = os.getenv("CELERY_RESULT_BACKEND")
    app_name = os.getenv("APP_NAME", "koiki_worker")

    if not broker_url:
        logger.warning("CELERY_BROKER_URL not set. Celery tasks cannot be executed.")
        return None
    if not backend_url:
        logger.warning("CELERY_RESULT_BACKEND not set. Task results might not be stored.")
        # バックエンドなしでも動作は可能

    logger.info("Initializing Celery app", app_name=app_name, broker=broker_url, backend=backend_url)

    # Celery インスタンスを作成
    celery_app = Celery(
        app_name,
        broker=broker_url,
        backend=backend_url,
        include=[
            "src.tasks.email", # ウェルカムメールタスク
            # 他のタスクモジュールも追加
            # "src.tasks.reports",
        ]
    )

    # Celery 設定 (celeryconfig.py を使うか、ここで直接設定)
    celery_app.conf.update(
        # --- 基本設定 ---
        task_serializer="json",         # タスクのシリアライザ
        result_serializer="json",       # 結果のシリアライザ
        accept_content=["json"],        # 受け入れるコンテントタイプ
        timezone=os.getenv("TZ", "UTC"), # タイムゾーン (コンテナのTZ環境変数も参照)
        enable_utc=True,                # UTCを有効にする

        # --- スケジューリング (Celery Beat を使う場合) ---
        # beat_schedule = {
        #     'send-summary-every-hour': {
        #         'task': 'src.tasks.summary.send_hourly_summary',
        #         'schedule': crontab(minute=0, hour='*/1'), # 毎時0分に実行
        #     },
        # },

        # --- ルーティング (キューを分ける場合) ---
        task_routes={
            "src.tasks.email.*": {"queue": "email"}, # email関連タスクは email キューへ
            # "src.tasks.reports.*": {"queue": "reports"}, # report関連タスクは reports キューへ
            # デフォルトキュー (指定がない場合)
            # "default": {"queue": "default"}, # 明示的に定義も可能
        },
        # ワーカーが複数のキューを購読する場合: celery worker -Q email,reports,default

        # --- 信頼性・パフォーマンス設定 ---
        worker_prefetch_multiplier=1,   # 1度に1タスクずつ取得 (信頼性重視の場合)
        task_acks_late=True,            # タスク実行完了後にACK (失敗時に再実行されやすい)
        # task_reject_on_worker_lost=True, # ワーカー消失時にタスクを再キューイング (Brokerによる)
        # broker_connection_retry_on_startup=True, # 起動時のブローカー接続リトライ

        # --- 結果バックエンド設定 ---
        result_expires=timedelta(days=1), # 結果の有効期限 (1日)

        # --- ロギング設定 ---
        # Celery自身のロギング設定 (structlog と統合することも可能だが複雑)
        # logging='INFO', # Celeryワーカーのログレベル
    )

    # Celery シグナルを使った structlog の設定統合 (高度な設定)
    # setup_celery_logging()

    logger.info("Celery app configured successfully.")
    return celery_app

# --- (高度な設定) Celeryシグナルでstructlogを統合 ---
from celery.signals import setup_logging as setup_celery_logging_signal, after_setup_logger, after_setup_task_logger
from celery.app.log import TaskFormatter
import logging
from datetime import timedelta # timedelta をインポート
from typing import Optional # Optional をインポート

# @setup_celery_logging_signal.connect
# def setup_celery_logging(**kwargs):
#     """Celeryの標準ロギング設定を無効化 (structlogで管理するため)"""
#     # logging.getLogger('celery').handlers = []
#     # logging.getLogger('celery.app').handlers = []
#     # logging.getLogger('celery.task').handlers = []
#     pass # 何もしないことで標準設定を抑制

# def configure_structlog_celery(logger_instance, loglevel, format_string):
#     """structlog を Celery のロガーに適用するヘルパー"""
#     from libkoiki.core.logging import setup_logging as setup_app_logging # アプリのロギング設定を流用
#     # setup_app_logging() # 既に設定されているはずだが念のため
#     handler = logging.root.handlers[0] # アプリのハンドラを取得
#     logger_instance.addHandler(handler)
#     logger_instance.setLevel(loglevel)

# @after_setup_logger.connect
# def setup_celery_root_logger(logger, loglevel, logfile, format, colorize, **kwargs):
#     """Celery のルートロガーを structlog で設定"""
#     # logger.handlers = [] # 標準ハンドラを削除
#     configure_structlog_celery(logger, loglevel, format)

# @after_setup_task_logger.connect
# def setup_celery_task_logger(logger, loglevel, logfile, format, colorize, **kwargs):
#     """Celery のタスフロガーを structlog で設定"""
#     # logger.handlers = [] # 標準ハンドラを削除
#     configure_structlog_celery(logger, loglevel, format)


# --- アプリケーション起動時に Celery App を作成 ---
# create_celery_app() # main.py などで Celery を使う場合に呼び出すか、
# worker起動時に自動的に評価される

# このファイルが直接実行された場合 (例: `celery -A src.tasks.celery_app worker ...`)
if __name__ == "__main__":
    celery_app = create_celery_app()
    if celery_app is None:
         sys.exit("Failed to create Celery app instance. Check configuration.")

# モジュールレベルでのインスタンス作成試行
celery_app = create_celery_app()

# Celery Beat スケジュール用
# from celery.schedules import crontab
import sys # sys をインポート
