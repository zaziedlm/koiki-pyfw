# DM-12 v0.7 legacy / compatibility 棚卸し

作成日: 2026-05-04

対象タスク:

- `docs/dev/deferred-maintenance-tasks.ja.md` の `DM-12`

## 1. 目的

v0.7 から初めて開発に参加するメンバーが、現行実装の場所と過去互換のために残っている場所を誤認しないようにする。

この文書では、v0.6 系の移行経緯から残っている legacy / compatibility 要素を棚卸しし、次のいずれかに分類する。

- `削除候補`
- `互換維持`
- `正規導線へ置換`
- `履歴資料として残す`
- `要追加検証`

この PR では、原則としてファイル削除や entrypoint 変更は行わない。
削除や起動導線変更は、この棚卸し結果に基づいて別 PR で扱う。

## 2. 現行 v0.7 の正規導線

| 項目 | 正規導線 | 備考 |
| --- | --- | --- |
| reusable framework | `components/libkoiki/` | 共有 backend framework の正本 |
| reference application backend | `components/koiki_ref_app/` | 現行 reference app / backend starter の正本 |
| ASGI application | `koiki_ref_app.asgi:app` | Docker / local dev の標準起動先 |
| frontend | `frontend/` | root 配置の starter frontend |
| local setup | `docs/dev/local_setup.md` | uv sync / local run の標準導線 |
| test scope | `components/libkoiki/tests/`, `components/koiki_ref_app/tests/`, root `tests/` | component tests と root shared / e2e / agent guidance tests |
| downstream app area | `apps/` | 案件固有 backend API 実装の予約領域 |

新規開発者に案内する実装場所は、原則として `components/libkoiki/` と `components/koiki_ref_app/` である。

## 3. 棚卸しサマリ

| 対象 | 現状 | 分類 | 初回判断 | 後続対応 |
| --- | --- | --- | --- | --- |
| root `app/` | `app/__init__.py` と `app/main.py` が存在 | `互換維持` / `要追加検証` | `app.main:app` 互換 wrapper として維持 | 互換終了時期を決めた別 PR で削除可否を判断 |
| root `app/main.py` | `koiki_ref_app.asgi.app` を re-export | `互換維持` | 実装正本ではない | docs では新規導線として扱わない |
| root `app/__init__.py` | `components/*/src` を `sys.path` に追加し、namespace path を拡張 | `互換維持` / `要追加検証` | legacy import 対応として維持 | `app.main:app` 互換終了時に撤去可否を判断 |
| root `main.py` | 存在しない | `対応不要` | root cleanup 済み | 旧参照が現行 docs に戻らないよう監視 |
| root `libkoiki/setup.py` | Git 管理下に残存していた。旧 dependency に `passlib[bcrypt]` を含んでいた | `削除済み` | 現行 package metadata と矛盾し、混乱リスクが高いため削除した | DM-12-A で対応済み |
| root `libkoiki/` 配下生成物 | `__pycache__`, `libkoiki.egg-info` などがローカルに存在 | `ローカル artifact` | Git 管理外。PR 対象ではない | ローカル環境で清掃。必要なら `.gitignore` 確認 |
| `apps/` | `README.md` のみ存在 | `互換維持` / `予約領域` | downstream app 用の意図ある予約領域 | README の説明を維持。workspace member にはしない |
| root `tests/` | e2e / db integration / agent guidance tests が存在 | `互換維持` | component tests ではない cross-cutting tests として維持 | README / test guide の説明を継続 |
| Docker / Compose | `koiki_ref_app.asgi:app` を使用 | `正規導線` | 現行起動経路は正規化済み | `app.main:app` へ戻さない |
| docs の `app.main:app` 参照 | 現行 docs では互換導線として説明。履歴 docs に旧導線あり | `正規導線へ置換` / `履歴資料として残す` | 現行手順では `koiki_ref_app.asgi:app` を標準とする | 履歴 docs は必要に応じて注意書きを追加 |
| docs の root `libkoiki/` 参照 | v0.6 docs / backend audit docs / migration docs に多数存在 | `履歴資料として残す` / `正規導線へ置換` | 履歴資料は残すが、現行手順として読める docs は要注意 | docs cleanup PR で対象を分ける |

