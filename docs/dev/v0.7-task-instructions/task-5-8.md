# Task 5-8: Stage 5 結果検証

## 目的

新構造が import / test / package 観点で成立しているか確認し、Stage 6 へ渡す未解決事項を整理する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-4.md`
- `docs/dev/v0.7-task-instructions/task-5-5.md`
- `docs/dev/v0.7-task-instructions/task-5-6.md`
- `docs/dev/v0.7-task-instructions/task-5-7.md`
- `pyproject.toml`
- `apps/README.md`

## 事前条件

- [Task 5-7](./task-5-7.md) が完了している

## 確認観点

- `components/` と `apps/` の構造
- `libkoiki` / `koiki_ref_app` の import 導線
- pytest `testpaths`
- root `tests/` に残すものと移したものの整合

## 実施手順

1. `components/` と `apps/` の存在と役割を確認する
2. `libkoiki` と `koiki_ref_app` の import 動作を最低限確認する
3. pytest `testpaths` が新構成を含むか確認する
4. root `tests/` に app 固有テストが残っていないか確認する
5. Stage 6 へ渡す未解決事項を整理する

## 成果物

- Stage 5 検証記録

## 検証

- `components/` と `apps/` の構造が意図通り機能している
- `libkoiki` と `koiki_ref_app` の package import が path 面で成立している

## 完了条件

- Stage 6 着手可否を判断できる

## 実施結果

Task:

- Task 5-8: Stage 5 結果検証

変更内容:

- Stage 5 で作った新構造を横断確認した
  - `components/`
    - `libkoiki`
    - `koiki_ref_app`
  - `apps/`
    - `README.md`
- pytest `testpaths` が新構成を含むことを確認した
  - `tests`
  - `components/libkoiki/tests`
  - `components/koiki_ref_app/tests`
- root `tests/` に残るものを確認した
  - `tests/unit/agent_guidance`
  - root shared tests
  - `tests/integration/services`
  - app 固有の `tests/unit/app` と `tests/integration/app` は移設済み

未解決事項:

- guidance / README 類の移動は未コミットで残っている
  - `components/libkoiki/AGENTS.md`
  - `components/libkoiki/CLAUDE.md`
  - `components/libkoiki/README.md`
  - `components/koiki_ref_app/AGENTS.md`
  - `components/koiki_ref_app/CLAUDE.md`
  - `apps/README.md`
- `app/AGENTS.md` と `app/CLAUDE.md`、旧 `libkoiki` 側 guidance file の削除も未コミット
- Stage 6 で CI / Docker / docs / instructions の path と command を新構成へ追随させる必要がある
- 依存同期が未実施のため、FastAPI / SQLAlchemy を含む runtime import と pytest 実行の完全確認は未完了

検証結果:

- `python -c "..."` で `components/libkoiki/src` を追加した状態の `import libkoiki` は成功した
- `python -c "..."` で `components/koiki_ref_app/src` を追加した状態の `import koiki_ref_app` も成功した
- pytest `testpaths` は新構成へ追随済み
- root `tests/` から app 固有 test 配下は消えており、component 所有に寄った配置になっている
- したがって Stage 5 の構造変更は成立しており、Stage 6 へ進める

次タスクへ渡す事項:

- Stage 6 では Alembic / CI / Docker / scripts を新配置へ一括追随させる
- docs / guidance / placeholder 類は、必要に応じて別コミットで整理する

## 次タスク

- Stage 6 / Task 6-1
