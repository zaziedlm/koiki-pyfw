# SAML認証機能 移植ガイド

KOIKI-FW（koiki-pyfw）に実装したSAML認証機能を、同様のプロジェクト構造（FastAPI + SQLAlchemy + Next.js）を持つ別プロジェクトへ移植する手順書。最新コミットでDBテーブルマッピングをプロジェクト非依存に整理済みであり、そのまま移植できるものと改修が必要なものを明確に分離し、リスク最小の手順で移植作業を進める。

---

## 前提条件（重要）

**`libkoiki/` は移植先でも共有フレームワークとして使用される。かつ、移植先もアプリケーションモジュール名は `app` を使用している。**

これにより、すべてのimportパスは移植元・移植先で完全に同一となる。
- `libkoiki.*` のimport → 変更不要
- `app.*` のimport → 変更不要（移植先も `app` モジュール名を使用）

**結論: バックエンドPythonファイルはすべてコピーのみ。変更が必要なのはAlembic `down_revision` と統合作業のみ。**

---

## 移植対象ファイル一覧と分類

### カテゴリA: そのままコピー移植可能（変更不要）

**バックエンド（全ファイルimportパス変更不要）:**

| ファイル | 備考 |
|---------|------|
| `app/core/saml_config.py` | `pydantic_settings`のみ |
| `app/schemas/saml.py` | `pydantic`のみ |
| `app/models/saml_auth_flow.py` | libkoiki Base のみ |
| `app/models/user_sso.py` | libkoiki Base + UserModel のみ |
| `app/services/saml_metadata_loader.py` | `httpx`, `structlog`のみ |
| `app/services/saml_certificate_manager.py` | `app.*` / `libkoiki.*` → 変更不要 |
| `app/services/saml_service.py` | `app.*` / `libkoiki.*` → 変更不要 |
| `app/repositories/saml_auth_flow_repository.py` | `app.*` / `libkoiki.*` → 変更不要 |
| `app/repositories/user_sso_repository.py` | `app.*` / `libkoiki.*` → 変更不要 |
| `app/api/v1/endpoints/saml_auth.py` | `app.*` / `libkoiki.*` → 変更不要 |
| `tests/unit/app/services/test_saml_service.py` | `app.*` → 変更不要 |

**フロントエンド・その他:**

| ファイル | 備考 |
|---------|------|
| `frontend/src/lib/saml-storage.ts` | ブラウザAPIのみ |
| `frontend/src/hooks/use-saml-login.ts` | `@/lib/config` の `saml?.redirectUri` 参照を移植先に合わせて確認 |
| `frontend/src/app/api/saml/authorization/route.ts` | `NEXT_PUBLIC_API_BASE_URL` 環境変数名を移植先に合わせて確認 |
| `.env.saml.example` | URLのみ移植先に合わせて変更 |
| `docs/saml/` 配下の全ドキュメント | 6ファイル（参照資料として移植） |
| `docker/keycloak/realm-saml.json` | 開発IdP設定（流用可能） |

### カテゴリB: Alembic `down_revision` の変更のみ

| ファイル | 変更箇所 |
|---------|---------|
| `alembic/versions/20250908001_add_user_sso_table.py` | `down_revision` を移植先の最新リビジョンIDに変更 |
| `alembic/versions/20251010001_add_app_columns_to_user_sso.py` | `down_revision` を変更（`20250908001` を指すよう維持） |
| `alembic/versions/20260228001_add_saml_auth_flow_table.py` | `down_revision` を変更（`20251010001` を指すよう維持） |

連鎖順序: `{移植先最新}` → `20250908001` → `20251010001` → `20260228001`

### カテゴリC: プロジェクト固有の統合作業（追記のみ）

| ファイル | 作業内容 |
|---------|---------|
| `app/api/v1/router.py` | 移植先の既存ルーターにSAMLルーターを登録する1〜5行の追記 |
| `app/main.py` | 移植先の `lifespan` 関数にクリーンアップタスク（`_periodic_saml_flow_cleanup`）の起動/停止を追記 |
| `app/models/user_sso.py` コピー後 | 移植先の `UserModel` に `sso_links` リレーションを追加（UserModelファイルへの追記） |
| `frontend/src/app/api/saml/login/route.ts` | `@/lib/cookie-utils`, `@/lib/csrf-utils` が移植先に存在しない場合のみ実装が必要 |
| `frontend/src/app/auth/saml/callback/page.tsx` | CSRF cookie名（`koiki_csrf_token`）、エラーリダイレクト先（`/auth/login`）、UIコンポーネント（`@/components/ui/button`）を移植先の値に変更 |

