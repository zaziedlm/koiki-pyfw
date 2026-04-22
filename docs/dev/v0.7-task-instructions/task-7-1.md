# Task 7-1: 互換 wrapper の棚卸し

## 目的

Stage 5 までの移設で残した互換 wrapper / shim / legacy import を一覧化し、Stage 7 で削除対象と順序を明確にする。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `app/__init__.py`
- `app/main.py`
- `main.py`
- `components/koiki_ref_app/src/koiki_ref_app/**`
- `components/koiki_ref_app/tests/**`
- `tests/conftest.py`

## 事前条件

- [Task 6-6](./task-6-6.md) が完了している

## 確認観点

- `app` package を互換維持するための wrapper / path 注入が何か
- root `main.py` がまだ必要か
- `koiki_ref_app` 側で `from app...` に依存している箇所がどこか
- tests / conftest が旧 `app` 導線に依存しているか

## 実施手順

1. `app/__init__.py` と `app/main.py` の互換責務を確認する
2. root `main.py` の役割を確認する
3. `rg` で `from app.` / `import app.` / `app.main:app` / path 注入箇所を検索する
4. 互換導線を「削除候補」「Stage 7 中は残すもの」に分類する
5. 次タスクで除去する順序を整理する

## 成果物

- 互換 wrapper / shim 一覧

## 検証

- Stage 7-2 以降で削る対象が一覧化されている

## 完了条件

- legacy import / shim 除去の対象と順序を説明できる

## 実施結果

Task:

- Task 7-1: 互換 wrapper の棚卸し

変更内容:

- `app/__init__.py` を確認し、互換 layer の中心であることを整理した
  - `pkgutil.extend_path`
  - `sys.path` への `components/koiki_ref_app/src` と `components/libkoiki/src` 注入
  - `koiki_ref_app` package path を `app` package 側へ append
- `app/main.py` を確認し、`from koiki_ref_app.asgi import app` だけを持つ薄い wrapper であると整理した
- root `main.py` を確認し、Docker / ローカル互換のために `from app.main import app` と `uvicorn.run(\"app.main:app\", ...)` を保持していると整理した
- `rg` で旧 `app` 依存を検索し、主な残件を抽出した
  - `components/koiki_ref_app/src/koiki_ref_app/**` 内の `from app...`
  - `components/koiki_ref_app/tests/**` 内の `from app...`
  - `tests/conftest.py` の `from app.main import app`
  - root `main.py` の `app.main:app`
- 互換導線を次の 2 群へ分類した
  - 即時除去候補
    - `koiki_ref_app` 実装内の `from app...`
    - `koiki_ref_app` test 内の `from app...`
    - `tests/conftest.py` の `from app.main import app`
  - Stage 7 中は最後まで残す候補
    - `app/__init__.py`
    - `app/main.py`
    - root `main.py`
    - Docker / docs 上の `app.main:app`

未解決事項:

- `koiki_ref_app` 側の `from app...` は数が多く、Stage 7-2 で package import をまとめて置換する必要がある
- `app/__init__.py` は path 注入に依存するため、除去前に全 import を `koiki_ref_app` へ切り替える必要がある
- root `main.py` の除去時期は Docker / docs の正式 ASGI path 切替と連動する

検証結果:

- 互換 wrapper は `app/__init__.py`、`app/main.py`、root `main.py` の 3 点が中心であると確認した
- legacy import の主戦場は `components/koiki_ref_app` 実装と test 群であると確認した
- したがって Stage 7-2 は、まず `from app...` を `koiki_ref_app...` へ置換し、その後 wrapper 除去可否を判断する順が妥当

次タスクへ渡す事項:

- Task 7-2 では `components/koiki_ref_app` 実装と test から `from app...` を除去する
- wrapper 本体の削除は、その後の import / test / startup 確認を見て判断する

## 次タスク

- [Task 7-2](./task-7-2.md)
