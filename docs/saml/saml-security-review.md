# SAML連携実装 点検メモ

本ドキュメントは、KOIKI-FW の SAML 連携（IdP: HENNGE ONE 想定）の実装について、フロントエンドからバックエンドまでの処理フローとセキュリティ観点の点検結果をまとめたものです。

## フロー概要

1. **フロントエンドでのログイン開始**
   - ユーザー操作で `useSamlLogin` フックを通じて Next.js API (`/api/saml/authorization`) を呼び出し、RelayState を含む認可リクエスト情報を取得する。【F:frontend/src/hooks/use-saml-login.ts†L39-L63】
   - 取得した RelayState やリダイレクト先を `sessionStorage` に保存し、IdP の SSO エンドポイントへブラウザをリダイレクトする。【F:frontend/src/hooks/use-saml-login.ts†L53-L63】

2. **Next.js API からバックエンド API 呼び出し**
   - Next.js 側の API ルートが `redirect_uri` を検証した上でバックエンドの `/api/v1/auth/saml/authorization` にプロキシし、レスポンスをそのままフロントへ返す。【F:frontend/src/app/api/saml/authorization/route.ts†L7-L37】

3. **バックエンドでの AuthnRequest 生成**
   - FastAPI 側の `/auth/saml/authorization` エンドポイントが `SAMLService.generate_authn_request` を呼び出し、OneLogin ライブラリで AuthnRequest を生成。RelayState には `request_id`・`nonce`・戻り先 URI を含み HMAC 署名付きトークンとして返却する。【F:app/api/v1/endpoints/saml_auth.py†L62-L90】【F:app/services/saml_service.py†L129-L172】

4. **IdP での認証 → ACS 受信**
   - HENNGE ONE から POST された `SAMLResponse` と `RelayState` を `/auth/saml/acs` で受領し、RelayState 検証と `process_response(request_id=...)` による Response 検証、属性抽出、ローカルユーザーとの紐付けを行う。【F:app/api/v1/endpoints/saml_auth.py†L102-L146】【F:app/services/saml_service.py†L989-L1059】【F:app/services/saml_service.py†L420-L517】
   - 正常終了時にはログインチケットを生成し、許可済みリダイレクト URI に `saml_ticket` を付加してブラウザを 303 リダイレクトする。【F:app/services/saml_service.py†L1008-L1059】【F:app/api/v1/endpoints/saml_auth.py†L131-L146】【F:app/core/saml_config.py†L204-L235】

5. **フロントエンドでのチケット交換**
   - フロントエンドのコールバックページが `saml_ticket` を読み出し、Next.js API `/api/saml/login` を経由してバックエンドの `/auth/saml/login` を呼び出し、内部アクセストークン／リフレッシュトークンを受領してブラウザ Cookie に保存する。【F:frontend/src/app/auth/saml/callback/page.tsx†L20-L71】【F:frontend/src/app/api/saml/login/route.ts†L7-L72】【F:app/api/v1/endpoints/saml_auth.py†L174-L220】

6. **ログインチケット検証とトークン発行**
   - ログインチケットは RelayState と同じ HMAC キーで署名された短期トークンで、バックエンド側で検証・単回利用制御した上でアクセストークンを発行する。【F:app/services/saml_service.py†L1071-L1130】

7. **証明書管理**
   - IdP 証明書は設定された戦略（メタデータ取得／静的証明書／ハイブリッド）に基づき `SAMLCertificateManager` が管理し、署名検証エラー時には自動再取得を試みる。【F:app/services/saml_certificate_manager.py†L37-L116】【F:app/services/saml_certificate_manager.py†L200-L234】

## セキュリティ評価

### RelayState とリダイレクト制御
- RelayState は HMAC-SHA256 で署名されたトークンで、`request_id` と `return_to` を含み、改ざんや期限切れ検出が可能な実装になっている。【F:app/services/saml_service.py†L145-L172】【F:app/services/saml_service.py†L989-L1019】【F:app/services/saml_service.py†L1136-L1197】
- リダイレクト URI はサーバー側設定で許可リストを管理しており、未許可の URI が指定された場合はデフォルトへフォールバックするため、オープンリダイレクタのリスクは抑制されている。【F:app/core/saml_config.py†L204-L235】

### SAML Response 検証
- OneLogin の `process_response` に `request_id` を渡し、署名エラー時は証明書の再取得を伴うリトライを実装。必須属性（NameID・メール）や許可ドメインの検証も行っているため、典型的な Assertion 受信時の検証ポイントはカバーされている。【F:app/services/saml_service.py†L420-L517】【F:app/services/saml_service.py†L474-L507】
- RelayState の検証で `nonce` と `request_id` の存在チェックを行っており、`process_response` 側では `InResponseTo` を強制している点は、SAML2 のフローに沿った防御になっている。【F:app/services/saml_service.py†L989-L1047】

### ログインチケットとトークン交換
- ログインチケットは短期（デフォルト 120 秒）・署名付きで発行され、バックエンドで単回利用制御が行われている点はセッション固定化防止に有効。ただし現状はプロセス内メモリでの管理のため、スケールアウト時は共有ストレージへの移行が必要になる。【F:app/services/saml_service.py†L1008-L1130】

### 証明書管理
- HENNGE ONE からメタデータを取得できる構成であれば、自動キャッシュと検証失敗時の再取得で証明書ローテーションに追従できる。静的証明書のみを利用する場合も PEM 正規化が行われるため、設定ミス検出の仕組みは用意されている。【F:app/services/saml_certificate_manager.py†L52-L198】