---

## 移植先で新規追加が必要なもの

### Pythonパッケージ

```toml
# pyproject.toml に追加
python3-saml = ">=1.16.0,<1.17.0"
xmlsec = ">=1.3.13,<1.4.0"
```

### Dockerfileへのシステムライブラリ追加（必須）

```dockerfile
RUN apt-get update && apt-get install -y \
    libxml2-dev libxmlsec1-dev libxmlsec1-openssl pkg-config
```

---

## 移植作業手順（リスク最小順）

### フェーズ0: 事前確認チェックリスト

importパスが全て同一のため確認事項は最小限。

**バックエンド:**
1. Alembicの最新リビジョンID（`alembic current`）→ カテゴリBの `down_revision` に使用
2. DockerfileでのXML/xmlsecシステムライブラリのインストール有無
3. `app/api/v1/router.py` の既存構成（ルーター登録方法の確認）
4. `app/main.py` の lifespan 関数の場所と構造
5. 移植先 `UserModel` のファイルパス（`sso_links` リレーション追記先）

**フロントエンド:**
6. `@/lib/cookie-utils`, `@/lib/csrf-utils` の存在確認
7. CSRF cookie名（`koiki_csrf_token`と異なる場合）
8. UIコンポーネントライブラリ（shadcn/uiが使われているか）
9. `@/lib/config` の `saml` 設定キーの有無
10. `NEXT_PUBLIC_API_BASE_URL` 環境変数名の確認

---

### ステップ1: システムライブラリ・Pythonパッケージの追加（リスク: 低）

**作業:**
- 移植先 `Dockerfile` にxml/xmlsecシステムライブラリを追加
- `pyproject.toml` に `python3-saml`, `xmlsec` を追加
- `uv lock && uv sync --locked`

**検証:**
```bash
python -c "from onelogin.saml2.auth import OneLogin_Saml2_Auth; print('OK')"
```

---

### ステップ2: カテゴリAファイルの一括コピー（リスク: ゼロ）

**バックエンドファイルをそのままコピー（import変更不要）:**
```
app/core/saml_config.py
app/schemas/saml.py
app/models/saml_auth_flow.py
app/models/user_sso.py
app/services/saml_metadata_loader.py
app/services/saml_certificate_manager.py
app/services/saml_service.py
app/repositories/saml_auth_flow_repository.py
app/repositories/user_sso_repository.py
app/api/v1/endpoints/saml_auth.py
tests/unit/app/services/test_saml_service.py
```

**その他ファイルをそのままコピー:**
```
frontend/src/lib/saml-storage.ts
frontend/src/hooks/use-saml-login.ts   # @/lib/config の saml キー存在を確認
frontend/src/app/api/saml/authorization/route.ts   # 環境変数名を確認
.env.saml.example
docs/saml/
docker/keycloak/realm-saml.json
```

**検証:**
```bash
python -c "from app.core.saml_config import SAMLSettings; print('OK')"
```

---

### ステップ3: DBモデル統合とマイグレーション移植（リスク: 低）

**作業:**

1. 移植先の `UserModel` に `sso_links` リレーションを追記（`user_sso.py` コピー後）：
   ```python
   # 移植先の UserModel クラスに追記
   sso_links: Mapped[list["UserSSOModel"]] = relationship(
       "UserSSOModel", back_populates="user", lazy="selectin"
   )
   ```

2. Alembicマイグレーション3ファイルをコピー後、`down_revision` を変更：
   - `20250908001_add_user_sso_table.py` の `down_revision` → 移植先の最新リビジョンID
   - `20251010001_add_app_columns_to_user_sso.py` の `down_revision` → `"20250908001"`（連鎖維持）
   - `20260228001_add_saml_auth_flow_table.py` の `down_revision` → `"20251010001"`（連鎖維持）

**注意:** `users` テーブル名が移植先でも `users` であることを確認。

**検証:**
```bash
uv run --locked alembic -c components/koiki_ref_app/alembic.ini upgrade head
# user_sso, saml_auth_flow テーブルが生成されること
```

---

