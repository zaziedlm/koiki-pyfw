# KOIKI-FW v0.7 Frontend SPA Migration Tasks

本ディレクトリは、[frontend-spa-migration-plan.ja.md](../frontend-spa-migration-plan.ja.md)
に基づく個別タスク指示書を収録するものです。

## 使い方

- 原則として番号順に進める
- backend 認証 parity が揃うまで Next.js route handler は削除しない
- 認証、Cookie、CSRF、SSO、SAML の変更では backend integration test を優先する
- 前提が崩れた場合は、後続タスクへ進まず計画書とタスク指示書を更新する
- タスク完了時は各ファイルの `実施結果` セクションに結果を残す

## タスク一覧

1. [Task 0-1: frontend 責務棚卸し](./task-0-1.md)
2. [Task 0-2: backend 認証 contract 設計](./task-0-2.md)
3. [Task 1-1: backend Cookie / CSRF primitives](./task-1-1.md)
4. [Task 1-2: password auth Cookie endpoints](./task-1-2.md)
5. [Task 1-3: SSO / SAML Cookie endpoints](./task-1-3.md)
6. [Task 1-4: backend auth integration tests](./task-1-4.md)
7. [Task 2-1: Vite React scaffold](./task-2-1.md)
8. [Task 2-2: SPA API client / auth hooks](./task-2-2.md)
9. [Task 2-3: route / page migration](./task-2-3.md)
10. [Task 2-4: SSO / SAML callback migration](./task-2-4.md)
11. [Task 3-1: Next.js server surface removal](./task-3-1.md)
12. [Task 3-2: Docker / environment migration](./task-3-2.md)
13. [Task 4-1: final validation / release notes](./task-4-1.md)

## 推奨進行

- Stage 0 で現状と contract を固定する
- Stage 1 で FastAPI 側に security-sensitive behavior を移す
- Stage 2 で SPA 化する
- Stage 3 で Next.js 依存を削除する
- Stage 4 で統合検証と引き渡し文書を整える
