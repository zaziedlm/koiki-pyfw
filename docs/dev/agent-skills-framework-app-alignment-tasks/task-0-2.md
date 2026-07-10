# Task 0-2: Backend API / frontend contract impact map

## 目的

業務アプリ開発で判断が必要な backend API 契約と frontend contract を整理し、Skill に必要な guidance を定義する。

## 事前条件

- Task 0-1 が完了している。

## 対象

- `docs/agent/boundaries.md`、`architecture.md`、`auth-security.md`、`testing.md`
- `components/libkoiki/` と `components/koiki_ref_app/` の現行 router、endpoint、schema、dependency
- `frontend/` と `docs/frontend-spa-implementation-guide.ja.md`
- `docs/authentication-api-guide.md`

## 実施手順

1. backend API を framework、reference app、business app の ownership に分類する。
2. API 変更時に確認すべき schema、auth/RBAC、Cookie/CSRF、SSO/SAML、config、migration、test を整理する。
3. frontend contract として、endpoint schema、error、Cookie session、CSRF、authorization、query invalidation、frontend test を整理する。
4. Vite + React SPA 固有の推奨事項と、将来の別 frontend 技術にも共通する契約を分離する。
5. 代表シナリオ（業務 API 追加、session auth 変更、SSO/SAML、SPA API 利用、frontend-only 改修）を作り、必要な Skill routing を記録する。

## 完了条件

- Skill に載せるべき backend API / frontend contract の要点が記録されている。
- backend の配置判断と frontend の利用判断が混同されていない。
- 代表シナリオごとの期待 Skill が決まっている。

## 実施結果

未実施。
