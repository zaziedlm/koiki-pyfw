# Task 2-1: Vite React scaffold

## 目的

`frontend/` を Vite + React + TypeScript の SPA として起動できる状態にする。

## 事前条件

- Task 1-4 により backend auth parity が確認されている

## 実施手順

1. `vite` と `@vitejs/plugin-react` を導入する
2. `index.html` と `src/main.tsx` を追加する
3. `src/app/layout.tsx` 相当の provider composition を `main.tsx` 側へ移す
4. Tailwind / PostCSS 設定を Vite で動作する形に調整する
5. path alias `@/*` を Vite / TypeScript の両方で維持する
6. `npm run dev`, `npm run build`, `npm run check-types` を Vite 前提に更新する

## 検証

- `npm run check-types`
- `npm run build`
- Vite dev server で blank page にならない

## 完了条件

- 最小 SPA が Vite で表示できる

## 実施結果

実施済み。

- `frontend/` を Vite + React + TypeScript で起動できる構成に切り替えた。
- `vite` と `@vitejs/plugin-react` を追加した。
- `index.html`, `src/main.tsx`, `src/App.tsx`, `vite.config.ts`, `src/vite-env.d.ts` を追加した。
- `src/app/layout.tsx` の provider composition から、Vite entry 側へ以下を移した。
  - `ReactQueryProvider`
  - `Toaster`
  - `globals.css`
- path alias `@/*` を Vite config / TypeScript の両方で維持した。
- Tailwind v4 の PostCSS plugin を Vite で読み込める形式に調整した。
- `frontend` の scripts を Vite 前提へ更新した。
  - `npm run dev`
  - `npm run build`
  - `npm run preview`
  - `npm run check-types`
- Vite が production mode を自動設定するため、production / docker env file から `NODE_ENV=production` を外した。

検証:

```text
npm run check-types
```

結果:

```text
passed
```

```text
npm run build
```

結果:

```text
vite build passed
```

補足:

- `vite build` は成功したが、初期 scaffold 時点では既存 UI 依存をまとめて読むため chunk size warning が出る。後続の route migration / code splitting で再確認する。
- Vite dev server は `NODE_ENV=development npm run dev` で起動し、`http://127.0.0.1:3000` が `200` を返すことを確認した。
- in-app browser はこの環境で利用できなかったため、ブラウザ画面のスクリーンショット確認は未実施。
