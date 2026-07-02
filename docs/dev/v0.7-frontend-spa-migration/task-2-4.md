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

未実施。
