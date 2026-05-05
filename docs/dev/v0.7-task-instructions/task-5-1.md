# Task 5-1: `components/libkoiki` 移設準備

## 目的

framework code を `components/libkoiki` へ移す前に、`src/` layout 化と path 変更で破断しやすい箇所を洗い出し、移設時の修正対象一覧を確定する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-1-5.md`
- `docs/dev/v0.7-task-instructions/task-2-2.md`
- `docs/dev/v0.7-task-instructions/task-3-4.md`
- `libkoiki/pyproject.toml`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `Dockerfile`

## 事前条件

- [Task 4-5](./task-4-5.md) が完了している

## 確認観点

- `src/` layout 対応方針
- `utils/` など補助サブパッケージの扱い
- import path 変更方針
- CI / Docker / docs / tests の `libkoiki/` 直参照
- 移設時に除外すべき生成物

## 実施手順

1. 現在の `libkoiki/` 配下構造を確認する
2. `src/` 化しても package import 名を `libkoiki` のまま維持できるか確認する
3. `pyproject.toml`、tests、CI、Docker、docs、GitHub instructions から `libkoiki/` 直参照箇所を洗い出す
4. `components/libkoiki/src/libkoiki` へ移す際の修正対象を分類する
5. 移設前に残る未確定点を整理する

## 成果物

- `components/libkoiki` 移設前チェックメモ
- 修正対象一覧

## 検証

- `libkoiki` 側の移設方針に未確定点がない
- Task 5-2 以降で実移設に入れる粒度まで修正対象が分解されている

## 完了条件

- Task 5-2 で `koiki_ref_app` 側の移設準備へ進める

## 実施結果

Task:

- Task 5-1: `components/libkoiki` 移設準備

変更内容:

- 現在の `libkoiki/` 配下を確認し、移設対象と生成物を切り分けた
  - 実コードとして移す対象
    - `api/`
    - `core/`
    - `db/`
    - `events/`
    - `models/`
    - `repositories/`
    - `schemas/`
    - `services/`
    - `tasks/`
    - `utils/`
    - `__init__.py`
  - component 直下に残す候補
    - `pyproject.toml`
    - `README.md`
    - 将来必要なら `AGENTS.md`
  - 移設対象ではなく除外すべき生成物
    - `libkoiki/.venv/`
    - `libkoiki/libkoiki.egg-info/`
    - `__pycache__/`
    - `poetry.lock`
    - 旧 `setup.py` は Stage 1 方針どおり廃止対象
- `src/` layout の基本方針を次のように定義した
  - 目標配置は `components/libkoiki/src/libkoiki/`
  - Python import 名は `libkoiki` のまま維持する
  - したがってアプリコードやテスト内の `from libkoiki...` / `import libkoiki...` は原則大量修正しない
  - 修正の主対象は filesystem path、package discovery、workspace member path
- `utils/` の扱いも整理した
  - `utils/` は framework 補助サブパッケージとして `src/libkoiki/utils/` に同居させる
  - `utils/` を component 直下の別 top-level package にはしない
  - したがって import 名も `libkoiki.utils...` のまま維持する
- packaging / package discovery の破断点も洗い出した
  - `libkoiki/pyproject.toml` の `[tool.poetry] packages = [{include = "*"}]` は `src/` layout では不適切
  - Stage 5 実装時には `src/libkoiki` を前提に package discovery を更新する必要がある
  - root `pyproject.toml` の local dependency path `libkoiki = {path = "libkoiki", develop = true}` は `components/libkoiki` へ更新が必要
  - root `tool.coverage.run.source = ["app", "libkoiki"]` も `components` 化後の整理対象
- CI の破断点も確認した
  - `.github/workflows/ci.yml` は `pytest --cov=libkoiki` を実行している
  - import 名が `libkoiki` のままなら coverage target 名は維持可能
  - ただし install path と workspace member path は `components/libkoiki` に合わせて更新が必要
- Docker / Compose の破断点も確認した
  - `Dockerfile` は `COPY ./libkoiki ./libkoiki` 前提
  - `docker-compose.unified.yml` と `docker-compose.dev.yml` は `./libkoiki:/app/libkoiki:cached` bind mount 前提
  - Stage 6 でまとめて直す方針だが、Task 5-1 でも更新対象として確定した
- docs / scripts / instruction files の直参照も洗い出した
  - `.github/instructions/*.instructions.md` の `applyTo: "libkoiki/**/*.py"` などは `components/libkoiki/src/libkoiki/**/*.py` 前提に更新が必要
  - `docs/saml/SAML_MIGRATION_GUIDE.md` は `libkoiki/` 直下前提で書かれている
  - backend audit 文書には `libkoiki/...` 実 path を埋め込んだ参照がある
  - Stage 5 / 6 で docs の path 記述更新が必要
- tests の観点も整理した
  - `tests/` 配下の多くは `import libkoiki...` 前提なので import 名は維持すべき
  - 一方で `tests/unit/libkoiki/` のようなディレクトリ構成は、将来 `components/libkoiki/tests/` へ移す対象
  - `tests/conftest.py` など root test support は、component move 後にどこへ残すかの見直しが必要
- import path 変更方針も固定した
  - Python package import は `libkoiki` を維持する
  - filesystem path だけを `components/libkoiki/...` に更新する
  - したがって Stage 5 の `libkoiki` 側では、import rename より path / packaging / workspace 更新が主作業になる
- Task 5-1 時点の修正対象一覧を次の4分類で確定した
  - packaging
    - `libkoiki/pyproject.toml`
    - root `pyproject.toml`
  - runtime / build path
    - `Dockerfile`
    - `docker-compose*.yml`
    - `.github/workflows/ci.yml`
  - guidance / docs
    - `.github/instructions/*.instructions.md`
    - `docs/saml/*`
    - `docs/backend-audit/*`
  - tests
    - `tests/unit/libkoiki/`
    - `tests/conftest.py`
    - coverage / import assumptions

未解決事項:

- `libkoiki/AGENTS.md` と `libkoiki/CLAUDE.md` を component 直下に残すか、repo root guidance に統合するかは後続判断が必要
- `tests/conftest.py` を root に残すか、component 単位の fixture へ分割するかは Task 5-4 以降で整理が必要
- `poetry.lock` の扱いは Stage 2 方針上は `uv.lock` へ移行するため、Stage 5 実装時に削除タイミングを決める必要がある

検証結果:

- `libkoiki` の import 名は維持し、主変更点を filesystem path / packaging / workspace に限定する方針で説明できる
- `src/` layout に入る前に更新が必要な packaging、CI、Docker、docs、tests の対象一覧が揃った
- `components/libkoiki` 移設時に除外すべき生成物も明確になった

次タスクへ渡す事項:

- Task 5-2 では `koiki_ref_app` 側の配置を `libkoiki` 側の `src/` 方針と噛み合わせて確定する
- Task 5-3 以降の実移設では、まず生成物を巻き込まないことと package discovery 更新を優先する
- Stage 6 では Docker / Compose / CI / docs の直参照更新をまとめて実施する

## 次タスク

- [Task 5-2](./task-5-2.md)
