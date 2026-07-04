# Task 3-2: Docker / environment migration

## 目的

frontend の Docker、compose、env、README を Vite SPA 構成に合わせる。

## 事前条件

- Task 3-1 が完了している

## 対象

- `frontend/Dockerfile`
- `frontend/Dockerfile.unified`
- `docker-compose.yml`
- `docker-compose.unified.yml`
- `frontend/.env.local.example`
- `frontend/.env.production.example`
- `frontend/.env.docker`
- `frontend/README.md`

## 実施手順

1. production build を `vite build` 前提にする
2. Task 0-2 の same-origin / cross-origin 方針に従って serving 構成を更新する
3. healthcheck を `/api/health` 依存から変更する
4. React Router の deep link / reload に備えて `/index.html` fallback を設定する
5. env mapping 表に従って環境変数を移行する
   - `VITE_*` に残すもの
   - backend setting へ移すもの
   - 削除するもの
6. compose の frontend environment を更新する
7. unified compose の frontend profiles を更新する
8. README を Next.js 初期文面から SPA 実装説明へ更新する

## 検証

- Docker build が成功する
- compose 起動時に frontend healthcheck が通る
- README の起動手順でローカル起動できる
- `/dashboard` などの SPA route を直接開いても `/index.html` fallback により表示できる
- `docker-compose.yml` と `docker-compose.unified.yml` の frontend 設定が矛盾していない

## 完了条件

- ローカルと Docker の frontend 起動方法が Vite SPA と一致している
- env variable の移行先が `VITE_*` / backend setting / removed のいずれかに分類されている

## 実施結果

未実施。
