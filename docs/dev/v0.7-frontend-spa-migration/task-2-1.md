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

未実施。
