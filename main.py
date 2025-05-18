"""
KOIKI-FW アプリケーションのエントリーポイント。
このファイルは Docker コンテナ内で使用されるメインエントリーポイントです。
"""
import uvicorn
from app.main import app

from libkoiki.core.rate_limiter import limiter

# アプリケーション作成後にレートリミッターを登録
limiter.app = app
app.state.limiter = limiter

if __name__ == "__main__":
    # Python 3.11.7 互換の構成でアプリケーションを実行
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