### フロントエンド側の扱い
- RelayState やチケットは `sessionStorage`／HTTP-only Cookie で保持しており、JavaScript からアクセス可能なのは RelayState 情報のみ。RelayState 自体が署名済みであり有効期限も検証しているため、攻撃者による改ざんリスクは低い。【F:frontend/src/hooks/use-saml-login.ts†L53-L63】【F:frontend/src/app/auth/saml/callback/page.tsx†L31-L64】

## 提案事項（改善検討ポイント）と対応状況

> 以下の提案はすべて Phase 1〜4 のセキュリティ改修で対応済みです。

1. **RelayState / AuthnRequest の再利用検知強化** — ✅ **Phase 2 で対応済み**  
   現在は RelayState を署名付きで検証しているものの、`nonce` や `request_id` の使用済み管理は行っていない。短時間内のリプレイ攻撃をより確実に防ぐため、`nonce`／`request_id` をサーバー側ストレージに記録し、再利用を拒否する仕組みの追加を検討したい。【F:app/services/saml_service.py†L145-L172】【F:app/services/saml_service.py†L989-L1059】  
   → **対応内容**: `saml_auth_flow` テーブルで認証フロー全体のライフサイクルを DB 管理。nonce は DB レコードの `nonce` カラムに記録され、チケット交換時に照合。状態遷移（`authn_requested` → `acs_verified` → `ticket_consumed`）により再利用を確実に検知・拒否。

2. **ログインチケット再利用防止の分散対応** — ✅ **Phase 2 で対応済み**  
   `_LOGIN_TICKET_CACHE` はプロセス内メモリのため、複数インスタンス構成では別ノードでチケット再利用が成立する可能性がある。Redis など共有キャッシュに移行する、もしくはデータベースで使用済み管理を行う形へ拡張すると堅牢性が上がる。【F:app/services/saml_service.py†L1111-L1130】  
   → **対応内容**: PostgreSQL の `saml_auth_flow` テーブルに移行。チケット交換時に `SELECT FOR UPDATE` による行ロックで、分散環境（複数ワーカー/インスタンス）でも二重消費を確実に防止。

3. **署名鍵の用途分離** — ✅ **Phase 1 で対応済み**  
   RelayState とログインチケットで同一の HMAC キーを利用している。運用上は十分な長さのランダムキーであれば問題ないが、鍵用途を分離しておくとキー漏洩時の影響範囲を限定できる。設定項目を分けるか、内部的に別キーを派生させる実装を検討しても良い。【F:app/services/saml_service.py†L1136-L1197】  
   → **対応内容**: HKDF（HMAC-based Key Derivation Function）を導入。1つのマスターキー (`SAML_RELAY_STATE_SIGNING_KEY`) から `"relay_state"` 用と `"login_ticket"` 用の2つの独立した鍵を派生。一方が漏洩しても他方には影響しない設計。

4. **AuthnRequest 署名要件の確認** — ✅ **Phase 3 で設定接続強化済み**  
   デフォルト設定では `SAML_SIGN_REQUESTS=False` となっている。HENNGE ONE 側のセキュリティポリシーによっては AuthnRequest 署名が必須となる場合があるため、要件確認と設定値の見直し（署名証明書の配備）を推奨する。【F:app/core/saml_config.py†L64-L118】  
   → **対応内容**: Phase 3 で署名設定と IdP 接続の整合性を強化。`SAML_SIGN_REQUESTS`、`SAML_SIGN_RESPONSES`、`SAML_SIGN_ASSERTIONS` の各設定が正しく OneLogin ライブラリに反映されるよう改修。IdP 要件に応じて `SAML_SIGN_REQUESTS=true` に変更するだけで AuthnRequest 署名が有効化できる状態。

5. **メタデータ運用方針の整理** — ✅ **Phase 3 で対応済み**  
   現在 `validate_required_settings` で静的証明書を必須としているため、メタデータのみでの運用が難しい。HENNGE ONE からの自動更新に完全に依存する場合は、必須項目の見直しや運用ドキュメントでの明示が望ましい。【F:app/core/saml_config.py†L214-L235】【F:app/core/saml_config.py†L312-L340】  
   → **対応内容**: 証明書取得戦略を `auto`（推奨）/ `metadata` / `static` / `hybrid` の4パターンに整理。`auto` 戦略ではメタデータからの動的取得を優先し、静的証明書はフォールバック用として任意。署名検証失敗時には最新証明書を自動取得してリトライする機能を実装。

6. **フロントエンドでの RelayState 有効期限ハンドリング** — ✅ **Phase 4 で対応済み**  
   コールバック画面では `expiresAt` を参照しているが、`sessionStorage` 保存直後に期限切れが近いケースも考慮し、IdP リダイレクト前に十分な猶予があるかクライアント側でもチェックすると UX・安全性双方で安心感が高まる。【F:frontend/src/hooks/use-saml-login.ts†L53-L63】【F:frontend/src/app/auth/saml/callback/page.tsx†L31-L64】  
   → **対応内容**: `use-saml-login.ts` に `expires_at` の残り時間事前チェックを追加（閾値 30 秒未満ならリダイレクト中止）。コールバックページでも `expiresAt` の事後チェックを維持し、二重防御を実現。

以上。
