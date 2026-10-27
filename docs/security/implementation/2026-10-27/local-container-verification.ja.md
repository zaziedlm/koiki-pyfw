# ローカルPCでのコンテナ起動・ブラウザ操作確認と、未対応の気づき

記録日: 2026-10-27
対象ブランチ: `security/backend-python-emsign-brotli`（確認時点のHEAD `0b4e99d`）
環境: Windows 11 / Docker 29.1.3（Rancher Desktop）/ uv 0.11.7。組織のTLS検査プロキシ配下

Python・OSS依存の脆弱性対応（[README.ja.md](README.ja.md)）の後、更新済みの依存でコンテナをビルドし、ローカルPC上でブラウザ操作による機能確認まで行った実績と、その際に気づいたが**今回は対応しなかった点**を残す。ここに挙げた気づきは未対応であり、解消済みを意味しない。

## 1. 確認できたこと

| 確認項目 | 結果 |
| --- | --- |
| ホスト `.venv` の `pip-audit` | 更新前の`.venv`のままだと11パッケージ55件。`uv sync --locked --group security --native-tls` で`uv.lock`に合わせた後は、アプリ依存0件。残ったのは`.venv`だけにある setuptools 80.9.0 の3件（`uv.lock`に無い。`--exact`での除去は未実施） |
| `unified-dev`（ビルド・起動） | 成功。app/frontend/db/keycloak が healthy。既存DBは Alembic `20260715001`、roles 4・permissions 7・business clock 1・users 6 で、再作成・初期データ投入は不要だった |
| `unified-dev` ブラウザ操作 | ログイン、タスク一覧、作成、状態更新が成功 |
| `unified-optimized` ブラウザ操作 | ログイン、一覧、作成、更新、ログアウトが成功。アプリログに例外・スタックトレースなし。JWT・bcryptハッシュ・Authorizationヘッダー・Cookie値は出ていない。ログに出るリフレッシュトークンはSHA-256ハッシュ（`token_hash`）で生値ではない |
| `unified-prod`（再ビルド後の起動） | app/frontend/db/keycloak が healthy。`/health` は200（version 0.8.1）。**ブラウザでの再表示確認はこの記録では未確認** |

TLS検査プロキシ配下では `uv run --native-tls`（または `UV_NATIVE_TLS=1`）が必要だった。証明書検証の無効化は行っていない。

## 2. 起動時に詰まった点と、その原因・対処

| 事象 | 原因 | 対処 |
| --- | --- | --- |
| `uv run` が `UnknownIssuer` で失敗 | 組織のTLS検査プロキシのCAを、`uv`が既定では信頼しない | `--native-tls` |
| `pip-audit` が旧版を検出し続けた | `pip-audit`が検査するのは`uv.lock`ではなく導入済み`.venv`。ホスト`.venv`は意図的に更新しておらず、更新後の実測は隔離コンテナで行っていた（README.ja.md） | `uv sync --locked --group security` で同期 |
| `up`が「container name already in use」で失敗 | 過去のプロジェクト名`koiki_v07`で作られた同名の停止中コンテナが残っていた（現在の構成は`koiki_v07_unified`） | 古いコンテナを削除して`unified-dev`を再実行（データは名前付きボリュームに残る） |
| `unified-prod`でバックエンドが再起動を繰り返した（`Can't locate revision identified by '20260715001'`） | `unified-prod`は`up -d`のみで再ビルドしない。3か月前のprodイメージ（vNext前）が使われた | `unified-prod-build`で再ビルド後に`unified-prod` |
| `unified-prod`でフロントが白紙 | ビルド済みSPAのAPI接続先が`VITE_API_BASE_URL=/api/v1`（相対）。nginxに`/api`のプロキシが無く、`/api/v1/*`が`index.html`（200）で返りJSONとして解釈できない。相対パスはALB等の同一オリジン構成の前提設定で、`frontend/.env.production`はテンプレートと同一 | `FRONTEND_BUILD_ENV_FILE=.env.docker`（`http://localhost:8000/api/v1`）でfrontendだけビルドし直した |

## 3. 未対応の気づき（失念しないための記録）

優先度は、本番相当の起動前に必要か、機能・監査の欠落か、運用上の整理かで付けた目安。

