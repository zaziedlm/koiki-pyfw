# セッション認証セキュリティ点検 追確認整理

- 確認日: 2026-07-07
- 対象文書: `docs/security/session-auth-security-review.ja.md`
- 目的: React SPA 化に伴うセッション認証セキュリティ指摘について、現行コード上での成立状況、対応可否、追検討・判断事項を整理する。
- 備考: この整理時点ではソースコード変更・テスト実行は行っていない。
- 更新: 2026-07-07 に `F1`, `F3`, `F6` の一部, `F9` を対応済み。残件は本書の「対応状況」「追検討が必要な事項」を参照。

## 結論

元文書の主要指摘は、現行コードでも概ね成立している。

特に優先度が高いのは `F1`、`F2`、`F3`。加えて、レートリミットについては、`app_factory.py` 側で Redis 対応の limiter を作っている一方、各 endpoint の decorator は `components/libkoiki/src/libkoiki/core/rate_limiter.py` のグローバル limiter を import しているため、Redis 設定が実際の decorator に効いていない可能性がある。したがって `F6` は元文書より強めに扱うべき。

## 対応状況

| ID | 状態 | 対応内容・残件 |
|---|---|---|
| F1 todos CSRF 漏れ | 済み | todos の POST/PUT/DELETE に `CookieCSRFDep` を追加。追加確認で `business_clock` 更新 API にも `CookieCSRFDep` を追加。 |
| F2 CSRF 適用が手作業・順序依存 | 未対応 | 個別追加は進んだが、middleware / route-level / fail-close などの再発防止設計は未対応。 |
| F3 SSO redirect_uri fail-open | 済み | allowlist 未設定時は default redirect URI のみ許可し、default もなければ拒否する挙動に変更。`.env.example` の callback URL 誤りも修正。 |
| F4 access token 60分・logout 後失効なし | 未対応 | 期限短縮は設定対応候補。access token denylist は Redis 等を前提に別設計。 |
| F5 CSRF TTL・鍵分離・非セッション拘束 | 未対応 | 中期対応。CSRF TTL / 鍵分離 / セッション拘束 / `__Host-` Cookie 採用方針を分けて検討。 |
| F6 rate limit 実効性 | 一部済み | endpoint decorator が使う共有 limiter を app 起動設定で再構成するよう修正。Redis 分散 rate limit と ALB/proxy client IP key 方針は残件。 |
| F7 refresh Cookie Path | 未対応 | refresh Cookie path 分離は未対応。frontend/backend の refresh endpoint path 影響確認が必要。 |
| F8 refresh token 再利用検知 | 未対応 | token family 方式または同一ユーザー全 refresh token revoke 方針の判断が必要。 |
| F9 refresh 7日ハードコード | 済み | refresh rotation 時も `settings.REFRESH_TOKEN_EXPIRE_DAYS` を参照するよう変更。 |
| F10 既定値・ヘッダ・CI | 未対応 | Cookie secure、CORS、nginx headers、CSP、frontend CI は運用・配備方針込みで分割対応。 |

## 対応可否・判断整理