## 4. 詳細

### 4.1 root `app/`

現状:

```text
app/__init__.py
app/main.py
```

`app/main.py` は次の薄い wrapper である。

```python
"""Compatibility wrapper for the migrated reference application."""

from koiki_ref_app.asgi import app
```

`app/__init__.py` は `components/koiki_ref_app/src` と `components/libkoiki/src` を `sys.path` に追加し、`koiki_ref_app` package path を `app` namespace に接続している。

判断:

- 現行実装の正本ではない
- `app.main:app` 互換を維持するための wrapper として扱う
- Docker / Compose の正規起動先は既に `koiki_ref_app.asgi:app`
- 初回 DM-12 では削除しない

後続対応:

- 互換終了時期を決めたうえで、`app.main:app` が必要な外部利用・運用手順が残っていないか確認する
- 削除する場合は Docker / docs / import / test を横断確認する

### 4.2 root `main.py`

現状:

- root `main.py` は存在しない
- `docs/dev/root-cleanup-plan.ja.md` では、root `main.py` は削除済みと記録されている

判断:

- DM-12 の削除対象ではない
- 旧 docs や履歴資料での参照は、履歴説明として扱う

後続対応:

- 現行 setup / README / Docker docs に `python main.py` や `uvicorn main:app` が戻らないよう確認する

### 4.3 root `libkoiki/`

DM-12 棚卸し時点で Git 管理下に残っていたファイル:

```text
libkoiki/setup.py
```

`libkoiki/setup.py` は旧 package metadata であり、次のように現行 dependency と矛盾する。

- version が `0.6.1`
- `passlib[bcrypt]` を dependency に含む
- 現行 `components/libkoiki/pyproject.toml` / root `pyproject.toml` と別系統の metadata

また、ローカル環境には Git 管理外の生成物が残っている。

```text
libkoiki/__pycache__/
libkoiki/*/__pycache__/
libkoiki/libkoiki.egg-info/
```

判断:

- `libkoiki/setup.py` は削除対象
- 現行正本 `components/libkoiki/` と混同されるリスクが高い
- `passlib[bcrypt]` を含むため、DM-11 後の方針とも矛盾する
- ローカル生成物は Git PR では扱わず、必要に応じて作業環境で清掃する

DM-12-A 実施結果:

- `libkoiki/setup.py` を削除した
- 削除前に `git ls-files libkoiki` で Git 管理対象が `libkoiki/setup.py` のみであることを確認した
- `rg "libkoiki/setup.py|passlib\[bcrypt\]"` で、削除対象以外の `passlib[bcrypt]` 参照が履歴・計画 docs であることを確認した
- root `libkoiki/` 配下のローカル生成物は Git 管理外のため、この PR では削除しない
- unified prod コンテナを build / run し、ブラウザで password login とタスク管理の作成 / 更新が成功することを確認した
- アプリコンテナログで `setup.py` / `libkoiki/setup.py` / `No such file or directory` / `ModuleNotFoundError` / `ImportError` / `Traceback` / `ERROR` / `CRITICAL` が出ていないことを確認した

後続対応:

- ローカル生成物は Git 管理外であることを確認し、必要なら `.gitignore` の対象を確認する

### 4.4 `apps/`

現状:

```text
apps/README.md
```

`apps/README.md` では、`apps/` は downstream 案件固有 backend API 実装の配置先として説明されている。

判断:

- v0.6 由来の残骸ではなく、v0.7 以降の予約領域
- 削除対象ではない
- ただし現時点では実装コードがないため、新規メンバーには「予約領域」と明記する必要がある

後続対応:

- `README.md` と `apps/README.md` の説明を維持する
- `apps/` を root workspace member に含めない方針を維持する

