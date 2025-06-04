# src/utils/email.py
# メール送信関連のユーティリティ関数 (ダミー実装)
import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)

# --- ダミーのメール送信関数 ---
# 本番環境では、SMTPライブラリ (smtplib, aiosmtplib) や
# メール送信サービス (SendGrid, Mailgun など) のクライアントを使用します。

def send_email(
    to_email: str,
    subject: str,
    template_name: str, # 使用するHTMLテンプレート名など
    context: Dict[str, Any], # テンプレートに渡すコンテキスト変数
    # from_email: Optional[str] = settings.EMAILS_FROM_EMAIL # 送信元アドレス
):
    """
    メールを送信する（ダミー関数）。
    実際の送信ロジックをここに実装します。
    """
    # from_email = from_email or settings.EMAILS_FROM_EMAIL
    logger.info(
        "Sending email (dummy)",
        # from_email=from_email,
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=context,
    )

    # --- 実際のメール送信ロジック (例) ---
    # 1. HTMLテンプレートをレンダリング (Jinja2など)
    #    html_content = render_template(template_name, **context)

    # 2. SMTPサーバーに接続して送信 or メールサービスAPIを呼び出す
    #    try:
    #        # 例: smtplib を使用
    #        # server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    #        # server.starttls()
    #        # server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    #        # message = f"Subject: {subject}\nTo: {to_email}\nFrom: {from_email}\nContent-Type: text/html\n\n{html_content}"
    #        # server.sendmail(from_email, to_email, message.encode('utf-8'))
    #        # server.quit()
    #        pass # 成功
    #    except Exception as e:
    #        logger.error("Failed to send email", exc_info=True, to_email=to_email, subject=subject)
    #        raise ConnectionRefusedError(f"Failed to send email to {to_email}") # 例外を投げてタスクでリトライさせる

    # ダミー実装なので成功したとする
    logger.info("Email sent successfully (dummy)", to_email=to_email, subject=subject)
    return True
