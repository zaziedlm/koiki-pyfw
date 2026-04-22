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

## 次タスク

- [Task 2-3](./task-2-3.md)
