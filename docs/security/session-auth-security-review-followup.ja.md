# セッション認証セキュリティ点検 追確認整理

- 確認日: 2026-07-07
- 対象文書: `docs/security/session-auth-security-review.ja.md`
- 目的: React SPA 化に伴うセッション認証セキュリティ指摘について、現行コード上での成立状況、対応可否、追検討・判断事項を整理する。
- 備考: 初回整理時点ではソースコード変更・テスト実行は行っていない。
- 更新: 2026-07-07 に `F1`, `F2`, `F3`, `F4` の一部, `F6` の一部, `F9` を対応済み。2026-07-08 に `F5` の一部を対応済み。残件は本書の「対応状況」「追検討が必要な事項」を参照。

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
| F5 CSRF TTL・鍵分離・非セッション拘束 | 一部済み | CSRF token に発行時刻を含め、`AUTH_CSRF_COOKIE_MAX_AGE_SECONDS` で TTL 検証するよう変更。署名鍵も `AUTH_CSRF_SECRET` へ分離。セッション拘束 / `__Host-` Cookie 採用方針は残件。 |
| F6 rate limit 実効性 | 一部済み | endpoint decorator が使う共有 limiter を app 起動設定で再構成するよう修正。Redis 分散 rate limit と ALB/proxy client IP key 方針は残件。 |
| F7 refresh Cookie Path | 未対応 | refresh Cookie path 分離は未対応。frontend/backend の refresh endpoint path 影響確認が必要。 |
| F8 refresh token 再利用検知 | 未対応 | token family 方式または同一ユーザー全 refresh token revoke 方針の判断が必要。 |
| F9 refresh 7日ハードコード | 済み | refresh rotation 時も `settings.REFRESH_TOKEN_EXPIRE_DAYS` を参照するよう変更。 |
| F10 既定値・ヘッダ・CI | 未対応 | Cookie secure、CORS、nginx headers、CSP、frontend CI は運用・配備方針込みで分割対応。 |

## 対応可否・判断整理

| ID | 判断 | 整理 |
|---|---|---|
| F1 todos CSRF 漏れ | 対応済み | todos の POST/PUT/DELETE と `business_clock` 更新 API に `CookieCSRFDep` を追加済み。 |
| F2 CSRF 適用が手作業・順序依存 | 対応済み | `get_current_active_user()` に CSRF 検証を集約し、cookie 認証の unsafe request では route 個別の `CookieCSRFDep` 追加漏れがあっても fail-close する方針とした。 |
| F3 SSO redirect_uri fail-open | 対応済み | allowlist 未設定時は default redirect URI のみ許可し、default もなければ拒否する方針で対応済み。 |
| F4 access token 60分・logout 後失効なし | 一部対応済み | `ACCESS_TOKEN_EXPIRE_MINUTES` の既定値と example を 30 分へ短縮済み。access token denylist は Redis 等を前提にした設計判断。 |
| F5 CSRF TTL・鍵分離・非セッション拘束 | 一部対応済み | TTL と鍵分離は対応済み。セッション拘束や `__Host-` Cookie 採用は配備条件も絡むため追検討。 |
| F6 rate limit 実効性 | 一部対応済み | endpoint decorator が使う共有 limiter を app 起動設定で再構成するよう修正済み。Redis 分散 rate limit と proxy headers 方針は残件。 |
| F7 refresh Cookie Path | 対応可 | `components/libkoiki/src/libkoiki/core/auth_cookies.py` で access / refresh が共通 path `/`。refresh 用 path 設定を分離すれば対応可能。 |
| F8 refresh token 再利用検知 | 中期対応 | revoked token は単に invalid 扱い。ファミリー概念を入れるか、同一ユーザー全 refresh token revoke にするか判断が必要。 |
| F9 refresh 7日ハードコード | 対応済み | refresh rotation 時も `settings.REFRESH_TOKEN_EXPIRE_DAYS` を参照するよう変更済み。 |
| F10 既定値・ヘッダ・CI | 混在 | Cookie secure、CORS、nginx headers、CSP、frontend CI はそれぞれ運用・配備方針の確認が必要。SPA 静的配信 nginx には現状セキュリティヘッダがない。 |

## 推奨順序

1. 対応済み: `F1`, `F2`, `F3`, `F4` の一部, `F5` の一部, `F6` の一部, `F9`
2. 設定・運用で短期に固める: `AUTH_COOKIE_SECURE`, nginx security headers
3. 本番前に判断する: `F6` の ALB/proxy client IP key 方針
4. 中期基盤強化: `F5`, `F7`, `F8`, CSP, frontend CI

## 追検討が必要な事項

- `F6`: Redis storage による分散 rate limit は将来対応として扱う。AWS ECS 2タスク想定では、当面は memory rate limit がタスク数分に緩む前提を明記する。
- `F6`: AWS ALB 配下では proxy headers / real client IP の扱いを本番前に決める。`X-Forwarded-For` は trusted proxy 経由時のみ信頼する方針が必要。
- `F5`: CSRF token のセッション拘束を行うか。導入する場合は access token / session identifier との結合方式と、refresh 時の token 再発行タイミングを設計する。
- `F5`: `__Host-` Cookie 採用は `Secure` 必須、`Domain` 未指定、`Path=/` 固定が前提。本番 HTTPS 配備方針と合わせて判断する。
- `F8`: refresh token reuse 検知時に token family を全失効するか、既存モデルのまま同一ユーザー全 refresh token を失効するか。

## 確認した主な根拠

- `components/libkoiki/src/libkoiki/api/v1/endpoints/todos.py`: todos 更新系に `CookieCSRFDep` なし。
- `components/libkoiki/src/libkoiki/api/dependencies.py`: `get_current_active_user()` で cookie 認証の unsafe request に CSRF 検証を適用。
- `components/libkoiki/src/libkoiki/core/csrf.py`: `auth_method == "cookie"` の場合のみ unsafe request の CSRF を検証。CSRF token は発行時刻と `AUTH_CSRF_SECRET` 署名を持ち、TTL を検証する。
- `components/koiki_ref_app/src/koiki_ref_app/core/sso_config.py`: allowed redirect URI 未設定時に `is_redirect_uri_allowed()` が `True` を返す。
- `components/libkoiki/src/libkoiki/core/config.py`: access token 既定 30 分、`AUTH_COOKIE_SECURE=False`。
- `components/libkoiki/src/libkoiki/core/auth_cookies.py`: access / refresh / csrf cookie path が共通。
- `components/libkoiki/src/libkoiki/services/auth_service.py`: refresh rotation 時の有効期限が `days=7` 固定。
- `components/libkoiki/src/libkoiki/core/rate_limiter.py`: グローバル limiter は `get_remote_address` + メモリ前提。
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`: Redis-aware limiter を作成して `app.state.limiter` に保持。
- `frontend/docker/nginx.conf`: SPA 静的配信側にセキュリティヘッダ設定なし。
