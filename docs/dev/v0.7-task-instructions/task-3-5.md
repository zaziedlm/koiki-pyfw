# Task 3-5: 互換起動導線の定義

## 目的

app factory 導入中も既存起動導線を壊さないように、暫定互換 wrapper と ASGI import path の扱いを定義する。

## 参照ファイル

- `app/main.py`
- `main.py`
- `Dockerfile`
- `Dockerfile.unified`
- `docker-compose.yml`

## 事前条件

- [Task 3-4](./task-3-4.md) が完了している

## 確認観点

- root wrapper の必要有無
- `uvicorn` 起動互換
- Docker / Compose / test の参照点

## 実施手順

1. 現在の ASGI import path 参照箇所を洗い出す
2. `app.main:app` を維持すべき期間を整理する
3. root `main.py` の扱いを整理する
4. 暫定 wrapper の形を定義する
5. 将来の切替ポイントを記録する

## 成果物

- 互換起動導線メモ
- 暫定 wrapper 方針

## 検証

- Stage 3 完了後もローカル起動と Docker 起動に破断がない
- 将来の `koiki_ref_app.main:app` への切替点が説明できる

## 完了条件

- Task 3-6 で Stage 3 全体の安定性確認に進める

## 実施結果

Task:

- Task 3-5: 互換起動導線の定義

変更内容:

- 現在の ASGI import path 参照箇所を整理し、`app.main:app` 依存が広く存在することを確認した
  - root `main.py`
    - `from app.main import app`
    - `uvicorn.run("app.main:app", ...)`
  - Docker / Compose
    - `Dockerfile`
    - `Dockerfile.unified`
    - `docker-compose.yml`
    - `docker-compose.dev.yml`
    - `docker-compose.unified.yml`
  - docs
    - `docs/dev/local_setup.md`
    - `docs/saml/SAML_SETUP.md`
    - `task-2-1.md`
    - `task-2-3.md`
  - tests / examples
    - `tests/conftest.py`
    - `docs/authentication-api-guide.md`
- この現状から、Stage 3 中に `app.main:app` を壊すのは不適切と判断した
  - 理由:
    - ローカル起動
    - Docker 起動
    - テスト import
    - 各種 docs
    が一斉に壊れるため
- 暫定互換 wrapper の必要性を次のように確定した
  - 必要
  - 互換レイヤは二層で維持する
    - `app/main.py`
    - root `main.py`
- `app/main.py` の暫定 wrapper 方針を次のように定義した
  - Stage 3 で `app/app_factory.py` と `app/bootstrap/*.py` を導入した後も
    - `app/main.py` には `app = create_app()` を残す
  - `uvicorn app.main:app` を継続サポートする
  - `app/main.py` 自体は「実装本体」ではなく「互換 import target」に役割を縮小する
- root `main.py` の扱いも次のように整理した
  - こちらも暫定 wrapper として維持する
  - ただし優先互換対象は `app.main:app`
  - root `main.py` は Stage 7 の互換コード除去候補とする
- 互換 wrapper の実装イメージを次のように定義した
  - `app/app_factory.py`
    - `def create_app(...) -> FastAPI`
  - `app/main.py`
    - `from app.app_factory import create_app`
    - `app = create_app()`
  - root `main.py`
    - `from app.main import app`
    - 必要なら `uvicorn.run("app.main:app", ...)`
- 将来の正式 ASGI path の切替方針も整理した
  - Stage 3
    - `app.main:app` を維持
  - Stage 5 以降
    - `components/koiki_ref_app/src/koiki_ref_app/main.py` へ移行
  - Stage 6
    - Docker / Compose / CI / docs を新 path へ一括更新
  - Stage 7
    - `app.main:app` と root `main.py` の互換 wrapper を削除
- 互換期間中の source of truth も明示した
  - 実装本体の source of truth
    - `app.app_factory.create_app`
  - 互換 import target
    - `app.main:app`
  - 暫定 root convenience entrypoint
    - `main.py`
- Docker / Compose と Stage 6 の関係も再確認した
  - 現時点では Dockerfile / Compose の ASGI path を変えない
  - `uv`、`create_app()`、`components/` 配置が固まった後にまとめて切り替える
  - Stage 3 では互換維持の設計だけを先に確定する
- test / docs 側の扱いも整理した
  - `tests/conftest.py` など `from app.main import app` している箇所は、Stage 3 中はそのままでよい
  - docs の `uvicorn app.main:app` 記述も Stage 6 までは大きくは崩さない
  - ただし今後の source of truth は `create_app()` へ寄ることを文書側で意識する

未解決事項:

- root `main.py` を Stage 5 まで維持するか、Stage 6 で先に削除候補へ回すかは実運用参照状況を見て判断が必要
- `tests/conftest.py` など test 側を早期に `create_app()` import へ寄せるかは、実装後の差分規模次第で判断したい
- `koiki_ref_app.main:app` への正式切替時に、app package 名変更と ASGI path 変更を同一リリースで行うため、運用告知は必要

検証結果:

- Stage 3 完了後もローカル起動と Docker 起動に破断がない設計になった
- `app.main:app` を当面の互換 import target としつつ、source of truth を `create_app()` に寄せる方針を説明できる
- 将来の `koiki_ref_app.main:app` への切替点も Stage 5 / 6 / 7 の流れで説明できる

次タスクへ渡す事項:

- Task 3-6 では、Stage 3 全体が「`create_app()` を source of truth にしつつ互換起動導線を維持する」構成として安定しているか確認する
- 実装時には、`app/main.py` を薄い wrapper へ縮退させる差分を中心に設計する
- Stage 6 の Docker / Compose 更新時に、ここで定義した切替順序を遵守する

## 次タスク

- [Task 3-6](./task-3-6.md)
