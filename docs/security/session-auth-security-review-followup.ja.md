# セッション認証セキュリティ点検 追確認整理

- 確認日: 2026-07-07
- 対象文書: `docs/security/session-auth-security-review.ja.md`
- 目的: React SPA 化に伴うセッション認証セキュリティ指摘について、現行コード上での成立状況、対応可否、追検討・判断事項を整理する。
- 備考: 初回整理時点ではソースコード変更・テスト実行は行っていない。
- 更新: 2026-07-07 に `F1`, `F2`, `F3`, `F4` の一部, `F6` の一部, `F9` を対応済み。2026-07-08 に `F5` の一部, `F7`, `F8`, `F10` の一部を対応済み。残件は本書の「対応状況」「追検討が必要な事項」を参照。

## 結論

元文書の主要指摘は、現行コードでも概ね成立している。

初回整理時に特に優先度が高いと判断した `F1`、`F2`、`F3` は対応済み。加えて、レートリミットについては、`app_factory.py` 側で Redis 対応の limiter を作っている一方、各 endpoint の decorator は `components/libkoiki/src/libkoiki/core/rate_limiter.py` のグローバル limiter を import しているため、Redis 設定が実際の decorator に効いていない可能性があった。したがって `F6` は元文書より強めに扱うべきものとして一部対応済み。

## 対応状況

| ID | 状態 | 対応内容・残件 |
|---|---|---|
| F1 todos CSRF 漏れ | 済み | todos の POST/PUT/DELETE に `CookieCSRFDep` を追加。追加確認で `business_clock` 更新 API にも `CookieCSRFDep` を追加。 |
| F2 CSRF 適用が手作業・順序依存 | 済み | `get_current_active_user()` に CSRF 検証を集約し、cookie 認証の unsafe request が route 個別設定漏れでも拒否されるよう変更。Bearer API は CSRF 対象外。 |
| F3 SSO redirect_uri fail-open | 済み | allowlist 未設定時は default redirect URI のみ許可し、default もなければ拒否する挙動に変更。`.env.example` の callback URL 誤りも修正。 |
| F4 access token 60分・logout 後失効なし | 一部済み | `ACCESS_TOKEN_EXPIRE_MINUTES` の既定値と example を 30 分へ短縮。本番 example は 15 分を維持。logout 後の access token denylist は Redis 等を前提に別設計。 |
| F5 CSRF TTL・鍵分離・非セッション拘束 | 一部済み | CSRF token に発行時刻を含め、`AUTH_CSRF_COOKIE_MAX_AGE_SECONDS` で TTL 検証するよう変更。署名鍵も `AUTH_CSRF_SECRET` へ分離。社内限定・同一オリジン・HTTPS・Domain 未指定前提では、現行の署名付き TTL double-submit 方式を当面許容する。セッション拘束 / `__Host-` Cookie 採用方針は強化候補として残す。 |
| F6 rate limit 実効性 | 一部済み | endpoint decorator が使う共有 limiter を app 起動設定で再構成するよう修正。Redis 分散 rate limit と ALB/proxy client IP key 方針は残件。 |
| F7 refresh Cookie Path | 済み | `AUTH_REFRESH_COOKIE_PATH` を追加し、refresh cookie を session auth route 配下へ限定。削除時は移行前の `/` path cookie も消去。 |
| F8 refresh token 再利用検知 | 済み | revoked refresh token の再利用を検知した場合、同一ユーザーの refresh token を全 revoke するよう変更。token family 方式は将来の拡張候補。 |
| F9 refresh 7日ハードコード | 済み | refresh rotation 時も `settings.REFRESH_TOKEN_EXPIRE_DAYS` を参照するよう変更。 |
| F10 既定値・ヘッダ・CI | 済み | production example で `AUTH_COOKIE_SECURE=true` を明示し、本番同一オリジン方針として CORS を無効化 / 最小化する設定例へ整理。frontend nginx に基本 security headers と CSP を追加。React SPA は参照実装のため frontend CI の必須ゲート化は保留し、`npm run build` / `npm run lint` の手動確認に留める。 |

## 対応可否・判断整理

