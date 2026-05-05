# Task 2-4: CI の uv 化

## 目的

CI を Poetry 依存から切り離し、`uv` ベースの依存管理とテスト実行へ移行する。

## 参照対象

- `.github/workflows/`
- root `pyproject.toml`
- `uv` 導入ポリシー

## 事前条件

- [Task 2-3](./task-2-3.md) が完了している
- ローカル側の標準 `uv` コマンドが定まっている

## 確認観点

- Poetry 前提の install 手順
- キャッシュ戦略
- test 実行コマンド
- branch trigger との整合

## 実施手順

1. 現在の CI workflow を棚卸しする
2. Poetry を前提にした箇所を抽出する
3. `uv` 版の install / run / test フローを設計する
4. キャッシュ方針の変更要否を判断する
5. ローカル手順との差異を記録する

## 成果物

- CI 置換方針メモ
- `uv` ベースの workflow 設計

## 検証

- CI が `uv` で何をするか説明できる
- ローカルと CI でコマンド体系が大きく乖離していない

## 完了条件

- 実 workflow 変更に着手できる設計材料が揃っている

## 実施結果

Task:

- Task 2-4: CI の `uv` 化

変更内容:

- `.github/workflows/` を棚卸しし、現時点で実運用 workflow は `ci.yml` のみであることを確認した
- 現行 `ci.yml` の Poetry 前提を次のように整理した
  - `Install Poetry`
  - `Configure Poetry 2.x`
  - `.venv` を `poetry.lock` hash で cache
  - `poetry check --lock`
  - `poetry install --only=main --no-root`
  - `poetry install --only=dev --no-root`
  - `poetry install --no-root`
  - `poetry run pytest ...`
  - `poetry show --tree --only=main`
- branch trigger も現行ブランチ戦略と不整合であることを確認した
  - 現状
    - `push`: `master`, `develop`, `dev/*`, `feature/*`, `bugfix/*`
    - `pull_request`: `master`, `develop`
  - 新方針
    - `main`
    - `dev/v0.7`
    - `topic/*`
    - `feature/*`
    - 必要なら `support/0.6`
- `uv` 版 CI フローを次のように設計した
  - Python setup
    - `actions/setup-python@v5`
  - `uv` install
    - `astral-sh/setup-uv` もしくは公式 install script の利用
    - 方針上は `uv` 自体を CI 内で明示 install
  - lockfile consistency / environment sync
    - `uv sync --locked`
  - test run
    - `uv run --locked pytest ...`
  - optional diagnostics
    - `uv tree` あるいは `uv pip list`
- install / run / test の CI 標準コマンドを次のように定義した
  - install / sync
    - `uv sync --locked`
  - test
    - `uv run --locked pytest --cov=app --cov=libkoiki --cov-report=term-missing --cov-report=html ...`
  - dependency tree diagnostics
    - `uv tree`
- キャッシュ戦略の変更方針も整理した
  - Poetry 時代の `.venv` cache 直保持から、`uv` の global cache 前提へ切り替える
  - `uv.lock` を cache key に使う
  - `.venv` をそのまま使うかは `uv` の既定挙動と CI 所要時間を見て判断するが、少なくとも Poetry 固有 cache 設定は不要
  - 目的は Poetry 仮想環境 cache ではなく、`uv` の dependency cache を活用すること
- ローカル手順との差異も整理した
  - ローカル
    - `uv sync`
    - `uv run pytest`
  - CI
    - `uv sync --locked`
    - `uv run --locked pytest`
  - 差分は lockfile を固定するかどうかであり、コマンド体系は揃える
- 実 workflow 変更時の設計メモも整理した
  - `poetry check --lock` は `uv lock --check` 相当の考え方へ置換するか、`uv sync --locked` の失敗で整合性確認を兼ねる
  - `poetry show --tree --only=main` は `uv tree` へ読み替える
  - HTML coverage artifact upload は現行のまま維持可能
  - PostgreSQL service と `DATABASE_URL`、`ENV_FILE` は dependency manager 切替の影響を受けない
- branch trigger の推奨更新も次のように整理した
  - `push`
    - `main`
    - `dev/v0.7`
    - `topic/*`
    - `feature/*`
    - `support/0.6` を保守 CI 対象にするかは別途判断
  - `pull_request`
    - `main`
    - `dev/v0.7`
- 実装上の補足として、`.github/workflows/security.yml` は存在せず、security 系チェックは別 workflow ではなく今後の CI 設計に含める前提で扱うと記録した

未解決事項:

- `uv` の install を `astral-sh/setup-uv` action で行うか、script install で行うかは実 workflow 更新時に統一する必要がある
- test / security / dev group を CI でどう選択的に sync するかは Task 2-5 の dependency-group 実定義に依存する
- `support/0.6` を CI trigger に含めるかは、保守線の自動テスト範囲と合わせて最終決定が必要

検証結果:

- CI が `uv` で何をするかを install / cache / run / test / trigger の単位で説明できる状態になった
- ローカルと CI のコマンド体系は、`--locked` 有無以外は大きく乖離しない設計になった
- 実 workflow 変更に着手するための設計材料が揃った
- 現行 CI の古い branch trigger も、Stage 0 で確定したブランチ戦略へ合わせて見直す必要が明確になった

次タスクへ渡す事項:

- Task 2-5 では、`dependency-groups` と package 定義を CI の `uv sync --locked` 前提に合わせて整える
- 実 workflow 更新時には `master/develop` 前提の trigger を `main/dev/v0.7/topic/*/feature/*` 前提へ更新する
- Poetry 固有 cache と install 手順は、workflow 更新時にまとめて除去する

## 次タスク

- [Task 2-5](./task-2-5.md)
