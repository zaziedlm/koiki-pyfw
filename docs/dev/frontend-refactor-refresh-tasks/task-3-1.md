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
- `.github/workflows/frontend-ci.dev-v0.8.yml.disabled`

## 実施手順

1. ESLint flat config に TypeScript、React Hooks、React Refresh の実効ルールを追加する
2. 必要に応じて jsx-a11y 系ルールの導入可否を判断する
3. `npm run lint` が意味のある違反を検出できることを確認する
4. dev/v0.8 で有効化する frontend CI 定義を作る
5. frontend CI 定義で `npm ci`, `npm run check-types`, `npm run lint`, `npm run build` を実行する
6. node version と npm cache 方針を明示する

## 検証

- `npm ci`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- GitHub Actions workflow syntax が妥当である

## 完了条件

- `npm run lint` が ignore だけの実行ではなくなる
- dev/v0.8 で有効化する frontend CI 定義が用意されている
- 既存ブランチ向け Actions が意図せず発火しない

## 実施結果

完了。

- `frontend/eslint.config.mjs` を ignore のみの設定から、`@eslint/js` recommended、`typescript-eslint` recommended、React Hooks、React Refresh の flat config に更新した。
- `@typescript-eslint/no-unused-vars` は `_` prefix の意図的な未使用を許容する設定にした。
- jsx-a11y は今回は導入しない判断にした。現時点の主目的は TypeScript / Hooks / Refresh の実効化であり、アクセシビリティルール導入は既存 UI 全体への影響が大きいため、必要なら別タスクで扱う。
- frontend devDependencies に ESLint 実効化用の `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals` を追加した。
- React SPA 版以降の `dev/v0.8` 向け frontend CI 定義を `.github/workflows/frontend-ci.dev-v0.8.yml.disabled` として追加した。
- `.yml.disabled` は GitHub Actions の workflow 対象外なので、現時点では Actions を発火させない。
- frontend CI 定義は Node.js `22`、npm cache `frontend/package-lock.json`、`npm ci`, `npm run check-types`, `npm run lint`, `npm run build` を実行する内容にした。
- 既存 `.github/workflows/ci.yml` は変更しない方針に戻した。

検証:

- `npm ci`
- `npm run check-types`
- `npm run lint`
- `npm run build`
- `git diff --check`

補足:

- sandbox 通常権限の `npm ci` と `npm run build` は `spawn EPERM` で失敗したため、昇格実行で成功を確認した。
- `npm run lint` は exit code 0。既存 UI helper export に対する `react-refresh/only-export-components` warning が 3 件残っている。
- `npm ci` 後の npm audit は 7 vulnerabilities を報告したが、依存 audit 対応は本タスク外とした。
- workflow syntax は YAML parser / actionlint がローカルで利用できなかったため、構造の目視確認と `git diff --check` まで実施した。
- frontend CI を有効化するタイミングで、`.github/workflows/frontend-ci.dev-v0.8.yml.disabled` を `.yml` へ rename する。
