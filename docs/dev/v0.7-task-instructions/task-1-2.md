# Task 1-2: libkoiki/setup.py 廃止方針の確定

## 目的

`libkoiki` の package 定義を `pyproject.toml` に一本化する前提を固める。

## 参照ファイル

- `libkoiki/setup.py`
- `libkoiki/pyproject.toml`
- root `pyproject.toml`

## 事前条件

- [Task 1-1](./task-1-1.md) の棚卸し結果がある

## 確認観点

- `setup.py` が現時点で担っている役割
- `pyproject.toml` に移せていない情報があるか
- CI、ローカル手順、ビルド手順が `setup.py` に依存しているか

## 実施手順

1. `setup.py` の内容を確認する
2. `pyproject.toml` と比べて差分を洗う
3. 差分が本当に必要かを判断する
4. `setup.py` 廃止の前提条件を列挙する
5. 削除の順序と影響範囲を記録する

## 成果物

- `setup.py` の役割整理メモ
- 廃止可否判断
- 廃止手順案

## 検証

- `setup.py` にしか存在しない必要情報がない
- 廃止後の正本が `libkoiki/pyproject.toml` だと説明できる

## 完了条件

- Task 1-6 で「廃止可能」と判断できる材料が揃っている

## 次タスク

- [Task 1-3](./task-1-3.md)
