# Task 2-7: `uv.lock` 生成と lockfile 切替

## 目的

`uv.lock` を正規 lockfile として成立させ、Poetry lockfile 依存から切り替える。

## 推奨ブランチ

- `topic/uv-lock-adoption`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-6](./task-2-6.md)

## 事前条件

- [Task 2-6](./task-2-6.md) が完了している
- root workspace metadata が `uv` 用に反映されている

## 確認観点

- `uv lock` が依存解決に成功するか
- component 間参照が lock 解決を妨げていないか
- `poetry.lock` の扱いが曖昧になっていないか
- lockfile 切替順序が docs と一致しているか

## 実施手順

1. `uv lock` 実行前に、依存競合の可能性がある箇所を確認する
2. `uv lock` を実行し、`uv.lock` を生成する
3. lock 解決に失敗した場合は dependency 定義を修正し、再実行する
4. 生成された `uv.lock` が root workspace と component 依存を反映しているか確認する
5. `poetry.lock` を残すか削除するかの切替タイミングを決める
6. lockfile の正本を `uv.lock` とする方針を docs に反映する

## 成果物

- `uv.lock`
- lockfile 切替方針メモ

## 検証

- `uv.lock` が生成されている
- lock 解決に失敗する未解決 dependency conflict が残っていない
- `poetry.lock` の扱いが文書上で説明できる

## 完了条件

- Task 2-8 と Task 2-9 が `uv.lock` を前提に進められる

## 実施結果

Task:

- Task 2-7: `uv.lock` 生成と lockfile 切替

変更内容:

- `uv lock` を実行し、root に `uv.lock` を生成した
- 生成された `uv.lock` が root workspace と component 依存を反映していることを確認した
  - `koiki-pyfw`
  - `koiki-ref-app`
  - `libkoiki`
- workspace package は editable source として lock された
  - `components/koiki_ref_app`
  - `components/libkoiki`
- `uv.lock` を Stage 2 以降の lockfile 正本として扱う方針を固定した

lockfile 切替方針:

- 正本は `uv.lock`
- `poetry.lock` は Task 2-9 の CI 切替後に削除した
  - 理由:
    - CI workflow が `uv.lock` / `uv sync --locked` 前提へ切り替わった
    - local docs / helper script も `uv` 標準経路へ切り替わった
    - lockfile 正本を複数残すと依存解決の source of truth が曖昧になる

未解決事項:

- `components/libkoiki/pyproject.toml` には Poetry 固有設定が残っている
  - これは component の build backend / package discovery に関わる残置であり、root lockfile 正本ではない

検証結果:

- `uv lock` が成功した
- `uv lock --check` が成功した
- `uv.lock` 内で root / component の workspace package が認識されていることを確認した
- 未解決 dependency conflict は確認されなかった

次タスクへ渡す事項:

- Task 2-8 では local docs / helper script を `uv.lock` 前提の `uv sync` / `uv run` に更新する
- Task 2-9 では CI を `uv sync --locked` / `uv run --locked ...` へ切り替え、cache key を `uv.lock` 基準にする

## 次タスク

- [Task 2-8](./task-2-8.md)
- [Task 2-9](./task-2-9.md)
