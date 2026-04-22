# Task 2-2: pre-move workspace member 定義

## 目的

現行構造のままで `uv workspace` を成立させつつ、将来の `components/` 移動にも繋がる形を先に設計する。

## 参照ファイル

- root `pyproject.toml`
- `libkoiki/pyproject.toml`
- `app/pyproject.toml`

## 事前条件

- [Task 2-1](./task-2-1.md) が完了している

## 確認観点

- pre-move member
- post-move member
- root workspace 設定との整合
- Stage 5 で再設計不要か

## 実施手順

1. 現在の member 候補を整理する
2. `libkoiki` と `app` を前提に pre-move 形を作る
3. `components/libkoiki` と `components/koiki_ref_app` を前提に post-move 形を作る
4. 差分と移行時の変更点をメモする
5. Stage 5 で設定を全面やり直ししないための条件を整理する

## 成果物

- pre-move workspace member 案
- post-move workspace member 案
- 差分メモ

## 検証

- pre-move と post-move の両方が 1 枚で説明できる
- Stage 5 で `uv` 設定を破壊的に作り直さずに済む見通しがある

## 完了条件

- Task 2-3 と Task 2-4 の実装前提が定まっている

## 実施結果

Task:

- Task 2-2: pre-move workspace member 定義

変更内容:

- `libkoiki/pyproject.toml` と `app/pyproject.toml` の package 名と責務を確認し、workspace 設計の前提を次のように整理した
  - `libkoiki`
    - 再利用 framework package
    - workspace member 化して問題ない
  - `app`
    - 現状 package 名は `koiki-app`
    - 将来 `koiki_ref_app` へ置き換える前提の暫定 member
  - root
    - 現段階では workspace root 兼 coordination project
    - 将来も Python workspace root として残す
- pre-move workspace member 案を次のように定義した
  - root
    - `koiki-pyfw`
  - member
    - `libkoiki`
    - `app`
  - `tool.uv.workspace.members`
    - `["libkoiki", "app"]`
- pre-move での dependency/source 取り扱いも整理した
  - root は当面 `uv run` の実行起点として使う
  - root から `libkoiki` を参照する場合は `tool.uv.sources.libkoiki = { workspace = true }` を使う前提
  - `app` は workspace member として登録するが、Task 2-5 で `app/pyproject.toml` を整えるまでは「root が直ちに `koiki-app` のみを依存として持つ」形には固定しない
  - 理由:
    - 現在の root には app 固有 dependency がまだ残っており、Stage 2 前半で一気に切り替えると起動導線が崩れやすい
    - `app/pyproject.toml` 自体がまだ参照アプリ package として未完成
- pre-move の狙いを次のように定義した
  - `uv workspace` 自体は現構造で先に成立させる
  - ただし root runtime 依存の整理と app package の再設計は段階的に進める
  - Stage 2 の早い段階では「workspace member 宣言」と「root の `uv` 化」を先に行い、完全な dependency 正規化は Task 2-4 / 2-5 で仕上げる
- post-move workspace member 案を次のように定義した
  - root
    - `koiki-pyfw`
  - member
    - `components/libkoiki`
    - `components/koiki_ref_app`
  - `tool.uv.workspace.members`
    - `["components/libkoiki", "components/koiki_ref_app"]`
- post-move の source 取り扱いも定義した
  - root あるいは `components/koiki_ref_app` が `libkoiki` を参照する場合は `tool.uv.sources.libkoiki = { workspace = true }`
  - `koiki_ref_app` は `libkoiki` を workspace member dependency として扱う
  - `frontend/` は Python workspace member に含めない
  - `apps/` は案件固有実装であり、root workspace member に一律では含めない
- pre-move と post-move の差分を次のように整理した
  - member path
    - `libkoiki` → `components/libkoiki`
    - `app` → `components/koiki_ref_app`
  - member package 名
    - `koiki-app` → `koiki_ref_app` へ再設計
  - root の `tool.uv.workspace.members` の path 更新
  - `tool.uv.sources` の path/workspace 参照更新
- Stage 5 で `uv` 設定を全面やり直ししないための条件も整理した
  - workspace root は Stage 2 の時点から root のまま維持する
  - member 数は pre-move と post-move で `libkoiki` / 参照アプリの2系統を維持する
  - `frontend/` と `apps/` を workspace member に含めない方針を今の段階で固定する
  - source 参照は path 直書きではなく `workspace = true` 前提へ寄せる
  - root を「全 runtime dependency を抱える本体 package」として再定義しない
- pre-move から post-move への移行イメージも 1 枚で説明できるように整理した
  - pre-move
    - root + `libkoiki` + `app`
  - post-move
    - root + `components/libkoiki` + `components/koiki_ref_app`
  - 本質的に変えるのは path と app package 名であり、workspace という枠組み自体は維持する

未解決事項:

- root が最終的に publish しない virtual coordination project に近づくのか、軽量な workspace root member として残るのかは Stage 5 時点で再確認が必要
- `app` を pre-move member とする以上、Task 2-5 では `app/pyproject.toml` の runtime/dev 分離と app 固有 dependency の補完を行わないと workspace と実運用の整合が弱い
- root が `koiki-app` を直接依存に持つかどうかは、Task 2-5 の package 設計結果を見て最終決定する

検証結果:

- pre-move と post-move の両方を 1 枚の設計として説明できる状態になった
- Stage 5 で `uv` 設定を全面やり直しせず、member path と package 名の更新で追従できる見通しが立った
- `frontend/` と `apps/` を workspace member から外す方針が明確になり、root Python workspace の範囲が定まった
- Task 2-3 と Task 2-4 が、root workspace を前提にした `uv` コマンド体系で進められる状態になった

次タスクへ渡す事項:

- Task 2-3 では、pre-move workspace 前提でローカル標準コマンドを `uv` へ置換する
- Task 2-4 では、CI も root workspace を起点に `uv sync --locked` / `uv run --locked` へ読み替える
- Task 2-5 では、`app` member を将来 `koiki_ref_app` へ移す前提で package 定義を見直す

## 次タスク

- [Task 2-3](./task-2-3.md)