### 4.5 root `tests/`

現状:

```text
tests/e2e/
tests/integration/services/
tests/unit/agent_guidance/
tests/unit/test_hello.py
tests/unit/test_pyjwt_migration.py
```

判断:

- component 所有テストではなく、cross-cutting / e2e / agent guidance tests として維持する
- `components/libkoiki/tests/` と `components/koiki_ref_app/tests/` へ無理に移す対象ではない

後続対応:

- README / test guide で root `tests/` の役割を明確に保つ
- 新規テスト追加時は、component 所有か cross-cutting かを判断する

### 4.6 `app.main:app` 参照

現行 runtime:

- `Dockerfile`
- `Dockerfile.unified`
- `docker-compose*.yml`
- `scripts/start-local-dev.ps1`

これらは `koiki_ref_app.asgi:app` を使っている。

現行 docs:

- `docs/dev/local_setup.md` は `koiki_ref_app.asgi:app` を正式導線、`app.main:app` を互換導線として説明している
- `docs/dev/setup.md` も互換導線として `app.main:app` が残ることを説明している
- `README.md` は root `app/` を compatibility wrapper と明記している

履歴 docs:

- `docs/design_kkfw_0.6.0.md`
- `docs/authentication-api-guide.md`
- `docs/saml/*`
- `docs/dev/v0.7-*`
- `docs/backend-audit/*`

これらには旧 `app` / root `libkoiki` 参照が残る。

判断:

- 現行 docs では `app.main:app` は互換導線として扱われており、許容範囲
- 履歴 docs の旧参照は、履歴資料として残す場合は削除不要
- ただし、現行手順として読める docs に旧導線が残る場合は docs cleanup 対象

後続対応:

- docs cleanup PR では、履歴資料と現行手順を分けて扱う
- 履歴 docs には必要に応じて「v0.6 時点の記録」と明記する

## 5. 後続 PR 候補

### DM-12-A: root `libkoiki/setup.py` 削除

状態: `対応済み`

目的:

- 現行 `components/libkoiki/` と混同される旧 package metadata を削除する
- DM-11 後に不要となった `passlib[bcrypt]` 参照を root legacy metadata から消す

対象:

- `libkoiki/setup.py`

実施結果:

- root `libkoiki/setup.py` を削除した
- root `libkoiki/` に残る Git 管理対象はなくなった
- root `libkoiki/` 配下の `__pycache__` / `libkoiki.egg-info` は Git 管理外 artifact として扱う
- unified prod コンテナ build / run、password login、タスク管理の作成 / 更新で動作影響がないことを確認した
- コンテナログで `libkoiki/setup.py` 削除に起因する import / file missing error がないことを確認した

事前確認:

