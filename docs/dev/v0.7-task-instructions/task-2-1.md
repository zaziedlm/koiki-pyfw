# Task 2-1: uv 導入ポリシーの定義

## 目的

Poetry から `uv` へ何を置き換えるかを先に明文化し、移行中の判断ぶれを防ぐ。

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)

## 事前条件

- [Task 1-6](./task-1-6.md) が完了している

## 決める内容

- `uv sync` を標準セットアップコマンドにするか
- `uv run` を標準実行コマンドにするか
- `uv.lock` を正規 lockfile にするか
- root workspace と member 管理をどう扱うか

## 実施手順

1. 現在 Poetry が担っている役割を列挙する
2. それぞれを `uv` でどう置き換えるか定義する
3. ローカル開発、CI、将来の `components/` 移動への影響を確認する
4. 「何を `uv` に置換し、何を置換しないか」を文章化する
5. 標準コマンド一覧を作る

## 成果物

- `uv` 導入ポリシーメモ
- 標準コマンド一覧

## 検証

- Poetry と `uv` の責務差分が説明できる
- チームが使う標準コマンドを 1 セットで示せる

## 完了条件

- Task 2-2 以降がこの方針で判断できる

## 実施結果

Task:

- Task 2-1: `uv` 導入ポリシーの定義

変更内容:

- 現在 Poetry が担っている役割を、repo 内の利用箇所と運用文書から次のように整理した
  - lockfile 管理
    - `poetry.lock`
  - 仮想環境への dependency install
    - `poetry install`
  - コマンド実行
    - `poetry run ...`
  - package build
    - `poetry build`
  - dependency group 管理
    - `[tool.poetry.group.*]`
  - root を package ではなく workspace 的に扱う制御
    - `tool.poetry.package-mode = false`
  - Docker / local setup / 各種ガイドに埋め込まれた Poetry 前提コマンド
- `uv` 公式ドキュメントを確認し、採用する置換先を次のように定義した
  - `poetry install` → `uv sync`
  - `poetry run ...` → `uv run ...`
  - `poetry.lock` → `uv.lock`
  - `[tool.poetry.group.*]` → `[dependency-groups]`
  - local path / workspace member 管理 → `[tool.uv.sources]`
  - workspace member 定義 → `[tool.uv.workspace]`
- 置換ポリシーを次のように確定した
  - `uv sync` を標準セットアップコマンドにする
  - `uv run` を標準実行コマンドにする
  - `uv.lock` を正規 lockfile にする
  - Stage 2 では Poetry と `poetry.lock` を移行対象として扱い、最終的にチーム標準から外す
  - root `pyproject.toml` は workspace ルートとして残し、将来の `components/` 配置時に `tool.uv.workspace.members` を追加する
  - `libkoiki` と将来の `koiki_ref_app` の依存関係は、workspace member 化後は `tool.uv.sources.<name> = { workspace = true }` を使う
- 「何を `uv` に置換し、何を置換しないか」を次のように整理した
  - 置換するもの
    - dependency install / sync
    - command execution
    - lockfile
    - dependency group 宣言
    - local component 間参照の開発用 source 定義
  - すぐには置換しないもの
    - build backend そのもの
      - Stage 2 では `poetry-core` / `setuptools` の build backend を直ちに `uv_build` へ変えない
      - まず dependency manager を `uv` へ切り替え、build backend 再設計は後続段階で判断する
    - package metadata の基本表現
      - 依存定義は引き続き `pyproject.toml` の標準テーブルを使う
      - `uv` 固有設定は `tool.uv.*` に限定する
    - `uv pip` ベースの互換運用
      - 本プロジェクトでは `uv pip` を標準 workflow にしない
      - 例外的な互換用途が必要な場合だけ補助的に使う
- root workspace と member 管理の方針も整理した
  - Stage 2 開始時点では、現構成の root を `uv` 管理 project として扱う
  - `components/` へ移行した段階で、root は workspace root として次を持つ
    - `[tool.uv.workspace]`
    - `members = ["components/libkoiki", "components/koiki_ref_app"]`
  - `apps/` は案件固有資産であり、全案件を root workspace member に固定する前提では扱わない
  - `frontend/` は Python workspace member ではないため、`tool.uv.workspace` の対象外
- dependency の表現ルールも定義した
  - published runtime dependency は `[project.dependencies]`
  - reusable optional feature は `[project.optional-dependencies]`
  - 開発 / test / security などローカル専用 dependency は `[dependency-groups]`
  - local component 参照は `[tool.uv.sources]`
- 標準コマンド一覧を次のように定義した
  - 初回セットアップ
    - `uv sync`
  - 開発用 dependency を含む同期
    - `uv sync`
  - 本番相当の最小同期
    - `uv sync --no-dev`
  - 特定 group を含める同期
    - `uv sync --group test`
    - `uv sync --group security`
  - API 起動
    - `uv run uvicorn app.main:app --reload`
    - 将来は `uv run uvicorn koiki_ref_app.main:app --reload` など新 ASGI path に読み替える
  - テスト実行
    - `uv run pytest`
  - スクリプト実行
    - `uv run python <script>`
  - lockfile 更新
    - `uv lock`
  - lockfile 更新を伴わない CI 実行
    - `uv sync --locked`
    - `uv run --locked pytest`
- CI / Docker / local setup への影響も整理した
  - CI は `poetry install` / `poetry run` から `uv sync --locked` / `uv run --locked ...` へ置換する前提
  - Dockerfile / Compose の `poetry install` は Stage 6 で `uv sync` ベースへ置換する
  - `docs/dev/local_setup.md`、テストガイド、監査系 runbook の Poetry コマンドは Stage 2 以降の更新対象
- 方針の根拠として、次の `uv` 公式ドキュメントを確認した
  - dependency fields と `dependency-groups`
    - `project.dependencies`
    - `project.optional-dependencies`
    - `dependency-groups`
    - `tool.uv.sources`
  - automatic lock / sync と `uv run --locked`
  - workspace member の `tool.uv.workspace` と `workspace = true`

未解決事項:

- root を最終的に virtual workspace root とするか、root 自体も workspace member package とするかは Stage 5 の `components/` 移動時に再確認が必要
- `dev` / `test` / `security` group をすべて root に置くか、一部を member 側へ持たせるかは Task 2-4 / 2-5 の package 編集時に調整が必要
- `uv build` / `uv publish` を採用するかは今回の Stage 2 スコープ外

検証結果:

- Poetry が担っていた責務と `uv` での置換先を 1 対 1 で説明できる状態になった
- チーム標準コマンドを `uv sync` / `uv run` / `uv lock` 中心で 1 セット提示できた
- 将来の `components/` workspace 化と、現段階の root 単体管理の両方に整合するポリシーになっている
- build backend を今すぐ変えない方針により、Stage 2 を dependency manager 切替へ絞れることを確認した

次タスクへ渡す事項:

- Task 2-2 では、root `pyproject.toml` から Poetry 固有の group / package-mode 依存を減らし、`uv` 前提の workspace メタへ寄せる
- Task 2-3 では、`uv.lock` を導入し、`poetry.lock` からの切替順序を崩さないように進める
- Task 2-4 / 2-5 では、`libkoiki` と `app` の dependency 表現を `project.*` / `dependency-groups` / `tool.uv.sources` 前提で整える

## 次タスク

- [Task 2-2](./task-2-2.md)
