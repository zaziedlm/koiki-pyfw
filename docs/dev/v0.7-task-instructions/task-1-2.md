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

## 実施結果

Task:

- Task 1-2: `libkoiki/setup.py` 廃止方針の確定

変更内容:

- `libkoiki/setup.py` の内容を確認し、役割を次のように整理した
  - `setuptools.setup()` による従来型 package 定義
  - `find_packages()` による flat layout 前提の package 収集
  - runtime dependency の別定義
- `libkoiki/pyproject.toml` と比較した結果、`setup.py` は現行の正本ではなく、古い定義が残っている状態と判断した
- `setup.py` と `pyproject.toml` の主な差分を確認した
  - `setup.py` にのみある依存
    - `email-validator`
    - `prometheus-client`
    - `python-multipart`
  - `pyproject.toml` にのみある依存
    - `pydantic-settings`
    - `slowapi`
    - `tzdata`
    - version pin を含む各種 runtime dependency
  - 依存構成が一致しておらず、二重管理の状態になっている
- 参照箇所を確認した結果、`setup.py` を直接使う運用は見当たらなかった
  - `docs/dev/local_setup.md` に `pip install -e ./libkoiki` の記載はあるが、「非推奨」と明記されている
  - パッケージング手順は `poetry build` または `python -m build` が推奨されている
- 以上から、`libkoiki` の package 定義の正本は `libkoiki/pyproject.toml` に寄せるべきであり、`setup.py` は削除対象として扱ってよいと判断した

未解決事項:

- `libkoiki/pyproject.toml` 側の dependency 自体もまだ精査途上であり、削除前に Task 1-5 の境界整理を通す必要がある
- `tool.poetry.packages = [{include = \"*\"}]` の妥当性は、将来の `components/libkoiki` / `src` 化も踏まえて別途見直しが必要
- `libkoiki.egg-info` など `setuptools` 由来の成果物整理は、実削除タスク時にあわせて判断が必要

検証結果:

- `setup.py` にしか存在しない package metadata の必須情報は見当たらなかった
- `setup.py` の dependency 定義は `pyproject.toml` と不整合であり、正本として扱うべきではないことを確認した
- 現行ドキュメント上でも `setup.py` ベース運用は推奨されていないことを確認した

次タスクへ渡す事項:

- Task 1-3 では root `pyproject.toml` の workspace 責務を明確化する
- Task 1-5 で `libkoiki` に残すべき依存を精査した上で、`setup.py` 削除の最終判断へ進む
- Stage 1 の結論としては、「`libkoiki` の package 定義は `pyproject.toml` に一本化する」方向で問題ない
- 実削除自体は、Task 1-6 または Stage 1 の具体編集タイミングで行う

## 次タスク

- [Task 1-3](./task-1-3.md)
