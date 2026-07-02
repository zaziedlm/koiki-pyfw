# Task 4-1: final validation / release notes

## 目的

Frontend SPA migration の完了判定を行い、残課題とリリース時の注意点を文書化する。

## 事前条件

- Task 3-2 が完了している

## 実施手順

1. backend auth integration tests を実行する
2. frontend typecheck を実行する
3. frontend production build を実行する
4. Docker または local dev で login -> Todo CRUD -> logout を確認する
5. SSO happy path を確認する
6. SAML happy path を確認する
7. docs と README の古い Next.js 記述を検索する
8. release notes に breaking changes と migration notes をまとめる

## 検証

- auth Cookie が JS から読めない
- state-changing request は CSRF なしで失敗する
- token refresh 後も authenticated state が維持される
- logout 後に protected route へ戻れない

## 完了条件

- 移行結果、検証結果、残課題が文書化されている
- frontend は Next.js なしで起動・build・運用できる

## 実施結果

未実施。
