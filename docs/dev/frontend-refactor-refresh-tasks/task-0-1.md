# Task 0-1: frontend target architecture decision

## 目的

刷新作業に入る前に、`frontend/` の配置方針、責務境界、採用する React Router mode、server state / client state の線引きを固定する。

## 事前条件

- `docs/dev/frontend-implementation-review-findings.ja.md` を確認している
- `docs/dev/frontend-implementation-review-findings-codex.ja.md` を確認している
- `docs/dev/frontend-refactor-refresh-plan.ja.md` を確認している

## 対象

- `frontend/src/`
- `frontend/README.md`
- 必要に応じて `docs/agent/app.md` または frontend 関連 guide

## 実施手順

1. 現在の `src/app`, `src/components`, `src/hooks`, `src/lib`, `src/stores`, `src/types` の責務を棚卸しする
2. 目標構成を次の単位で決める
   - `src/routes`
   - `src/shared/api`
   - `src/shared/ui`
   - `src/shared/config`
   - `src/features/<feature>`
   - `src/stores`
3. React Router は当面 Library Mode / Declarative Mode を継続するか、Data Router へ移行するかを判断する
4. TanStack Query と React Router loader/action の責務重複を避けるルールを明文化する
5. Zustand に保持してよい state と保持してはいけない state を明文化する
6. 後続タスクでファイル移動する順序を更新する

## 検証

- 目標構成が `frontend-refactor-refresh-plan.ja.md` と矛盾していない
- auth / csrf / sso / saml の backend ownership が崩れていない
- 後続タスクの作業順序が実装可能である

## 完了条件

- frontend の配置方針が文書化されている
- 後続タスクが参照できる責務境界がある
- 既存コードをどの順序で移動・分割するかが明確である

## 実施結果

完了。

- `docs/dev/frontend-target-architecture.ja.md` を追加し、現行 `frontend/src/` の棚卸し、目標構成、Router 方針、TanStack Query / Router 境界、Zustand 境界、API 境界、移行順序、維持する認証境界を文書化した。
- 当面の React Router 方針は Declarative / Library Mode 継続とした。Data Router は route-level pending / error / redirect などの明確な価値が出るまで導入しない。
- TanStack Query は server state の主責務、Router は navigation / layout / route matching の主責務と定義した。
- Zustand は UI preference と client-only transient state に限定し、token、user profile、roles、task list、dashboard stats などの API 由来 state は保持しない方針を明記した。
- 後続の移行順序は Task 0-2、1-1、1-2、2-1、2-2、2-3、3-1、3-2、4-1 の順とし、Task 2-1 と Task 2-2 は import 移動の競合に注意することを明記した。
