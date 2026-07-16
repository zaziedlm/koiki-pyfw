# セッション認証契約 `/api/v1/auth/session/*` セキュリティ点検報告

- 点検日: 2026-07-07
- 対象: `dev/v0.7-react-only`(HEAD `287aeca`)の Cookie セッション認証基盤一式
  - `components/libkoiki/src/libkoiki/api/v1/endpoints/auth_session.py`
  - `components/libkoiki/src/libkoiki/core/auth_cookies.py` / `csrf.py` / `security.py` / `rate_limiter.py`
  - `components/libkoiki/src/libkoiki/api/dependencies.py`
  - `components/libkoiki/src/libkoiki/services/auth_service.py`
  - `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py` / `saml_auth.py`
  - `components/koiki_ref_app/src/koiki_ref_app/services/sso_service.py`、`core/sso_config.py` / `saml_config.py`
  - 周辺: CORS(`app_factory.py`)、セキュリティヘッダ(`middleware.py`)、nginx、CI
- 方法: リクエスト全経路(CSRF → 認証 → 認可 → トークンライフサイクル → 配備)の実装読解。
  移行前(`dev/v0.7`)との比較を含む。推測による断定はせず、根拠をファイル:行で示す。

---

## 1. 総評

セッション契約の中核(CSRF の暗号学的設計、トークンの httpOnly Cookie 化、
レスポンスボディへのトークン非露出、refresh のローテーション、既存ロックアウト・監査
ロジックの共有)は**堅実に構成されており、移行によって旧 BFF 実装より強化された面が多い**。

一方で、(a) CSRF 検証の適用が「エンドポイント作者の手作業」に依存して漏れが生じている点
(todos)、(b) 設定未投入時に安全側へ倒れない箇所(SSO redirect_uri の fail-open、
`AUTH_COOKIE_SECURE=false` 既定)、(c) アクセストークンの失効性(logout 後も最長 60 分有効、
旧構成の Cookie 30 分より実効寿命が伸びた)という **「既定値と運用に依存する弱点」** が残る。

---

## 2. 良好と確認できた点(維持すべき性質)

| # | 性質 | 根拠 |
|---|---|---|
| G1 | ログイン・登録にも CSRF 検証(ログイン CSRF 対策)。認証前に `require_valid_csrf_token` を直呼び | `auth_session.py:69,106` |
| G2 | CSRF トークンは HMAC-SHA256 署名付き+`hmac.compare_digest` による定数時間比較 | `csrf.py:19-43` |
| G3 | トークン値をセッション契約のレスポンスボディに一切含めない(統合テストで担保) | `auth_session.py:81-90,172-179`、`test_auth_session_api.py` |
| G4 | access/refresh は `httponly=True`。SameSite validator あり(lax/strict/none 限定) | `auth_cookies.py:17-35`、`config.py:74-80` |
| G5 | refresh token は SHA-256 ハッシュで保存(DB 漏えい時に平文トークンが漏れない)、形式検証あり | `security.py:225-235`、`auth_service.py:94-96` |
| G6 | refresh はローテーション(`enable_rotation=True`)、失敗時は Cookie 全消去+セキュリティイベント記録 | `auth_session.py:148-170` |
| G7 | logout は refresh token を DB 失効+Cookie 消去。CSRF 検証付き | `auth_session.py:182-200` |
| G8 | セッション login は既存 `/auth/login` とロックアウト・段階遅延・監査ログ・メトリクスを完全共有(新しい入口が防御を迂回しない) | `auth_basic.py:29-120`(`authenticate_password_and_create_token_pair`) |
| G9 | Bearer ヘッダが**存在すれば** Cookie にフォールバックしない(不正 Bearer → 401)。`auth_method` は検証成功後にのみ設定 | `security.py:124-138` |
| G10 | 毎リクエストで DB からユーザー実在・`is_active` を再確認(JWT 単独を信用しない) | `dependencies.py:163-190` |
| G11 | SSO state は HMAC 署名+nonce 拘束+TTL 検証をサーバ側で実施 | `sso_service.py:604-650` |
| G12 | SSO は署名アルゴリズム許可リスト・メールドメイン許可リストを強制 | `sso_service.py:76-79,188-190` |
| G13 | CORS は明示 origin リスト+`allow_credentials=True`(`*`+credentials の危険構成ではない) | `app_factory.py:258-266` |
| G14 | `/session/me` の `UserResponse` に資格情報系フィールドなし(roles は含む) | `schemas/user.py:59-66` |

---

## 3. 指摘事項

