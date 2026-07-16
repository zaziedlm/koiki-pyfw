# KOIKI-FW v0.8.0 Release Notes

## 概要

KOIKI-FW v0.8.0 は、v0.7 系で整理した framework layer / reference application layer の分離を維持しながら、reference frontend、ブラウザ認証契約、DB 基盤を刷新するリリースです。

主な変更は、Next.js BFF から Vite + React SPA への全面移行、Cookie セッション認証と CSRF / CSP の強化、DB vNext ベースラインへの移行、および Todo API の楽観的ロック導入です。

## 主要変更点

### Vite + React SPA への全面移行

- reference frontend を Next.js BFF から Vite + React SPA へ移行
- Next.js サーバーランタイムと frontend 側 API proxy routes を撤去
- React Router と TanStack Query を用いた feature-based 構成へ整理
- production では非特権 nginx が静的 SPA を配信
- `check-types`、`lint`、`test`、`build` を実行する frontend CI を `dev/v0.8` 向けに有効化

### Cookie セッション認証とブラウザセキュリティ

- `/api/v1/auth/session/*` にブラウザ SPA 向けのセッション API を追加
- access token / refresh token を HttpOnly Cookie で管理
- HMAC 署名付き double-submit token による CSRF 検証を導入
- Cookie 認証による unsafe request に CSRF header を必須化
- refresh token rotation と再利用検知を追加
- SSO / SAML callback でも同じ session Cookie 契約を使用
- 許可リスト外の SSO / SAML redirect URI を fail-closed で拒否
- nginx に CSP、`X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy` を追加

### DB vNext ベースライン

- Alembic の従来 migration 履歴を単一の `vnext_baseline` migration に再構成
- table ownership を接頭辞で明確化
  - `koiki_*`: `libkoiki` 所有
  - `kkref_*`: `koiki_ref_app` 所有
  - `kkbiz_*`: downstream business layer 所有
- production-safe な reference bootstrap と development-only seed を分離
- Web runtime 内の認証・SAML データ定期 cleanup を撤去し、外部の単一実行バッチ基盤で管理する方針へ変更

### Todo API の競合制御

- Todo に `version` を追加
- `UPDATE ... WHERE version = ?` による atomic な楽観的ロックを導入
- resource が存在しない場合の 404 と、古い version による競合の 409 を区別
- frontend で 409 を通知し、再取得した最新状態を表示

### Runtime / operation

- project、`libkoiki`、`koiki_ref_app` の version を `0.8.0` に統一
- unified Compose stack の `UVICORN_WORKERS` 既定値を `1` に変更
- ECS ではコンテナ内 worker 数ではなく service task 数でスケールする方針を明確化
- production 設定例で Cookie、CSRF、same-origin 配備、frontend build input を整理

### Documentation / Agent guidance

- `docs/design_kkfw_0.8.0.md` を現行アーキテクチャの正本として追加
- `docs/frontend-spa-implementation-guide.ja.md` を追加
- root `frontend/` 専用の `koiki-frontend-work` Agent Skill を追加
- 完了済み v0.7 タスク文書を削除または `docs/archive/` へ移動

## 重要な互換性・移行上の注意

### 既存 DB は直接アップグレードできません

v0.8.0 の DB vNext ベースラインは、v0.7 系以前の Alembic migration continuity を維持しません。既存 DB に対して通常の `alembic upgrade head` だけで段階移行することは想定していません。

v0.7 系以前のデータを引き継ぐ場合は、リリース適用前に次を実施してください。

1. DB backup と rollback 手順を確保する
2. `docs/dev/db-vnext-migration-note.ja.md` と `docs/dev/db-vnext-rebuild-runbook.ja.md` を確認する
3. 対象環境用のデータ移行または再構築手順を別途用意する
4. staging 相当環境で schema、seed、認証、業務データを検証する

### Frontend deployment

- Next.js server / BFF 前提の配備構成は利用できません。
- production frontend は Vite build artifact を nginx で配信します。
- same-origin 配備を推奨し、別 origin の場合は CORS、Cookie `SameSite` / `Secure`、CSRF transport を一体で設計してください。
- `VITE_*` は browser に公開される build-time 値であり、secret を含めないでください。

### Auth / Cookie configuration

- production では `AUTH_COOKIE_SECURE=true` が必要です。
- `JWT_SECRET` と `AUTH_CSRF_SECRET` は別々の production secret を設定してください。
- SSO / SAML 利用時は、IdP callback URI と許可 redirect URI を production 値で再確認してください。

### Compatibility entrypoint

- 標準 ASGI entrypoint は `koiki_ref_app.asgi:app` です。
- `app.main:app` は v0.8.0 でも compatibility wrapper として維持します。
- root `app/` は新規実装の配置先ではありません。

## リリース検証

タグ作成前に、`main` へ取り込まれたリリース対象コミットで次を確認します。

### Backend

```powershell
$env:DEBUG = "False"
uv lock --check
uv run --locked python -c "import libkoiki; print(libkoiki.__version__)"
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.version)"
uv run --locked pytest components/libkoiki/tests components/koiki_ref_app/tests -m "not db_integration"
uv run --locked pytest tests/unit/agent_guidance
```

### Frontend

```powershell
Set-Location frontend
npm ci
npm run check-types
npm run lint
npm test
npm run build
```

### DB / runtime

```powershell
$env:DEBUG = "False"
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
.\scripts\run-db-integration-tests.ps1
```

必要に応じて unified Compose stack を起動し、次を確認します。

- `/health` が version `0.8.0` を返す
- password login、session refresh、logout
- Todo list / create / update / completion toggle / delete
- 古い Todo version に対する 409 response と frontend の再取得
- CSRF header がない Cookie 認証の unsafe request が拒否される
- 対象環境の SSO / SAML login、callback、logout
- SPA deep link の nginx fallback

## リリース確定記録

タグ作成時に以下を記録します。

- Release tag: `v0.8.0`
- Release commit: 未確定
- Release date: 未確定
- Backend CI: 未確認
- Frontend CI: 未確認
- DB integration / migration rehearsal: 未確認
- Browser smoke / SSO / SAML: 対象環境に応じて未確認

## 関連文書

- `docs/design_kkfw_0.8.0.md`
- `docs/frontend-spa-implementation-guide.ja.md`
- `docs/dev/react-spa-adoption-release-gates.ja.md`
- `docs/dev/react-spa-migration-completion.ja.md`
- `docs/dev/db-vnext-baseline-adr.md`
- `docs/dev/db-vnext-schema-contract.ja.md`
- `docs/dev/db-vnext-index-design.ja.md`
- `docs/dev/db-vnext-migration-note.ja.md`
- `docs/dev/db-vnext-rebuild-runbook.ja.md`
- `docs/dev/auth-table-maintenance.ja.md`
- `docs/releases/KOIKI-FW_0.7.0.md`
