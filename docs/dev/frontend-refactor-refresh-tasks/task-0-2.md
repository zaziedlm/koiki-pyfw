# Task 0-2: React / TanStack / Router version baseline

## 目的

刷新作業の前提となる React、TanStack Query、React Router の version baseline を固定し、React Router v8 採用可否を実装前に判断する。

## 事前条件

- Task 0-1 が完了していることが望ましい

## 対象

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/**/*.tsx`
- `docs/dev/frontend-refactor-refresh-plan.ja.md`

## 現時点の確認事項

2026-07-09 時点の npm metadata では次を確認済み。

- `react` latest: `19.2.7`
- `react-router` latest: `8.2.0`
- `react-router-dom` latest: `7.18.1`
- `react-router@8.2.0` peer dependency: `react >=19.2.7`, `react-dom >=19.2.7`

現行 `frontend/package.json` は `react` / `react-dom` が `19.1.0`、`react-router-dom` が `^7.18.1` である。

## 実施手順

1. `npm view react version dist-tags --json` で React latest を再確認する
2. `npm view react-dom version dist-tags --json` で React DOM latest を再確認する
3. `npm view @tanstack/react-query version dist-tags --json` で TanStack Query v5 latest を再確認する
4. `npm view react-router version dist-tags peerDependencies exports --json` で React Router v8 の要件を再確認する
5. `npm view react-router-dom version dist-tags --json` で `react-router-dom` の v8 availability を再確認する
6. React / React DOM を `19.2.7` 以上へ更新する
7. React Router v8 を採用する場合は、`react-router-dom` 依存を維持するか、`react-router` / `react-router/dom` import へ移すかを公式 docs と package exports で確認する
8. v8 採用が時期尚早と判断した場合は、`react-router-dom@7.18.1` を当面の固定 baseline とし、Task 2-2 では v7 上で route 構成を整理する
9. 採用・保留の理由を `frontend-refactor-refresh-plan.ja.md` と本タスクの `実施結果` に記録する

## 判断基準

React Router v8 を採用する条件:

- React / React DOM の peer dependency を満たせる
- Vite build と TypeScript が問題なく通る
- `BrowserRouter`, `Routes`, `Route`, `Navigate`, `Link`, `useNavigate`, `useLocation` の import 移行方針が明確である
- React Router DOM integration の package story が公式情報で確認できる
- route-level lazy loading / layout route 整理と同じ change window で実施しても過度なリスクにならない

React Router v8 を保留する条件:

- `react-router-dom` v8 が未提供で、DOM integration の移行パスが不明瞭である
- v8 移行が API client / test / CI 基盤整備より大きな不確実性を持つ
- 公式 migration guide または安定した adoption guidance が確認できない

## 検証

- `npm install`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- login / protected route / dashboard / tasks route の手動確認

## 完了条件

- React / React DOM / TanStack Query / React Router の baseline が明確である
- React Router v8 を採用するか、v7 最新系に留めるかの判断が記録されている
- 後続の Task 2-2 が前提にする router version が確定している

## 実施結果

完了。

2026-07-09 に npm metadata を再確認した。

- `react` latest: `19.2.7`
- `react-dom` latest: `19.2.7`
- `@tanstack/react-query` latest: `5.101.2`
- `react-router` latest: `8.2.0`
- `react-router-dom` latest: `7.18.1`
- `react-router@8.2.0` peer dependency: `react >=19.2.7`, `react-dom >=19.2.7`
- `react-router@8.2.0` engine: `node >=22.22.0`

更新した baseline:

- `react`: `^19.2.7`
- `react-dom`: `^19.2.7`
- `@tanstack/react-query`: `^5.101.2`
- `@tanstack/react-query-devtools`: `^5.101.2`
- `react-router-dom`: `^7.18.1`

React Router v8 は保留した。

- Context7 で React Router 公式 docs / changelog 相当の情報を確認し、v8 では `react-router-dom` re-export package がなくなり、`react-router` / `react-router/dom` import へ移行する必要があることを確認した。
- 一度 `react-router@8.2.0` を試したが、npm が `EBADENGINE` を警告した。現行 Node は `22.20.0`、`react-router@8.2.0` の要求は `>=22.22.0` である。
- CI の frontend Node baseline は Task 3-1 でこれから定義する段階であるため、Task 0-2 では v8 採用を時期尚早と判断し、Task 2-2 は `react-router-dom@7.18.1` を前提に進める。

検証結果:

- `npm run check-types`: 成功
- `npm run lint`: 成功。ただし Task 3-1 前なので ESLint は実効ルール未整備
- `npm run build`: sandbox では esbuild spawn が `EPERM`。通常権限で再実行して成功
- build warning: initial JS chunk が 611.58 kB で 500 kB を超過。Task 2-2 の route-level lazy loading で扱う
