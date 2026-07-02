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
5. CSRF 検証 dependency または middleware を実装する
6. raw token をログ出力しないことを確認する

## 検証

- unit test で Cookie 属性を確認できる
- invalid CSRF が拒否される
- safe method に CSRF を要求しない

## 完了条件

- password auth endpoint から再利用できる Cookie / CSRF primitive が揃っている

## 実施結果

未実施。
