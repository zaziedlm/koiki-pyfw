# Task 5-3: test 配置移設準備

## 目的

テストを component 単位に移しやすくするため、`tests/conftest.py` の shared fixture と component fixture を切り分け、`tests/unit/core/` を含むテスト群の帰属を確定する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-1.md`
- `docs/dev/v0.7-task-instructions/task-5-2.md`
- `tests/conftest.py`

## 事前条件

- [Task 5-2](./task-5-2.md) が完了している

## 確認観点

- `tests/conftest.py` の fixture 棚卸し
- shared fixture と component fixture の分離
- `tests/unit/core/` の帰属
- root に残す test 領域

## 実施手順

1. `tests/conftest.py` の fixture を shared / `libkoiki` / `koiki_ref_app` に分類する
2. `tests/unit/` / `tests/integration/` / `tests/e2e/` の現在配置を確認する
3. `tests/unit/core/` の実際の依存先を確認して帰属を決める
4. component move 後の test 配置案を定義する
5. 実移設時の fixture 破断リスクを整理する

## 成果物

- test 配置移設メモ
- fixture 分担表

## 検証

- test 移設時に fixture 崩壊が起きない設計になっている
- component 単位の test ownership を説明できる

## 完了条件

- Task 5-4 / 5-5 の実移設に向けて test 配置方針が固まっている

## 実施結果

Task:

- Task 5-3: test 配置移設準備

変更内容:

- `tests/conftest.py` を棚卸しし、fixture を次の3群に分類した
  - root shared に残す候補
    - `event_loop`
    - pytest marker 登録
  - `libkoiki` 側に寄せる候補
    - `test_settings`
    - `test_engine`
    - `test_db_session`
    - `mock_db_session`
    - `test_repositories`
    - `test_services`
  - `koiki_ref_app` 側に寄せる候補
    - `test_client`
      - `from app.main import app`
      - `libkoiki.db.session.get_db` override
      - 参照アプリの ASGI app に依存
- `tests/conftest.py` が現在抱えている問題も整理した
  - root 直下の `sys.path.insert(...)` に依存している
  - DB fixture と app client fixture が同居している
  - `libkoiki` テストと `app` テストの両方が同じ conftest に依存している
  - component move 後にこのままでは ownership が曖昧
- 現在の test ディレクトリ構成も確認し、帰属を次のように整理した
  - `tests/unit/libkoiki/`
    - `components/libkoiki/tests/unit/` へ移す
  - `tests/unit/app/`
    - `components/koiki_ref_app/tests/unit/` へ移す
  - `tests/integration/app/`
    - `components/koiki_ref_app/tests/integration/` へ移す
  - `tests/integration/services/`
    - 内容で分ける必要があるが、現状は `libkoiki` service に寄るものが多い
  - `tests/e2e/`
    - root `tests/e2e/` に残す
  - `tests/unit/agent_guidance/`
    - repo root の shared / governance test として残す
- `tests/unit/core/` の帰属も確認した
  - `test_logging_sanitizer.py`
  - `test_audit_middleware.py`
  - `test_security_logger.py`
  - `test_time_compliance.py`
  はいずれも `libkoiki.core` や `libkoiki.models` を直接検証しており、app 固有依存を持たない
  - したがって `tests/unit/core/` は root shared ではなく `components/libkoiki/tests/unit/core/` 相当へ寄せる方針を確定した
- component move 後の test 配置案を次のように定義した
  - `components/libkoiki/tests/unit/`
    - 旧 `tests/unit/libkoiki/`
    - 旧 `tests/unit/core/`
  - `components/libkoiki/tests/integration/`
    - `libkoiki` service / repository / DB integration に属するもの
  - `components/koiki_ref_app/tests/unit/`
    - 旧 `tests/unit/app/`
  - `components/koiki_ref_app/tests/integration/`
    - 旧 `tests/integration/app/`
    - app 固有 integration
  - root `tests/e2e/`
    - component を跨ぐ end-to-end
  - root `tests/shared/` 相当
    - 必要なら共通 fixture / helper を保持
  - root `tests/unit/agent_guidance/`
    - リポジトリ全体の guidance 検証として維持
- fixture 分担方針も明文化した
  - root conftest には最小限の shared fixture だけ残す
  - `libkoiki` 専用 fixture は `components/libkoiki/tests/conftest.py` に寄せる
  - `koiki_ref_app` 専用 fixture は `components/koiki_ref_app/tests/conftest.py` に寄せる
  - component 間で共有する helper が必要な場合のみ root `tests/shared/` を使う
- `test_client` の位置づけも明確化した
  - 参照アプリの ASGI app を起動し、dependency override を差し込む fixture なので `koiki_ref_app` 側へ移す
  - Stage 5 / 6 の互換期間は `app.main:app` wrapper を使ってもよいが、source of truth は最終的に `koiki_ref_app.asgi:app`
- integration tests の注意点も整理した
  - `tests/integration/services/` は名称が曖昧なため、実移設時に `libkoiki` / `koiki_ref_app` のどちらに属するか個別に再分類が必要
  - DB / repository / service の integration は component owner を優先して分ける
- fixture 崩壊を避けるための移設順序も整理した
  1. component tests の配置先を作る
  2. `libkoiki` fixture を component conftest へ移す
  3. `koiki_ref_app` fixture を component conftest へ移す
  4. root conftest を最小化する
  5. その後に test path / CI 対象を更新する

未解決事項:

- `tests/integration/services/` の各ファイルを `libkoiki` / `koiki_ref_app` のどちらへ寄せるかは実移設時に個別判断が必要
- root `tests/shared/` を新設するか、root `conftest.py` に最小限残すだけにするかは後続実装時に決めてよい
- `tests/local/` の扱いは Stage 6 以降のローカル運用整理で別途判断が必要

検証結果:

- `tests/conftest.py` の fixture を shared / `libkoiki` / `koiki_ref_app` に分解して説明できる状態になった
- `tests/unit/core/` は `libkoiki.core` のテストとして `components/libkoiki` 側へ寄せる方針を確定できた
- component move 時に root test 構造をどう縮退させるかの道筋が揃った

次タスクへ渡す事項:

- Task 5-4 では `components/libkoiki` 実移設時に、対応する test も `components/libkoiki/tests/` へ寄せる前提で進める
- Task 5-5 では `test_client` と app fixture を `koiki_ref_app` 側へ移す前提で進める
- Stage 6 では CI の test path と coverage source を component 構成に合わせて更新する

## 次タスク

- [Task 5-4](./task-5-4.md)
