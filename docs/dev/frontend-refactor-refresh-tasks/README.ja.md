# Frontend React SPA Refactor / Refresh Tasks

本ディレクトリは、[frontend-refactor-refresh-plan.ja.md](../frontend-refactor-refresh-plan.ja.md) に基づく個別タスク指示書を収録する。

## 進め方

- 原則として番号順に進める
- 各タスク開始時に現状コードを再確認する
- ユーザーまたは別エージェントの未追跡・未コミット変更を上書きしない
- 認証、Cookie、CSRF、SSO、SAML の境界は backend source of truth を維持する
- タスク完了時は各ファイルの `実施結果` セクションへ結果を残す
- 実装判断が計画に影響する場合は、計画書と後続タスクを同じタイミングで更新する

## タスク一覧

1. [Task 0-1: frontend target architecture decision](./task-0-1.md)
2. [Task 0-2: React / TanStack / Router version baseline](./task-0-2.md)
3. [Task 1-1: notification and production log cleanup](./task-1-1.md)
4. [Task 1-2: fetch ApiError and TanStack Query retry alignment](./task-1-2.md)
5. [Task 2-1: API client and feature query split](./task-2-1.md)
6. [Task 2-2: routing and Next.js residue cleanup](./task-2-2.md)
7. [Task 2-3: dashboard and navigation data cleanup](./task-2-3.md)
8. [Task 3-1: ESLint and frontend CI baseline](./task-3-1.md)
9. [Task 3-2: frontend test baseline](./task-3-2.md)
10. [Task 4-1: implementation guide and final validation](./task-4-1.md)

## 推奨進行

- Stage 0 で配置方針、責務境界、主要ライブラリ version baseline を固定する
- Stage 1 でユーザー影響のある不具合と API error 境界を直す
- Stage 2 で feature 分割、routing、Next.js 残骸を整理する
- Stage 3 で lint、test、CI を実効化する
- Stage 4 でガイド化し、後続の業務 UI 実装の入口にする