| ID | 優先度 | 内容 | 根拠・場所 | 想定する対応 |
| --- | --- | --- | --- | --- |
| FU-1 | 高 | `DEBUG=True`のままだとSQLが全件ログに出る（二重出力）。SQLパラメーターにメール・IP・トークンハッシュが含まれる。prodビルドでも同じ | `components/libkoiki/src/libkoiki/db/session.py:57` が`echo=settings.DEBUG`。`DB_ECHO`（`config.py:42`）はどこからも参照されていない。ローカルの`.env.production`は`DEBUG=True`・`APP_ENV=development`で、テンプレートの`AUTH_COOKIE_SECURE`・`AUTH_CSRF_SECRET`・`APP_PORT`も無い | `echo`を`DB_ECHO`に切り替える。`.env.production`は`DEBUG=False`へ。`APP_ENV=production`にすると、httpのlocalhostではSecure Cookieが送られずログインできない可能性と、`ops/scripts/setup_security.py`が拒否される影響があるため、段階的に確認する |
| FU-2 | 中 | セキュリティイベントとログイン試行の`user_agent`に、`{"user_agent": "...", "ip_address": "..."}`というJSON文字列全体が入る | `components/libkoiki/src/libkoiki/api/v1/endpoints/auth_basic.py` ほかが`user_agent=device_info`と、デバイス情報の辞書をそのまま渡している | User-Agent文字列だけを渡す。`login_security_service.py`の受け側と`koiki_login_attempts`の保存内容も確認する |
| FU-3 | 中 | ログアウトの監査記録に`actor`が無く、セキュリティイベントも出ない（ログインは`authentication_succeeded_after_risk_check`が出る） | `POST /api/v1/auth/session/logout`の監査行が`actor.user_id`・`actor.email`ともNone。イベント種別はログインの1種類のみ | ログアウトのイベントを追加し、actorを監査行に載せる |
| FU-4 | 低 | ログイン後の最初の書き込みが403になり、CSRFを取り直して再送して成功する。セッションごとに失敗の監査記録が1件残る | 2回観測（dev: `POST /todos`、optimized: `PUT /todos/4`）。ログイン前に取得したCSRFトークンがログイン後に無効になる | ログイン成功後にフロントがCSRFトークンを取り直す。フロントとバックエンドのどちらの責務かを`docs/agent/auth-security.md`のCookie/CSRF契約で確認する |
| FU-5 | 低 | ログのタイムスタンプが2種類。アプリログはJST（`+09:00`）、SQLAlchemyログはUTC | `2026-10-27T15:54:24+09:00`と`2026-10-27 06:54:24,886` | ログ設定でタイムゾーンを揃える（SQL出力自体を止めるFU-1で目立たなくなる） |
| FU-6 | 低 | ログにメールアドレスとIPが平文で出る（セキュリティイベント・ログイン監査） | 上記ログ | `docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md`の方針と照合して、許容か、マスクかを決める |
| FU-7 | 中 | `start-docker.ps1`の`unified-prod`／`unified-optimized`は再ビルドしないため、古いイメージで起動して失敗する。`unified-prod`系は、フロントのビルド環境を`.env.production`に固定するため、ローカルでは白紙になる | `start-docker.ps1`の`Ensure-ProductionEnv`と`up -d` | スクリプトに「ビルド有無の確認」と、ローカル用のフロント環境ファイル選択を足す。または`frontend/.env.production`のローカル確認用の値を手順書に明記する |
| FU-8 | 低 | `optimized`のバックエンドは`builder`ステージのままで、dev・testの依存を含む（`INSTALL_MAIN_ONLY`が既定のfalse）。名前から想像するより軽量ではない | `Dockerfile.unified`の`optimized`ステージ | 位置づけを手順書に明記する。必要なら実行依存のみに絞る |
| FU-9 | 低 | `DOCKER_SETUP.md`のトラブルシューティングに、現在のVite SPAと合わない記述が残る | `DOCKER_SETUP.md`122行目の「`_next/static`が取れない: Next.js…」 | Vite SPAの現状に合わせて書き直す |
| FU-10 | 低 | プロジェクト名の変更（`koiki_v07`→`koiki_v07_unified`）で、旧プロジェクトの停止済みコンテナ・ボリュームが残り、`up`が衝突する。composeが「別プロジェクトで作成されたボリューム」と警告する | `docker-compose.unified.yml`の`name: koiki_v07_unified`と固定の`container_name` | 旧コンテナの整理手順を手順書に載せる。ボリュームを`external: true`にするか検討する |
| FU-11 | 低 | ホスト`.venv`にsetuptools 80.9.0（`uv.lock`に無い）が残り、`pip-audit`が3件を報告する | `uv sync --locked --group security --exact`で除去できるが、手で入れた他のパッケージも消える | 実施するか、検出を既知の残りとして扱うか決める |

## 4. 今回の確認に含めていないこと

- Keycloak経由のSSO・SAMLのブラウザ操作、管理された実IdPとの接続（README.ja.mdの`VERIFY-IDP`）
- GitHub Actions、arm64、実配備CPUでの実行（`VERIFY-CPU-CI`）
- `unified-prod`でのブラウザ再表示と、`unified-prod-external`の起動
- PRの発行、`main`へのマージ（依頼者の指示により行わない）
