# Task 2-5: Stage 2 結果検証

## 目的

`uv` 移行の方針と前提が、Stage 3 以降に進める品質へ達しているか確認する。

## 参照タスク

- [Task 2-1](./task-2-1.md)
- [Task 2-2](./task-2-2.md)
- [Task 2-3](./task-2-3.md)
- [Task 2-4](./task-2-4.md)

## 事前条件

- Stage 2 の成果物が揃っている

## 確認観点

- `uv` の標準コマンドが定義されているか
- workspace member 方針が pre/post move 両方で説明できるか
- ローカルと CI が同じ `uv` モデルで整理されているか
- Stage 5 で `uv` 周りを全面再設計しなくて済むか

## 実施手順

1. Stage 2 の成果物を横断レビューする
2. ローカル、CI、workspace 設計の一貫性を確認する
3. 未解決事項を列挙する
4. 未解決事項が Stage 3 着手を妨げるか判定する
5. 問題なければ Stage 3 着手可と記録する

## 成果物

- Stage 2 レビュー結果
- Stage 3 着手可否判定

## 検証

- `uv sync`、`uv run`、`uv.lock` が標準経路として説明できる
- Stage 5 で設定破綻しない見通しがある

## 完了条件

- app factory と bootstrap 抽出へ進んでよいと判断できる

## 実施結果

Task:

- Task 2-5: Stage 2 結果検証

変更内容:

- Task 2-1 から Task 2-4 の結果を横断レビューし、Stage 2 の到達点を次の4点に集約した
  - `uv sync` / `uv run` / `uv.lock` を標準経路とする方針が定義済み
  - pre-move / post-move の workspace member 形が整理済み
  - ローカル標準コマンドの `uv` 化が整理済み
  - CI の `uv` 化設計と branch trigger 更新方針が整理済み
- Stage 2 の一貫したモデルを次のように整理した
  - root
    - `uv` 管理 project / 将来 workspace root
  - pre-move member
    - `libkoiki`
    - `app`
  - post-move member
    - `components/libkoiki`
    - `components/koiki_ref_app`
  - 標準コマンド
    - ローカル: `uv sync`, `uv run ...`
    - CI: `uv sync --locked`, `uv run --locked ...`
- Stage 2 結果として、次の前提を固定した
  - Poetry は最終的にチーム標準から外す移行対象
  - build backend 自体の切替は Stage 2 のスコープ外
  - `frontend/` と `apps/` は Python workspace member に含めない
  - Stage 5 では member path と package 名を差し替えるが、workspace モデル自体は維持する
- Stage 3 着手を妨げる blocker の有無を確認し、次のように判定した
  - blocker なし
  - ただし、実ファイル更新が未着手の論点は Stage 2 後続の実装作業として残る
- blocker ではない未解決事項を次のように一覧化した
  - root `pyproject.toml` の Poetry 固有記述除去
  - `dependency-groups` と `tool.uv.workspace` の実導入
  - `uv.lock` の実生成
  - `app/pyproject.toml` の runtime/dev/test 再設計
  - `libkoiki` の optional extra 設計
  - ローカル文書、CI workflow、Dockerfile の実更新
- 上記未解決事項についての判定も整理した
  - これらは「Stage 2 の方針が不足している」問題ではなく、「今後の実編集・実装作業が残っている」問題
  - app factory と bootstrap 抽出の設計検討自体は、この段階で開始可能
  - ただし Stage 3 の実装で `uv` 環境を使う前には、少なくとも root の実際の `uv` 導線整備を着手順に入れる必要がある
- Stage 3 着手可否を次のように記録した
  - 着手可
  - 前提条件:
    - Stage 3 の設計・方針決定は、Stage 2 で固めた `uv` モデルを前提に進める
    - 実際のローカル実行や CI 更新は、Stage 2 の実ファイル更新と並行または直後に進める

未解決事項:

- 現在の `pyproject.toml` 群はまだ Poetry / `setuptools` 前提の実記述を保持しており、Stage 2 は文書上の設計固定が中心である
- Stage 3 の実装に入る前に、`uv` をローカルで実際に成立させる変更をどのタイミングで入れるかは、作業順の再確認が必要
- `Task 2-5` の性質上、ここでの「着手可」は Stage 2 の設計完了を意味し、`uv` 移行実装完了を意味しない点は明示が必要

検証結果:

- `uv sync`、`uv run`、`uv.lock` が標準経路であることを一貫して説明できる状態になった
- workspace member 方針は pre-move / post-move の両方で説明できる
- ローカルと CI は同じ `uv` モデルで整理されており、CI だけ別運用になるリスクは低い
- Stage 5 で `uv` 設定を全面再設計しなくて済む見通しが立っている
- app factory / bootstrap 抽出の設計検討へ進んでよいと判断できた

次タスクへ渡す事項:

- Stage 3 / Task 3-1 では、`app.main` の責務棚卸しを `uv` 前提の新構成を意識して進める
- Stage 2 の実ファイル更新タスクは、Stage 3 の実装に入る前後で優先順位を再確認しつつ継続する
- `app` から `koiki_ref_app` への再設計は、app factory の責務分離と密接なので Stage 3 と連動させる

## 次タスク

- Stage 3 / Task 3-1
