# Task 3-1: ESLint and frontend CI baseline

## 目的

frontend の lint と CI を実効化し、型・lint・build が PR 上で継続的に検証される状態にする。

## 事前条件

- Task 1-2 が完了していることが望ましい
- Task 2-2 が完了していることが望ましい

## 対象

- `frontend/eslint.config.mjs`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.github/workflows/ci.yml`

## 実施手順

1. ESLint flat config に TypeScript、React Hooks、React Refresh の実効ルールを追加する
2. 必要に応じて jsx-a11y 系ルールの導入可否を判断する
3. `npm run lint` が意味のある違反を検出できることを確認する
4. CI に frontend job を追加する
5. CI frontend job で `npm ci`, `npm run check-types`, `npm run lint`, `npm run build` を実行する
6. node version と npm cache 方針を明示する

## 検証

- `npm ci`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- GitHub Actions workflow syntax が妥当である

## 完了条件

- `npm run lint` が ignore だけの実行ではなくなる
- frontend の型・lint・build が CI に入っている
- CI の backend job と frontend job の責務が明確である

## 実施結果

未実施。

