# Task 1-6: Stage 1 結果検証

## 目的

Stage 1 の判断結果が、Stage 2 の `uv` 移行に進める品質に達しているか確認する。

## 参照タスク

- [Task 1-1](./task-1-1.md)
- [Task 1-2](./task-1-2.md)
- [Task 1-3](./task-1-3.md)
- [Task 1-4](./task-1-4.md)
- [Task 1-5](./task-1-5.md)

## 事前条件

- Stage 1 の各タスク結果が記録されている

## 確認観点

- root、`libkoiki`、`app` の責務が説明できるか
- `setup.py` 廃止可否が判断できているか
- runtime/dev/test の境界が見えているか
- `libkoiki` 依存境界が再利用責務に一致しているか

## 実施手順

1. Stage 1 の成果物を横断レビューする
2. 未解決事項を一覧化する
3. 未解決事項が Stage 2 着手を妨げるかを判定する
4. 妨げるものがあれば Stage 1 に差し戻す
5. 問題なければ Stage 2 着手可と記録する

## 成果物

- Stage 1 レビュー結果
- Stage 2 着手可否判定

## 検証

- dependency の責務が曖昧な項目が残っていない
- `uv` 化の前提に致命的な未解決事項がない

## 完了条件

- Stage 2 に進んでよいと判断できる

## 実施結果

Task:

- Task 1-6: Stage 1 結果検証

変更内容:

- Task 1-1 から Task 1-5 の結果を横断レビューし、Stage 1 の判断を次の4点に集約した
  - root `pyproject.toml` は配布 package ではなく workspace メタデータとして再定義する
  - `libkoiki` の package 定義正本は `libkoiki/pyproject.toml` に一本化する
  - `app` / 将来の `koiki_ref_app` は runtime と dev/test を明確に分離する
  - `libkoiki` の依存は reusable framework core と app / 運用依存へ切り分ける
- Stage 1 の到達点として、root / `libkoiki` / `app` の責務を次のように整理した
  - root
    - workspace 全体の Python バージョン制約、tool 設定、将来の `uv workspace` 設定を持つ
    - package 本体の runtime dependency は持たない方向
  - `libkoiki`
    - reusable framework package
    - package 定義の正本は `pyproject.toml`
    - SAML や migration 運用依存は core runtime に含めない方向
  - `app`
    - 現行参照アプリ実装
    - 将来 `koiki_ref_app` へ置き換える前提で、runtime と dev/test を分離する
- Stage 2 着手を妨げる blocker の有無を確認し、次の結論を記録した
  - blocker なし
  - ただし package 実編集時に決める必要がある設計論点は残る
- blocker ではないが Stage 2 へ持ち越す未解決事項を一覧化した
  - `libkoiki` の optional extra をどう切るか
    - `monitoring`
    - `auth/form`
    - `schema validation`
  - `alembic` を workspace へ置くか、`koiki_ref_app` 側へ置くか
  - root の `[project]` をどこまで縮小し、`tool.uv.workspace` にどう置き換えるか
  - `app/pyproject.toml` を延命するか、`koiki_ref_app` 向けに新規設計するか
  - `asyncpg` 固定を当面維持するか
- 上記未解決事項について、現時点ではいずれも Stage 2 で package 定義と `uv` 導入方針へ落とし込む設計論点であり、Stage 1 の差し戻し理由にはならないと判断した
- Stage 2 着手可否を次のように判定した
  - 着手可
  - 前提条件:
    - Stage 2 では「root は workspace」「runtime dependency は component package」という Stage 1 の結論を維持する
    - `libkoiki/setup.py` は削除候補として扱い、実削除は Stage 2 以降の package 編集に合わせて行う
    - `python3-saml` / `xmlsec` / `alembic` / `psycopg2-binary` / `aiosqlite` は `libkoiki` core runtime に戻さない

未解決事項:

- Stage 2 で実際に `uv` へ切り替える際、`poetry.lock` と `uv.lock` の切替順序を誤ると差分が大きくなるため、Task 2-1 から 2-3 の順序を崩さない方がよい
- optional extra の最終形は、Task 2-4 / 2-5 で実 package 定義を触りながら再確認が必要
- `koiki_ref_app` の package 定義は現行 `app/pyproject.toml` の単純修正ではなく、再設計になる可能性が高い

検証結果:

- root、`libkoiki`、`app` の責務を一貫して説明できる状態になった
- `setup.py` 廃止可否については「廃止可能、ただし実削除は Stage 2 以降で package 編集と合わせる」が結論として定まった
- runtime / dev / test の境界は、root・`libkoiki`・`app` の各レイヤで説明できる状態になった
- `libkoiki` 依存境界は再利用責務と整合しており、SAML と運用依存の切り分けも明確になった
- `uv` 化の前提に致命的な未解決事項は残っていないと判断できた

次タスクへ渡す事項:

- Task 2-1 では、Stage 1 の結論を前提に `uv` 導入ポリシーを定義する
- Stage 2 では root `pyproject.toml` を workspace メタへ寄せ、package runtime dependency を root から外す方向で編集を進める
- `libkoiki` package 編集時には optional extra 候補と `setup.py` 削除を一体で扱う
- `app` 側 package は `koiki_ref_app` 前提の再設計を意識して扱う

## 次タスク

- [Task 2-1](./task-2-1.md)
