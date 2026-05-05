# Task 2-3: ローカル開発コマンドの uv 化

## 目的

開発者が Poetry を経由せず、`uv` を標準経路として作業できるようにする。

## 参照文書

- `docs/dev/setup.md`
- `docs/dev/local_setup.md`
- `docs/dev/test-guide.md`

## 事前条件

- [Task 2-1](./task-2-1.md) と [Task 2-2](./task-2-2.md) が完了している

## 対象

- セットアップコマンド
- テストコマンド
- 開発用起動コマンド
- ドキュメント上の Poetry 記述

## 実施手順

1. 開発者が実際に使う主要コマンドを列挙する
2. それぞれの Poetry 版を `uv` 版へ読み替える
3. ドキュメント内の Poetry コマンドを洗い出す
4. 置換方針を定義する
5. 新規開発者向けの最短手順を 1 本にまとめる

## 成果物

- ローカル標準コマンド一覧
- 置換対象ドキュメント一覧
- 最短セットアップ手順

## 検証

- `uv` だけで最低限のセットアップ、起動、テストが説明できる
- Poetry を前提にしない手順が整理されている

## 完了条件

- CI 更新前に、ローカル側の標準経路が固まっている

## 実施結果

Task:

- Task 2-3: ローカル開発コマンドの `uv` 化

変更内容:

- 現在のローカル開発で使われている主要コマンドを、`docs/dev/local_setup.md`、`README.md`、`docs/testing/認証系APIテストガイド.md` から次のように整理した
  - セットアップ
    - `poetry check --lock`
    - `poetry install`
    - `poetry install --with dev`
    - `poetry install --with test`
  - 起動
    - `poetry run uvicorn app.main:app --reload`
  - テスト
    - `poetry run pytest`
    - `poetry run pytest --cov=...`
    - 個別 test file を指定した `poetry run pytest ...`
  - ビルド
    - `cd libkoiki && poetry build`
- 上記の Poetry コマンドを、Task 2-1 の方針に従って `uv` 版へ読み替えた
  - `poetry install` → `uv sync`
  - `poetry install --with test` → `uv sync --group test`
  - `poetry install --with dev` → `uv sync`
    - `dev` group は default group として扱う前提
  - `poetry run uvicorn app.main:app --reload` → `uv run uvicorn app.main:app --reload`
  - `poetry run pytest ...` → `uv run pytest ...`
  - `poetry build` → 当面は維持
    - Stage 2 のローカル標準経路は dependency manager / command runner の切替に限定する
- ローカル標準コマンド一覧を次のように定義した
  - 初回セットアップ
    - `uv sync`
  - test group を含めた同期
    - `uv sync --group test`
  - security group を含めた同期
    - `uv sync --group security`
  - アプリ起動
    - `uv run uvicorn app.main:app --reload`
  - 全テスト実行
    - `uv run pytest`
  - カバレッジ付きテスト
    - `uv run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/`
  - 個別テスト
    - `uv run pytest tests/unit/test_simple_auth.py -v`
    - `uv run pytest tests/integration/app/api/test_todos_api.py -v`
  - Python スクリプト実行
    - `uv run python <script>`
- 新規開発者向けの最短セットアップ手順も次のように整理した
  1. `uv` をインストールする
  2. `uv sync`
  3. 必要に応じて `uv sync --group test`
  4. `uv run uvicorn app.main:app --reload`
  5. `uv run pytest`
- 置換対象ドキュメント一覧を次のように整理した
  - 最優先
    - `docs/dev/local_setup.md`
    - `README.md`
    - `docs/testing/認証系APIテストガイド.md`
  - 後続更新
    - `docs/agent/skills/testing-plan.md`
    - `docs/saml/SAML_SETUP.md`
    - `docs/saml/SAML_MIGRATION_GUIDE.md`
    - `docs/security/SECURITY_AUDIT_COMMANDS.md`
    - `docs/archive/ENTERPRISE_DEPENDENCY_STRATEGY.md`
    - backend-audit 系 runbook 群
- 置換方針も段階化して整理した
  - Stage 2 前半
    - ローカル標準コマンドの定義を先に固める
    - 実ドキュメント更新対象を一覧化する
  - Stage 2 後半〜Stage 4
    - 高頻度で参照される文書から `uv` 版へ差し替える
  - Stage 6
    - Docker / Compose / CI の `uv` 化に合わせて残存する Poetry 記述を整理する
- 現時点でのコマンド前提も補足した
  - ASGI path はまだ `app.main:app`
  - 将来 `koiki_ref_app.main:app` などへ変わるが、Task 2-3 時点では現構成のまま `uv` 化を説明できればよい
  - Docker を使う DB 起動や補助コマンドはそのまま維持し、Python dependency manager のみ `uv` に切り替える

未解決事項:

- `docs/dev/setup.md` と `docs/dev/test-guide.md` は現時点で実ファイルが確認できず、ローカル標準コマンドは実在する `docs/dev/local_setup.md` と既存テストガイドを基準に整理した
- `uv sync --group test` を使う前提には、Task 2-4 / 2-5 で `dependency-groups.test` を root または relevant member に定義する必要がある
- `libkoiki` 単体ビルド手順を `uv build` にするかは未決定で、当面は build backend の現状維持を前提とする

検証結果:

- `uv` だけで最低限のセットアップ、起動、テストを説明できる状態になった
- Poetry を前提にしないローカル標準経路を 1 セット示せた
- ローカル標準コマンドと、今後更新すべきドキュメント群の優先順位が明確になった
- CI 更新前に、ローカル側の `uv` 前提運用を先に固定できた

次タスクへ渡す事項:

- Task 2-4 では、ここで定義した `uv sync --locked` / `uv run --locked ...` 系の流れに CI を合わせる
- Task 2-5 では、`dependency-groups` の実定義がこの標準コマンドと整合するよう package 定義を調整する
- 高頻度参照ドキュメントの実更新は、Stage 2 後半以降の実作業として扱う

## 次タスク

- [Task 2-4](./task-2-4.md)