```powershell
git ls-files libkoiki
rg -n "libkoiki/setup.py|passlib\\[bcrypt\\]" . -S --glob "!**/.git/**" --glob "!**/.venv/**"
uv lock --check
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

### DM-12-B: 現行 docs の旧導線整理

状態: `対応済み`

目的:

- 新規メンバーが現行手順として旧 root `libkoiki/` や `app.main:app` を読まないようにする

候補:

- `docs/authentication-api-guide.md`
- `docs/saml/saml-env-config-guide.md`
- `docs/saml/SAML_MIGRATION_GUIDE.md`
- `docs/saml/saml-certificate-strategies.md`
- `docs/testing/認証系APIテストガイド.md`

方針:

- 履歴資料は残す
- 現行手順として見える箇所には注意書きまたは現行パスを追記する

実施結果:

- `docs/saml/SAML_MIGRATION_GUIDE.md` に、v0.6 系 root `app/` / `libkoiki/` 前提を含む移植資料であることを明記した
- `docs/saml/saml-env-config-guide.md` に、現行 SAML backend 実装は `components/koiki_ref_app/src/koiki_ref_app/` 配下であることを明記し、import 例を `koiki_ref_app.core.saml_config` に更新した
- `docs/saml/saml-certificate-strategies.md` に、現行 SAML backend 実装の正規 path を明記し、コード例を `koiki_ref_app.services.saml_certificate_manager` に更新した
- `docs/testing/認証系APIテストガイド.md` に、現行テスト配置として `components/libkoiki/tests/`、`components/koiki_ref_app/tests/`、root `tests/` の役割を追記した
- `docs/authentication-api-security-fixes.md` に、v0.6 系の対応記録であり、本文中の `libkoiki/...` path は履歴として扱うことを追記した
- `docs/authentication-api-guide.md` は既に現行構成注記があるため、今回の追加修正対象外とした
- 履歴資料の旧 path 本文は大きく書き換えず、現行作業で優先すべき正規導線を注記する方針に留めた

### DM-12-C: `app.main:app` 互換終了判断

状態: `DM-13 後に着手`

目的:

- root `app/` wrapper をいつまで残すか判断する

着手順序:

- `DM-12-B` 完了後、先に `DM-14` として API ownership / sample feature boundary policy を整理する
- `DM-14` 後、`DM-15` として Agent guidance / Skills consistency を整理する
- `DM-15` 後、`DM-13` として v0.7.0 release preparation を実施する
- `DM-13` で version metadata と release docs を整理してから、`app.main:app` 互換終了判断へ進む
- release / versioning と compatibility wrapper の削除判断を同一 PR に混ぜない

事前確認:

```powershell
rg -n "app\.main:app|from app.main import app|uvicorn app\.main|from app\.|import app\." . -S --glob "!**/.git/**" --glob "!**/.venv/**"
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.title)"
uv run --locked python -c "from app.main import app; print(app.title)"
```

削除する場合:

- Docker / docs / external usage の影響を別 PR で確認する
- release note または migration note に互換終了を記載する

### DM-12-D: ローカル artifact 清掃

目的:

- Git 管理外の `libkoiki/__pycache__` / `libkoiki/libkoiki.egg-info` などを作業環境から除去する

注意:

- Git PR では扱わない
- 必要ならユーザー確認後にローカルで削除する
- 削除前に `git status --ignored=matching libkoiki` を確認する

## 6. 実施した確認

```powershell
rg --files app libkoiki apps tests .github docs docker scripts
git ls-files app libkoiki apps tests .github docs docker scripts
rg -n "app\.main|from app|import app|libkoiki/|components/libkoiki|koiki_ref_app|sys.path|PYTHONPATH" . -S
git status --ignored=matching libkoiki
git ls-files libkoiki
```

確認結果:

- root `main.py` は存在しない
- Git 管理下の root `libkoiki/` は `libkoiki/setup.py` のみ
- root `libkoiki/` 配下にローカル生成物はあるが Git 管理外
- Docker / Compose / local dev script は `koiki_ref_app.asgi:app` を使用
- root `app/` は `app.main:app` 互換 wrapper として残存
- `apps/` は downstream 案件固有 backend API 実装の予約領域として説明済み

import 確認:

```powershell
$env:DEBUG='true'
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.title)"
uv run --locked python -c "from app.main import app; print(app.title)"
```

結果:

```text
KOIKI Framework
KOIKI Framework
```

## 7. DM-12 初回 PR の結論

初回 DM-12 PR では、削除や entrypoint 変更は行わない。

この棚卸しにより、DM-12-A / DM-12-B 実施後に残る後続 PR 候補は次である。

1. `DM-14`: API ownership / sample feature boundary policy
2. `DM-15`: Agent guidance / Skills consistency review
3. `DM-13`: v0.7.0 release preparation
4. `DM-12-C`: `app.main:app` 互換終了判断

root `libkoiki/setup.py` は、現行 dependency と矛盾し、`passlib[bcrypt]` を含むため、DM-12-A で先行削除した。
現行 docs の旧導線整理は、DM-12-B で履歴資料を残しつつ正規導線注記を追加した。