### ステップ4: ルーターへのSAML登録（リスク: 低）

**作業:** 移植先の `app/api/v1/router.py` に追記：

```python
from .endpoints import saml_auth
router.include_router(saml_auth.router, prefix="/auth", tags=["SAML Authentication"])
```

**注意事項:**
- `SAML_RELAY_STATE_SIGNING_KEY` は本番で必ず新規生成すること

**検証:**
```bash
curl http://localhost:8000/api/v1/auth/saml/health
# 期待: {"status":"healthy",...}
```

---

### ステップ5: main.pyへのクリーンアップタスク統合（リスク: 低）

**作業:** 移植先の `lifespan` 関数に `_periodic_saml_flow_cleanup` タスクの起動/停止を追加。

参考実装（移植元 `app/main.py` の lifespan 内）:
```python
# startup
cleanup_task = asyncio.create_task(_periodic_saml_flow_cleanup())

# shutdown
cleanup_task.cancel()
try:
    await cleanup_task
except asyncio.CancelledError:
    pass
```

**検証:** 起動ログに `"SAML flow cleanup task started"` が出力されること

---

### ステップ6: フロントエンドの移植（リスク: 中）

**作業:**
1. `saml-storage.ts`, `use-saml-login.ts`, `authorization/route.ts` はステップ2でコピー済み
2. `@/lib/config` に `saml` キーがなければ追加（`use-saml-login.ts` が参照）
3. `frontend/src/app/api/saml/login/route.ts` のコピー後：
   - `cookie-utils`, `csrf-utils` が移植先になければ実装
   - リダイレクト先 `/dashboard` を移植先に合わせる
4. `frontend/src/app/auth/saml/callback/page.tsx` のコピー後：
   - `CSRF_COOKIE_NAME` を移植先の値に変更（現在: `koiki_csrf_token`）
   - UIコンポーネントを移植先に合わせる
   - `/api/auth/csrf` エンドポイントの存在確認
   - エラー時リダイレクト先 `/auth/login` を移植先に合わせる

**検証:**
```bash
npm run build
```

---

### ステップ7: E2E動作確認

**環境準備:**
- `.env.saml.example` を参考にSAML環境変数を `.env` に設定
- Keycloakをローカル起動（`docker/keycloak/realm-saml.json` を使用）

**確認手順:**
```bash
# 1. SAML設定ヘルスチェック
curl http://localhost:8000/api/v1/auth/saml/health
# 期待: {"status":"healthy",...}

# 2. SPメタデータ生成確認
curl http://localhost:8000/api/v1/auth/saml/metadata
# 期待: XML文書

# 3. AuthnRequest生成確認
curl "http://localhost:8000/api/v1/auth/saml/authorization?redirect_uri=http://localhost:3000/auth/saml/callback"
# 期待: sso_url, saml_request, relay_state を含むJSONレスポンス
```

**フロントエンドからのE2Eフロー:**
1. SAMLログインボタン → Keycloakにリダイレクト
2. Keycloakでログイン → `/auth/saml/callback` に戻る
3. JWTトークンがcookieに設定される
4. ダッシュボードへ遷移する

---

## CI/CDへの追加事項

```yaml
# GitHub Actions等のCI設定に追加
- name: Install xmlsec system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl pkg-config
```

---

## セキュリティ上の注意事項

1. **`SAML_RELAY_STATE_SIGNING_KEY`**: 本番環境では必ず新規生成すること
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
2. **`SAML_SP_ACS_URL`**: 本番環境ではHTTPS必須
3. **`SAML_SKIP_SSL_VERIFY=true`**: 開発環境のみ使用
4. **xmlsecの脆弱性確認**: 移植後に `pip-audit` を実行

---

## 関連ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [SAML_SETUP.md](SAML_SETUP.md) | SAML認証の初期セットアップ手順 |
| [saml-certificate-strategies.md](saml-certificate-strategies.md) | IdP証明書の取得戦略（4方式） |
| [saml-dynamic-certificate-test.md](saml-dynamic-certificate-test.md) | 動的証明書取得のテスト手順 |
| [saml-env-config-guide.md](saml-env-config-guide.md) | 環境変数設定ガイド |
| [saml-security-review.md](saml-security-review.md) | セキュリティレビュー結果 |
| [saml-idp-env-values-list](saml-idp-env-values-list) | IdP環境変数値一覧 |
