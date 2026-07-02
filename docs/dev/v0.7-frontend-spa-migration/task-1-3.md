# Task 1-3: SSO / SAML Cookie endpoints

## 目的

SSO と SAML の login exchange 後に FastAPI が直接 auth Cookie を発行できるようにする。

## 事前条件

- Task 1-1 が完了している
- Task 1-1 の Cookie 発行 helper が利用可能である

## 対象

- SSO authorization init
- SSO authorization code exchange
- SAML authorization init
- SAML login ticket exchange

## 実施手順

1. SSO authorization init の response contract を SPA 向けに確認する
2. SSO login exchange 成功時に access / refresh Cookie を発行する
3. SAML authorization init の response contract を SPA 向けに確認する
4. SAML login ticket exchange 成功時に access / refresh Cookie を発行する
5. Origin / CSRF / state / nonce / RelayState / ticket expiry の検証責務を確認する
6. backend security logging が raw token や raw assertion を出さないことを確認する

## 検証

- SSO exchange 成功時に Cookie が発行される
- SAML exchange 成功時に Cookie が発行される
- invalid state / RelayState / ticket は拒否される
- frontend は token value を受け取らなくても dashboard へ遷移できる

## 完了条件

- SSO / SAML flow が Next.js route handler なしで成立する

## 実施結果

未実施。
