# Task 1-4: backend auth integration tests

## 目的

Cookie 認証、CSRF、refresh、SSO、SAML の backend behavior を integration test で固定する。

## 事前条件

- Task 1-1 から Task 1-3 が完了している

## 実施手順

1. session password login の Cookie 発行を検証する
2. CSRF bootstrap と Cookie 認証された state-changing request の成功を検証する
3. Cookie 認証された request における invalid CSRF の拒否を検証する
4. Bearer-token client に CSRF を要求しないことを検証する
5. Cookie 認証で current user を解決できることを検証する
6. refresh token rotation と Cookie 更新を検証する
7. refresh 失敗時の Cookie clear を検証する
8. logout 後の `me` 401 を検証する
9. Users API authorization parity を検証する
10. 既存 token-returning login / refresh / SSO / SAML endpoint の互換性を検証する
11. session SSO / SAML exchange の Cookie 発行を検証する
12. SSO / SAML invalid state 系の拒否を検証する
13. session endpoint response body に token value が含まれないことを検証する
14. Cookie jar と CSRF header を扱う test helper を用意する
15. SSO / SAML integration test の mock 方針を決める
    - IdP token endpoint
    - JWKS / ID token verification
    - SAML response / login ticket
    - service boundary stub の利用可否

## 検証

- auth security-sensitive paths に integration coverage がある
- DEBUG 環境変数は repository guidance に従って boolean value を設定して実行する
- Cookie / CSRF test helper により、重複した test setup が増えすぎていない
- SSO / SAML の外部依存 mock 方針が文書化されている
- 既存 Bearer / token-returning contract と新しい Cookie session contract が別々に検証されている

## 完了条件

- Next.js route handler 削除前の backend parity がテストで確認できている
- parity ではなく強化した挙動は、期待仕様として明示された上でテストされている

## 実施結果

未実施。
