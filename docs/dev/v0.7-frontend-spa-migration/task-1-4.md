# Task 1-4: backend auth integration tests

## 目的

Cookie 認証、CSRF、refresh、SSO、SAML の backend behavior を integration test で固定する。

## 事前条件

- Task 1-1 から Task 1-3 が完了している

## 実施手順

1. password login の Cookie 発行を検証する
2. CSRF bootstrap と state-changing request の成功を検証する
3. invalid CSRF の拒否を検証する
4. refresh token rotation と Cookie 更新を検証する
5. refresh 失敗時の Cookie clear を検証する
6. logout 後の `me` 401 を検証する
7. SSO / SAML exchange の Cookie 発行を検証する
8. SSO / SAML invalid state 系の拒否を検証する

## 検証

- auth security-sensitive paths に integration coverage がある
- DEBUG 環境変数は repository guidance に従って boolean value を設定して実行する

## 完了条件

- Next.js route handler 削除前の backend parity がテストで確認できている

## 実施結果

未実施。
