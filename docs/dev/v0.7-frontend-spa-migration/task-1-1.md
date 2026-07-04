# Task 1-1: backend Cookie / CSRF primitives

## 目的

FastAPI 側に Cookie 発行、Cookie clearing、CSRF token 発行・検証の共通 primitive を用意する。

## 配置方針

- reusable な Cookie / CSRF helper は `components/libkoiki/`
- reference app 固有の SSO / SAML wiring は `components/koiki_ref_app/`

## 事前条件

- Task 0-2 が完了している

## 実施手順

1. Cookie 設定 helper の既存有無を確認する
2. access token cookie と refresh token cookie の属性を実装する
3. auth cookie clearing helper を実装する
4. CSRF token 発行 helper を実装する
5. Cookie 認証に対応する current-user dependency を設計する
   - `Authorization: Bearer` を維持する
   - Bearer がない場合に access token Cookie を読む
   - 既存 client の互換性を壊さない
6. CSRF 検証 dependency または middleware を実装する
   - Cookie 認証された state-changing request に限定する
   - safe method には要求しない
   - non-browser Bearer-token client には要求しない
7. Cookie 設定の source of truth を backend config に置く
   - cookie name
   - max-age
   - `Secure`
   - `SameSite`
   - `Domain` / host-only
   - `__Host-*` prefix の利用条件
8. token exp と Cookie max-age の整合性を確認する
9. raw token をログ出力しないことを確認する

## 検証

- unit test で Cookie 属性を確認できる
- invalid CSRF が拒否される
- safe method に CSRF を要求しない
- Bearer-token client に CSRF を要求しない
- Cookie 認証で current user を解決できる
- token exp と Cookie max-age の不整合が説明可能である

## 完了条件

- password auth endpoint から再利用できる Cookie / CSRF primitive が揃っている
- Task 1-2 / Task 1-3 が独自に Cookie / CSRF logic を再実装しなくてよい

## 実施結果

未実施。