| ID | 判断 | 整理 |
|---|---|---|
| F1 todos CSRF 漏れ | 対応可。即対応候補 | `components/libkoiki/src/libkoiki/api/v1/endpoints/todos.py` の POST/PUT/DELETE に `CookieCSRFDep` がない。小改修で対応可能。 |
| F2 CSRF 適用が手作業・順序依存 | 要設計判断 | 個別依存追加だけでは再発する。middleware / route-level 一括適用、または `CookieCSRFDep` fail-close 化のどちらを採るか決める必要がある。 |
| F3 SSO redirect_uri fail-open | 要設計判断。短期対応推奨 | `components/koiki_ref_app/src/koiki_ref_app/core/sso_config.py` で allowed redirect URI 未設定時に許可される。未設定拒否、default のみ許可、wildcard 制限の方針決定が必要。 |
| F4 access token 60分・logout 後失効なし | 一部は設定対応可 | まず `ACCESS_TOKEN_EXPIRE_MINUTES` を 15-30 分へ短縮するのが現実的。access token denylist は Redis 等を前提にした設計判断。 |
| F5 CSRF TTL・鍵分離・非セッション拘束 | 中期対応 | TTL と鍵分離は対応しやすい。セッション拘束や `__Host-` Cookie 採用は配備条件も絡むため追検討。 |
| F6 rate limit 実効性 | 要再設計・運用確認 | endpoint が `components/libkoiki/src/libkoiki/core/rate_limiter.py` のメモリ limiter を使っているため、`components/koiki_ref_app/src/koiki_ref_app/app_factory.py` の Redis-aware limiter と統一が必要そう。proxy headers 方針も必要。 |
| F7 refresh Cookie Path | 対応可 | `components/libkoiki/src/libkoiki/core/auth_cookies.py` で access / refresh が共通 path `/`。refresh 用 path 設定を分離すれば対応可能。 |
| F8 refresh token 再利用検知 | 中期対応 | revoked token は単に invalid 扱い。ファミリー概念を入れるか、同一ユーザー全 refresh token revoke にするか判断が必要。 |
| F9 refresh 7日ハードコード | 対応可。即対応候補 | `components/libkoiki/src/libkoiki/services/auth_service.py` の rotation 時だけ `days=7` 固定。settings 参照へ変更する低リスク修正。 |
| F10 既定値・ヘッダ・CI | 混在 | Cookie secure、CORS、nginx headers、CSP、frontend CI はそれぞれ運用・配備方針の確認が必要。SPA 静的配信 nginx には現状セキュリティヘッダがない。 |

## 推奨順序

1. すぐ直す: `F1`, `F9`
2. 先に方針を決めてから直す: `F2`, `F3`, `F6`
3. 設定・運用で短期に固める: `F4`, `AUTH_COOKIE_SECURE`, nginx security headers
4. 中期基盤強化: `F5`, `F7`, `F8`, CSP, frontend CI

## 追検討が必要な事項

- `F2`: CSRF を middleware で一括適用するか、router-level dependency に寄せるか、既存 `CookieCSRFDep` を fail-close 化するか。
- `F6`: Redis storage による分散 rate limit は将来対応として扱う。AWS ECS 2タスク想定では、当面は memory rate limit がタスク数分に緩む前提を明記する。
- `F6`: AWS ALB 配下では proxy headers / real client IP の扱いを本番前に決める。`X-Forwarded-For` は trusted proxy 経由時のみ信頼する方針が必要。
- `F8`: refresh token reuse 検知時に token family を全失効するか、既存モデルのまま同一ユーザー全 refresh token を失効するか。

## 確認した主な根拠

- `components/libkoiki/src/libkoiki/api/v1/endpoints/todos.py`: todos 更新系に `CookieCSRFDep` なし。
- `components/libkoiki/src/libkoiki/api/dependencies.py`: `CookieCSRFDep` は `request.state.auth_method` に依存。
- `components/libkoiki/src/libkoiki/core/csrf.py`: `auth_method == "cookie"` の場合のみ unsafe request の CSRF を検証。
- `components/koiki_ref_app/src/koiki_ref_app/core/sso_config.py`: allowed redirect URI 未設定時に `is_redirect_uri_allowed()` が `True` を返す。
- `components/libkoiki/src/libkoiki/core/config.py`: access token 既定 60 分、`AUTH_COOKIE_SECURE=False`。
- `components/libkoiki/src/libkoiki/core/auth_cookies.py`: access / refresh / csrf cookie path が共通。
- `components/libkoiki/src/libkoiki/services/auth_service.py`: refresh rotation 時の有効期限が `days=7` 固定。
- `components/libkoiki/src/libkoiki/core/rate_limiter.py`: グローバル limiter は `get_remote_address` + メモリ前提。
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`: Redis-aware limiter を作成して `app.state.limiter` に保持。
- `frontend/docker/nginx.conf`: SPA 静的配信側にセキュリティヘッダ設定なし。
