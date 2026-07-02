# Task 0-2: backend 認証 contract 設計

## 目的

SPA が依存する backend auth API contract を定義し、Next.js route handler の責務を FastAPI 側へ移す前提を固める。

## 参照ファイル

- `components/libkoiki/src/libkoiki/api/v1/endpoints/auth*.py`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/saml_auth.py`
- `components/libkoiki/src/libkoiki/services/auth_service.py`
- `components/koiki_ref_app/src/koiki_ref_app/services/sso_service.py`
- `components/koiki_ref_app/src/koiki_ref_app/services/saml_service.py`

## 事前条件

- Task 0-1 が完了している

## Contract 候補

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/csrf`
- `GET /api/v1/auth/sso/authorization`
- `POST /api/v1/auth/sso/login`
- `GET /api/v1/auth/saml/authorization`
- `POST /api/v1/auth/saml/login`

## 実施手順

1. 既存 backend endpoint の request / response を確認する
2. Cookie 発行が必要な endpoint を決める
3. CSRF が必要な endpoint を決める
4. refresh token rotation と logout 失効の仕様を確認する
5. SSO / SAML callback URL の互換要件を確認する
6. frontend から見た API contract を文書化する

## 推奨成果物

- endpoint contract 表
- Cookie 名、属性、max-age の定義
- CSRF token 取得・送信方式
- CORS / same-origin 方針

## 検証

- SPA が token value を扱わずに動作できる contract になっている
- state-changing request の CSRF 要件が明確である

## 完了条件

- Task 1-1 以降で実装する backend 変更範囲が確定している

## 実施結果

未実施。
