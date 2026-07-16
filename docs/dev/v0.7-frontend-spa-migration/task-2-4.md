# Task 2-4: SSO / SAML callback migration

## 目的

SSO と SAML の callback 画面を SPA と backend Cookie endpoint の構成へ移行する。

## 事前条件

- Task 2-2 が完了している
- Task 2-3 の routing が利用可能である

## 対象

- `frontend/src/app/sso/callback/page.tsx`
- `frontend/src/app/auth/saml/callback/page.tsx`
- `frontend/src/lib/sso-storage.ts`
- `frontend/src/lib/saml-storage.ts`
- `frontend/src/lib/pkce.ts`

## 実施手順

1. SSO callback を React Router route component に移す
2. URL query parsing を browser API / React Router 前提に置き換える
3. SSO state / nonce / PKCE verifier 検証を維持する
4. SSO login exchange を backend Cookie endpoint に向ける
5. SAML callback を React Router route component に移す
6. SAML RelayState と expiry 検証を維持する
7. SAML login exchange を backend Cookie endpoint に向ける
8. 成功時は `/dashboard` へ遷移し、失敗時は復旧可能な error view を出す

## 検証

- SSO callback happy path
- SSO state mismatch
- SAML callback happy path
- SAML RelayState mismatch / expired state

## 完了条件

- SSO / SAML callback が Next.js page に依存していない

## 実施結果

実施済み。

- Task 2-3 で SSO / SAML callback page を React Router route component として登録済みであることを確認した。
- URL query parsing が React Router の `useSearchParams` に置き換わっていることを確認した。
- SSO state / nonce / PKCE verifier 検証を維持していることを確認した。
- SSO login exchange が `cookieApiClient.sso.login()` 経由で backend Cookie endpoint に向いていることを確認した。
- SAML RelayState / expiry 検証を維持していることを確認した。
- SAML login exchange が `cookieApiClient.saml.login()` 経由で backend Cookie endpoint に向いていることを確認した。
- 成功時は React Router の `navigate(..., { replace: true })` で `/dashboard` または backend response の `location` に遷移する。
- 失敗時は login / home へ戻れる error view を表示する。
- React `StrictMode` の dev 二重 effect で callback exchange が二重送信されないよう、SSO / SAML callback に finalize guard を追加した。

検証:

- `npm run check-types`
- `npm run build`
- Vite dev server callback route HTTP 200:
  - `/sso/callback`
  - `/sso/callback?code=dummy&state=wrong`
  - `/auth/saml/callback`
  - `/auth/saml/callback?saml_ticket=dummy&RelayState=wrong`
- `rg "next/link|next/navigation|useRouter|usePathname" frontend/src/app/sso/callback/page.tsx frontend/src/app/auth/saml/callback/page.tsx frontend/src/hooks/use-sso-login.ts frontend/src/hooks/use-saml-login.ts frontend/src/lib/sso-storage.ts frontend/src/lib/saml-storage.ts frontend/src/lib/pkce.ts`
- `rg "/api/sso|/api/saml|/api/auth|access_token|refresh_token" frontend/src/app/sso/callback/page.tsx frontend/src/app/auth/saml/callback/page.tsx frontend/src/hooks/use-sso-login.ts frontend/src/hooks/use-saml-login.ts frontend/src/lib/sso-storage.ts frontend/src/lib/saml-storage.ts frontend/src/lib/pkce.ts`

補足:

- 実 IdP を使う happy path / mismatch / expired state の end-to-end 確認は、SSO / SAML provider 設定と backend 稼働状態が必要なため未実施。
- 今回は callback route 実装、backend Cookie endpoint への接続、state 検証維持、error view 到達性を確認した。