重要度: **高**(現実的な攻撃経路または防御の欠落)/**中**(条件付きで顕在化、
または多層防御の欠け)/**低**(堅牢化・整合性)。

### F1【高】todos 更新系に Cookie 認証時 CSRF 検証が未適用(既報・再掲)

- 内容: `CookieCSRFDep` は users 更新系 3 本のみ。`todos.py` の POST/PUT/DELETE と
  ルータ登録(`router.py:20`)のどちらにも CSRF 依存がない。SPA はヘッダを送るが検証されない。
- 顕在化条件: `AUTH_COOKIE_SAMESITE=none`(クロスオリジン配置)運用、または SameSite を
  尊重しない旧ブラウザ。既定 lax では大部分緩和されるが、防御が「ブラウザの仕様」任せになる。
- 推奨: `CookieCSRFDep` を todos 更新系へ追加。さらに恒久策として F2 参照。

### F2【高】CSRF 検証の適用がエンドポイント作者の手作業+依存の宣言順に依存する構造

- 内容: `require_csrf_for_cookie_auth` は `request.state.auth_method == "cookie"` を見るが、
  この値は認証依存(`get_user_from_token` → `security.py:138`)が設定する。
  FastAPI は依存を signature の宣言順に解決するため、**`CookieCSRFDep` を認証依存より
  先に書くと `auth_method` 未設定 → Cookie 認証と判定されず、CSRF 検証が静かにスキップ**される。
- 現状: `users.py:92,193,241` はいずれも正しい順序(ActiveUserDep → CookieCSRFDep)だが、
  順序を保証するテスト・Lint はなく、todos の漏れ(F1)と同根の「作者依存」構造。
- 推奨: いずれかの構造的対策。
  1. ミドルウェア(または `APIRouter(dependencies=[...])`)で「Cookie 認証+unsafe メソッド」を
     一括検証し、エンドポイント個別付与をやめる
  2. `CookieCSRFDep` が `auth_method` 未設定時に**例外を出す**(fail-close)よう変更
- 根拠: `api/dependencies.py:186,195-200`、`core/csrf.py:65-77`

### F3【高→運用条件依存】SSO redirect_uri 許可リストが fail-open

- 内容: `is_redirect_uri_allowed` は **`SSO_ALLOWED_REDIRECT_URIS` 未設定なら常に True**
  (`sso_config.py:168-170`)。さらに `*` を含むパターンは `fnmatch` で照合されるため、
  `https://*` のような過寛容パターンを設定できてしまう。
- 影響: 認可リクエストの `redirect_uri` を攻撃者が誘導できると、認可コードの漏えい
  (コード横取り)につながり得る。PKCE(S256)と IdP 側の redirect_uri 登録が第 2・第 3 の
  防壁になるため即座に破られるわけではないが、アプリ層としては安全側でない。
- 対比: **SAML 側は同じ状況でデフォルト URI へフォールバックする設計(安全側)**
  (`saml_config.py:227-238`)で、SSO と SAML で思想が非対称。
- 推奨: 未設定時は**拒否**(または default のみに限定)へ変更し、ワイルドカードは
  廃止かホスト固定パターンに制限。`.env.example` に必須設定として明記。

### F4【中】logout してもアクセストークンは失効しない+実効寿命が移行で倍増

- 内容: JWT はステートレスで、失効リスト(denylist)は存在しない。logout が失効させるのは
  refresh token のみ(`auth_session.py:191-196`)。窃取・残存した access token は
  期限まで有効。
- 移行での変化: 旧 BFF はブラウザ側 Cookie を **30 分**(`dev/v0.7:frontend/src/lib/cookie-utils.ts:8`)
  に制限していたが、新構成の access Cookie は `ACCESS_TOKEN_EXPIRE_MINUTES`(既定 **60 分**、
  `config.py:8`、`auth_cookies.py:9-10`)と同寿命。**ブラウザが保持する資格情報の実効寿命が
  移行で 30 分→60 分に伸びた**(意図的か不明。移行計画に言及なし=考慮漏れの可能性)。
- 推奨: `ACCESS_TOKEN_EXPIRE_MINUTES` を 15〜30 分へ短縮(refresh がシームレスに補うため
  UX 影響は小さい)。高保証が必要なら logout 時の access token denylist(Redis)を検討。

### F5【中】CSRF トークンがセッション非拘束・無期限・鍵共用

- 内容(3 点、いずれも `csrf.py`):
  1. トークンはユーザー/セッションに紐付かない(`nonce.署名` のみ)。攻撃者も `/csrf` から
     **正規の署名済みトークンを取得できる**ため、署名はトークン偽造は防ぐが、
     サブドメインからの Cookie 注入(cookie tossing)には無力。`AUTH_COOKIE_DOMAIN` を
     親ドメインに広げた運用で顕在化する。
  2. nonce にタイムスタンプがなく**署名は無期限有効**(Cookie の 24h は保持期限にすぎない)。
  3. 署名鍵が `JWT_SECRET` と共用(`csrf.py:20`)。鍵分離の原則に反し、用途間の
     相互影響(ローテーション巻き添え等)がある。
- 推奨: トークンへ発行時刻を含め TTL 検証を追加。鍵は HKDF 等で用途別導出。
  ホスト限定が必要な配備では `__Host-` プレフィックス Cookie の採用を検討。
  (セッション拘束化は仕組み上大きめの変更のため、まず 2・3 から)

### F6【中】レート制限の実効性が配備条件に依存

- 内容: `slowapi` の limiter は **ストレージ未指定(プロセス内メモリ)+
  `get_remote_address`(直接ソケットの IP)キー**(`rate_limiter.py:11-14`)。
  - 複数インスタンス構成では制限が共有されない(実質 N 倍に緩む)
  - ALB/リバースプロキシ背後で proxy headers を処理しない場合、全クライアントが
    同一 IP に見え、正規ユーザー巻き込みの 429 か、制限の無効化が起きる
- 緩和要素: email/IP 単位のロックアウトと段階遅延は **DB ベース**(`login_security_service`)
  で別立てのため、ブルートフォース防御自体は多層。
- 推奨: 本番プロファイルで Redis storage を設定し、`--proxy-headers` 等の
  X-Forwarded-For 処理と組み合わせてキーを実クライアント IP にする。

### F7【中】refresh token Cookie の Path が広すぎる

- 内容: `AUTH_COOKIE_PATH` 既定 `/` が access/refresh 共通のため、**refresh token が
  全リクエストに送信**される(`auth_cookies.py:17-27`)。refresh を必要とするのは
  `/api/v1/auth/session/refresh`(と logout)のみ。
- 推奨: refresh Cookie の Path を `/api/v1/auth/session` に限定する設定分離。
  露出面(ログ・中間装置・誤配信)を減らせる。

### F8【中】refresh token の再利用検知がない

- 内容: ローテーション後の旧トークンが再提示された場合、`get_valid_token` が None を
  返して 401 になるだけ(`auth_service.py:103-107`)。**「失効済みトークンの再利用」は
  盗難の強いシグナル**だが、検知してユーザーの全トークンを失効させる処理
  (`revoke_user_tokens` は既存)や専用セキュリティイベントはない。
- 推奨: 失効済み(revoked)トークンとの照合に成功した場合はファミリー全失効+
  `security_logger` へ専用イベントを記録。

### F9【低】ローテーション時の refresh 有効期限がハードコード

- 内容: 新規発行は `settings.REFRESH_TOKEN_EXPIRE_DAYS` を使うのに、ローテーション時は
  `days=7` 固定(`auth_service.py:139` vs `:57`)。設定変更時に不整合。
- 推奨: settings 参照に統一。

### F10【低】既定値・付帯設定(既報の再掲+補足)

- `AUTH_COOKIE_SECURE` 既定 false(`config.py:65`)— 本番 HTTPS で true 必須。
  起動時に `APP_ENV=production && !SECURE` を警告する仕組みがあると事故を防げる。
- CSP 未設定(`middleware.py:159-160` コメントアウト、nginx にもなし)。
- nginx の SPA 応答にセキュリティヘッダなし(旧 `next.config.ts` にはあった。移行時の補填漏れ)。
- CORS の `allow_methods=["*"]` / `allow_headers=["*"]`(`app_factory.py:263-264`)— origin が
  厳密なら実害は小さいが最小権限でない。
- セッション login 応答の `roles: []` 固定(`auth_session.py:47`)— SPA がログイン応答だけで
  ロール判定すると誤る(現実装は `/session/me` 使用のため実害なし。契約として明文化を)。
- CI にフロントエンド検証ジョブなし(`.github/workflows/ci.yml`)。
- `/auth/session/register` は無認証の自己登録(既存 `/auth/register` とパリティ)。
  これが業務要件として意図か(招待制にすべきか)は設計判断事項。

---

## 4. 移行前から持ち越された懸念 vs 移行で生じた懸念

| 区分 | 項目 |
|---|---|
| 移行前から存在(持ち越し) | F5-1(旧 CSRF も非拘束。むしろ旧は署名すらなかった)、F6(limiter 構成は従来から)、F8・F9(refresh 系は既存実装)、SSO fail-open(F3、既存 sso_config)、CORS `*` methods、自己登録 |
| 移行で新たに生じた | F1(todos: 旧 BFF は全 route handler で一律 CSRF 検証していたため、移行で**適用単位が「一括」→「個別」に変わった**ことが漏れの根因)、F2(auth_method 連動という新機構の構造的弱点)、F4 の寿命倍増、nginx ヘッダ欠落 |
| 移行で改善された | CSRF 署名化・定数時間比較、トークンのボディ非露出、Cookie 属性のサーバ側一元管理、非特権 nginx、フロント env からの内部情報排除 |

## 5. 推奨対応の優先順位

1. **即時(コード小改修)**: F1(todos へ CSRF 依存追加)、F9(ハードコード解消)
2. **短期(構造改善)**: F2(CSRF 一括適用 or fail-close 化)、F3(redirect_uri fail-close)、
   F4(アクセストークン 15〜30 分化)、F10 の nginx ヘッダ・SECURE 警告
3. **中期(基盤強化)**: F5(CSRF TTL・鍵分離)、F6(Redis limiter + proxy headers)、
   F7(refresh Path 限定)、F8(再利用検知)、CSP 設計、CI へのフロントジョブ追加

いずれも `docs/agent/auth-security.md` の規約(単体+統合の複数角度検証、失敗フローの検証)
に従って実装・検証すること。F1/F2 は `test_auth_session_api.py` に
「todos への Cookie 認証 CSRF なしリクエストが 403 になる」ケースを追加して固定化するのが良い。
