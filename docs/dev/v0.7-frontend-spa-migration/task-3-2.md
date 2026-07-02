# Task 3-2: Docker / environment migration

## 目的

frontend の Docker、compose、env、README を Vite SPA 構成に合わせる。

## 事前条件

- Task 3-1 が完了している

## 対象

- `frontend/Dockerfile`
- `frontend/Dockerfile.unified`
- `docker-compose.yml`
- `frontend/.env.local.example`
- `frontend/.env.production.example`
- `frontend/.env.docker`
- `frontend/README.md`

## 実施手順

1. production build を `vite build` 前提にする
2. production serving を静的配信にするか backend 同一配信にするか決める
3. healthcheck を `/api/health` 依存から変更する
4. `NEXT_PUBLIC_*` env を `VITE_*` に置き換える
5. compose の frontend environment を更新する
6. README を Next.js 初期文面から SPA 実装説明へ更新する

## 検証

- Docker build が成功する
- compose 起動時に frontend healthcheck が通る
- README の起動手順でローカル起動できる

## 完了条件

- ローカルと Docker の frontend 起動方法が Vite SPA と一致している

## 実施結果

未実施。
