# Task 0-2: ブランチ運用方針の確定

## 目的

`v0.7` 再編線と `v0.6` 保守線を明確に分け、以後の PR ベースに迷いが出ないようにする。

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)

## 事前条件

- [Task 0-1](./task-0-1.md) が完了している

## 決める内容

- 既定ブランチを `main` にするか
- `support/0.6` を保守線にするか
- `topic/*` と `feature/*` の命名ルール
- `release/0.7` の切り出し条件
- `main` の切り出し元を `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` にするか

## 実施手順

1. 現在のブランチ方針と計画書の記述を照合する
2. 現在の開発突端ブランチを確認し、`samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を `main` 切り出し元の正式候補として記録する
3. `main`、`support/0.6`、短命ブランチの役割を簡潔に定義する
4. `v0.7` 作業は `main`、`v0.6.x` 修正は `support/0.6` と明文化する
5. `topic/*` と `feature/*` の命名例を 3 つ以上示す
6. PR の base branch ルールを記録する

## 成果物

- ブランチ運用ルールメモ
- 命名規則メモ
- PR base branch ルール
- `main` 切り出し元ブランチ名の記録

## 検証

- 次の問いに迷わず答えられる
  - `v0.7` 再編はどこへ出すか
  - `v0.6.x` 修正はどこへ出すか
  - ツール整理は `topic/*` か `feature/*` か
  - `main` はどのブランチの `HEAD` を基点に作るか

## 完了条件

- 計画書と実 Git 運用の前提が一致している
- `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を `main` の正式な切り出し元候補として固定できている
- Stage 1 以降の作業ブランチを切れる

## 実施結果

Task:

- Task 0-2: ブランチ運用方針の確定

変更内容:

- `v0.7` 構造再編の主線は `main`、`v0.6.x` 保守線は `support/0.6` とする方針を確認した
- 現在の開発突端ブランチ `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を、`main` 切り出し元の正式候補として固定した
- 短命ブランチの使い分けを次で固定した
  - `topic/*`: 狭い範囲のツール変更、メタデータ整理、CI 更新
  - `feature/*`: app factory、template 構造、component レイアウトのような大きめの構造変更
- 命名例として、次を採用候補とした
  - `topic/metadata-cleanup`
  - `topic/uv-migration`
  - `feature/app-factory`
  - `feature/template-structure`
  - `feature/components-layout`
  - `topic/ci-workspace-update`
- PR base branch ルールを次で整理した
  - `v0.7` 再編系 PR は `main`
  - `v0.6.x` 保守系 PR は `support/0.6`
  - `support/0.6` 側で必要な修正は、必要に応じて `main` へ forward-port

未解決事項:

- 現時点の remote default branch は `origin/master` のままであり、実際の `main` 作成と default branch 切替はまだ未実施
- `support/0.6` の実ブランチ作成は、Task 0-3 で基点コミット確定後に行う前提

検証結果:

- 現在の checkout ブランチが `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` であることを確認した
- local branch 一覧に `main`、`support/0.6` がまだ存在しないことを確認した
- `origin/HEAD` が `refs/remotes/origin/master` を指していることを確認した
- 計画書日英版、タスク分解書、Task 0-2 指示書の記述が、`main` / `support/0.6` / 基点ブランチ前提で整合していることを確認した

次タスクへ渡す事項:

- Task 0-3 で `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` のどのコミットを基準点にするかを確定する
- Task 0-3 の結果を受けて、`support/0.6` と `main` の切り出し基点を一意に記録する
- 実際の `main` 作成、default branch 切替、branch protection は、基準点確定後に別操作として進める

## 次タスク

- [Task 0-3](./task-0-3.md)