| ID | 判断 | 整理 |
|---|---|---|
| F1 todos CSRF 漏れ | 対応済み | todos の POST/PUT/DELETE と `business_clock` 更新 API に `CookieCSRFDep` を追加済み。 |
| F2 CSRF 適用が手作業・順序依存 | 対応済み | `get_current_active_user()` に CSRF 検証を集約し、cookie 認証の unsafe request では route 個別の `CookieCSRFDep` 追加漏れがあっても fail-close する方針とした。 |
| F3 SSO redirect_uri fail-open | 対応済み | allowlist 未設定時は default redirect URI のみ許可し、default もなければ拒否する方針で対応済み。 |
| F4 access token 60分・logout 後失効なし | 一部対応済み | `ACCESS_TOKEN_EXPIRE_MINUTES` の既定値と example を 30 分へ短縮済み。access token denylist は Redis 等を前提にした設計判断。 |
| F5 CSRF TTL・鍵分離・非セッション拘束 | 一部対応済み | TTL と鍵分離は対応済み。社内限定システムとしては現行の署名付き TTL double-submit 方式を不十分とは扱わず、当面採用する。セッション拘束や `__Host-` Cookie 採用は配備条件も絡むため追検討。 |
| F6 rate limit 実効性 | 一部対応済み | endpoint decorator が使う共有 limiter を app 起動設定で再構成するよう修正済み。Redis 分散 rate limit と proxy headers 方針は残件。 |
| F7 refresh Cookie Path | 対応済み | refresh cookie は `AUTH_REFRESH_COOKIE_PATH` または `API_PREFIX + /auth/session` に限定。access / CSRF cookie は従来どおり `AUTH_COOKIE_PATH` を使用。 |
| F8 refresh token 再利用検知 | 対応済み | revoked token 再利用時は、同一ユーザー全 refresh token revoke で対応済み。token family / rotation chain は中期的な拡張候補。 |
| F9 refresh 7日ハードコード | 対応済み | refresh rotation 時も `settings.REFRESH_TOKEN_EXPIRE_DAYS` を参照するよう変更済み。 |
| F10 既定値・ヘッダ・CI | 対応済み | Cookie secure、CORS 本番方針、nginx security headers、CSP は対応済み。React SPA は参照実装で frontend stack は差し替え可能なため、frontend CI の必須ゲート化は現時点では保留。現行サンプルとして `npm run build` / `npm run lint` は手動確認済み。 |

## 推奨順序

1. 対応済み: `F1`, `F2`, `F3`, `F4` の一部, `F5` の一部, `F6` の一部, `F7`, `F8`, `F9`
2. 別タイミングで設計・運用判断: `F4` 残件, `F5` 残件, `F6` 残件

## 追検討が必要な事項

- `F10`: frontend CI の必須ゲート化は現時点では保留する。React SPA は参照実装であり、将来 Vue.js 等を含む別 frontend stack へ差し替え可能な位置づけとする。現行サンプルとして `npm run build` / `npm run lint` は手動確認済み。
- `F4`: logout 後の access token denylist は Redis 等の共有ストア前提のため、別タイミングで設計判断する。
- `F5`: CSRF token のセッション拘束を行うか。現行は署名付き・TTL 付き double-submit cookie 方式であり、社内限定・同一オリジン・HTTPS・`AUTH_COOKIE_DOMAIN` 未指定・CORS 最小化・CSP 維持を前提に当面許容する。導入する場合は access token / session identifier との結合方式と、refresh 時の token 再発行タイミングを別タイミングで設計する。
- `F5`: `__Host-` Cookie 採用は `Secure` 必須、`Domain` 未指定、`Path=/` 固定が前提。本番 HTTPS 配備方針と合わせて別タイミングで判断する。
- `F6`: Redis storage による分散 rate limit は将来対応として扱う。AWS ECS 2タスク想定では、当面は memory rate limit がタスク数分に緩む前提を明記する。
- `F6`: AWS ALB 配下では proxy headers / real client IP の扱いを本番前に別タイミングで決める。`X-Forwarded-For` は trusted proxy 経由時のみ信頼する方針が必要。

## 確認した主な根拠

- `components/libkoiki/src/libkoiki/api/v1/endpoints/todos.py`: todos 更新系に `CookieCSRFDep` を適用。
- `components/libkoiki/src/libkoiki/api/dependencies.py`: `get_current_active_user()` で cookie 認証の unsafe request に CSRF 検証を適用。
- `components/libkoiki/src/libkoiki/core/csrf.py`: `auth_method == "cookie"` の場合のみ unsafe request の CSRF を検証。CSRF token は発行時刻と `AUTH_CSRF_SECRET` 署名を持ち、TTL を検証する。
- `components/koiki_ref_app/src/koiki_ref_app/core/sso_config.py`: allowed redirect URI 未設定時に `is_redirect_uri_allowed()` が `True` を返す。
- `components/libkoiki/src/libkoiki/core/config.py`: access token 既定 30 分、開発既定は `AUTH_COOKIE_SECURE=False`。production example では `AUTH_COOKIE_SECURE=true`。
- `components/libkoiki/src/libkoiki/core/auth_cookies.py`: refresh cookie は session auth route 配下の専用 path、access / CSRF cookie は共通 path を使用。
- `components/libkoiki/src/libkoiki/services/auth_service.py`: refresh rotation 時の有効期限は `REFRESH_TOKEN_EXPIRE_DAYS` を参照。revoked refresh token 再利用時は同一ユーザーの refresh token を全 revoke。
- `components/libkoiki/src/libkoiki/core/rate_limiter.py`: グローバル limiter は `get_remote_address` + メモリ前提。
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`: Redis-aware limiter を作成して `app.state.limiter` に保持。
- `frontend/docker/nginx.conf`: SPA 静的配信側に X-Content-Type-Options、X-Frame-Options、Referrer-Policy、Permissions-Policy、Content-Security-Policy を設定。
