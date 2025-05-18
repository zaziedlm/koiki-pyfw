# src/tasks/email.py
from libkoiki.tasks.celery_app import celery_app # 設定済みの Celery インスタンス
import structlog
import time # ダミー処理用

# from libkoiki.utils.email import send_email # 実際のメール送信関数 (utilsに実装想定)
# from libkoiki.core.config import settings # 設定が必要な場合

logger = structlog.get_logger(__name__)

# celery_app が None (設定不備) の場合はタスクを登録しない
if celery_app:
    @celery_app.task(
        name="send_welcome_email", # タスク名 (省略すると自動生成)
        acks_late=True,           # 完了後にACK (デフォルト設定を継承)
        bind=True,                # taskインスタンス自身を引数として受け取る (リトライ等で使用)
        max_retries=3,            # 最大リトライ回数
        default_retry_delay=60    # リトライ間隔 (秒)
    )
    def send_welcome_email_task(self, user_id: int, email: str):
        """
        ウェルカムメールを送信するCeleryタスク。

        Args:
            self: Celery Task インスタンス (bind=True のため)
            user_id: ユーザーID
            email: 送信先メールアドレス
        """
        logger.info("Starting welcome email task", task_id=self.request.id, user_id=user_id, email=email)
        try:
            # --- 実際のメール送信処理 ---
            # この部分は `src/utils/email.py` などに実装し、それを呼び出す
            logger.debug("Simulating email sending...", duration=5)
            # send_email(
            #     to_email=email,
            #     subject="Welcome to KOIKI App!",
            #     template_name="welcome_email.html", # メールテンプレート名
            #     context={"user_id": user_id, "user_email": email} # テンプレートに渡す変数
            # )
            time.sleep(5) # ダミーの重い処理

            logger.info("Welcome email task completed successfully", task_id=self.request.id, user_id=user_id)
            return {"status": "success", "user_id": user_id, "email": email}

        except ConnectionRefusedError as exc: # 例: SMTPサーバー接続拒否
             logger.warning("Connection refused during email sending, retrying...", task_id=self.request.id, user_id=user_id, attempt=self.request.retries + 1, max_retries=self.max_retries)
             # リトライ処理 (countdown で待機時間を指定)
             raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) # 指数バックオフ

        except Exception as e:
            # その他の予期せぬエラー
            logger.error(f"Failed to send welcome email for user {user_id}", task_id=self.request.id, exc_info=True)
            # リトライ可能ならリトライ、そうでなければエラーとする
            # self.retry(exc=e) # 例外を指定してリトライ
            raise # リトライしない場合は例外を再送出し、タスクを失敗させる

else:
    # Celeryが無効な場合のダミー関数や警告
    def send_welcome_email_task(*args, **kwargs):
        logger.warning("Celery is not configured. Skipping send_welcome_email_task.")
        return None # または適切な値を返す

# 他のメール関連タスクもここに追加
# @celery_app.task(name="send_password_reset_email")
# def send_password_reset_email_task(user_id: int, email: str, reset_token: str): ...
