# KOIKI-FW root ファイル整理計画

## 目的

`v0.7` のディレクトリ再編により、framework 層は `components/libkoiki`、reference app 層は `components/koiki_ref_app` へ分離された。

一方で、リポジトリ root には過去の運用文書、補助スクリプト、履歴資料、生成物が混在している。

この文書は、root 直下を「リポジトリ入口として必要なもの」に絞り、文書・スクリプト・履歴資料・互換入口を段階的に整理するための計画である。

## 現在の基準

現行の標準経路:

- 依存同期: `uv sync --locked`
- 実行: `uv run --locked ...`
- lockfile 正本: `uv.lock`
- reusable framework 正本: `components/libkoiki`
- reference app 正本: `components/koiki_ref_app`
- application ASGI 正本: `koiki_ref_app.asgi:app`
- root `app/`: 互換 wrapper
- Docker / Compose: root `Dockerfile*` と `docker-compose*.yml`

root に残すべきもの:

- repository entrypoint docs
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
- package / dependency metadata
  - `pyproject.toml`
  - `uv.lock`
- container entry files
  - `Dockerfile`
  - `Dockerfile.unified`
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `docker-compose.unified.yml`
  - `docker-entrypoint.sh`
- repo-level config
  - `.editorconfig`
  - `.gitattributes`
  - `.gitignore`
  - `.python-version-sample`
  - `.env.example`
  - `.env.saml.example`
  - `.env.ci`
  - `.env.test`

root から整理したいもの:

- 現行 docs / history docs として `docs/` 配下へ寄せる Markdown
- 運用・検証スクリプトとして `scripts/` または `ops/scripts/` へ寄せる shell / PowerShell
- 互換目的が薄くなった root `main.py`
- local generated artifacts / backup files

## 分類ルール

### A. root に残す入口ファイル

リポジトリ利用者が最初に見る、または tool / platform が root にあることを期待するファイル。

例:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `pyproject.toml`
- `uv.lock`
- `Dockerfile*`
- `docker-compose*.yml`
- root config files

### B. docs 配下へ移す文書

現行運用文書または履歴資料として価値はあるが、root に置く必要は薄い Markdown。

移動時は、README や関連 docs のリンクを更新する。

### C. scripts / ops 配下へ移す補助スクリプト

root から実行できる利便性より、責務配置の明確さを優先できるスクリプト。

移動時は、README、docs、Makefile、他スクリプト内の参照を更新する。

### D. 削除または Git 管理外へ戻すファイル

生成物、ローカルバックアップ、または現行標準経路から外れた互換入口。

削除前に `rg` と `git ls-files` で参照と管理状態を確認する。

## Root Cleanup RC-1: Markdown 文書の配置整理

対象候補:

- `docs/testing/QUICK_TEST_GUIDE.md`
- `docs/archive/README-deploy.md`
- `docs/archive/ENTERPRISE_DEPENDENCY_STRATEGY.md`
- `docs/releases/KOIKI-FW_0.6.0.md`
- `docs/releases/KOIKI-FW_0.6.1.md`
- `docs/security/SECURITY_AUDIT_COMMANDS.md`
- `docs/testing/認証系APIテストガイド.md`
- `docs/dev/agent-skill-checklist.md`

推奨方針:

- `QUICK_TEST_GUIDE.md`
  - `docs/testing/` へ移動した
  - root `README.md` のリンクを更新する
- `README-deploy.md`
  - 履歴資料として `docs/archive/` へ移動した
  - 現行 Docker guide は `DOCKER_SETUP.md` を優先する
- `ENTERPRISE_DEPENDENCY_STRATEGY.md`
  - 履歴資料として `docs/archive/` へ移動した
  - 現行 security audit は `docs/security/SECURITY_AUDIT_COMMANDS.md` を参照する
- `KOIKI-FW_0.6.0.md` / `KOIKI-FW_0.6.1.md`
  - release note として `docs/releases/` へ移動した
- `SECURITY_AUDIT_COMMANDS.md`
  - 現行 runbook として `docs/security/` へ移動した
- `認証系APIテストガイド.md`
  - `docs/testing/` へ移動した
- `agent-skill-checklist.md`
  - agent guidance の作業成果物として `docs/dev/` 配下へ移動した

完了条件:

- root に残る Markdown が entrypoint docs として説明できる
- 移動した文書へのリンクが壊れていない
- 履歴資料と現行 runbook の区別が明確である

実施結果:

- `QUICK_TEST_GUIDE.md` を `docs/testing/QUICK_TEST_GUIDE.md` へ移動した
- `認証系APIテストガイド.md` を `docs/testing/認証系APIテストガイド.md` へ移動した
- `README-deploy.md` を `docs/archive/README-deploy.md` へ移動した
- `ENTERPRISE_DEPENDENCY_STRATEGY.md` を `docs/archive/ENTERPRISE_DEPENDENCY_STRATEGY.md` へ移動した
- `KOIKI-FW_0.6.0.md` と `KOIKI-FW_0.6.1.md` を `docs/releases/` へ移動した
- `SECURITY_AUDIT_COMMANDS.md` を `docs/security/SECURITY_AUDIT_COMMANDS.md` へ移動した
- `agent-skill-checklist.md` を `docs/dev/agent-skill-checklist.md` へ移動した
- `README.md`、関連 docs、follow-up 計画文書内の参照を新 path へ更新した

検証結果:

- root に残る Markdown は `AGENTS.md`、`CLAUDE.md`、`DOCKER_SETUP.md`、`README.md` のみ
- 旧ファイル名の残存は、移動先 path、履歴・計画文書、または検証コマンド内の検索語に限定されている

状態:

- `完了`

検証コマンド:

```powershell
Get-ChildItem -File *.md | Select-Object -ExpandProperty Name
rg -n "QUICK_TEST_GUIDE|README-deploy|ENTERPRISE_DEPENDENCY_STRATEGY|KOIKI-FW_0\.6|SECURITY_AUDIT_COMMANDS|認証系APIテストガイド|agent-skill-checklist" README.md docs ops scripts .github
```

## Root Cleanup RC-2: root スクリプトの配置整理

対象候補:

- `run_security_test.sh`
- `test_csrf.sh`
- `start-local-dev.ps1`
- `start-docker.ps1`
- `start-docker.sh`

推奨方針:

- `run_security_test.sh`
  - root 版は削除し、既存の `ops/scripts/run_tests.sh` を推奨入口にする
  - `ops/scripts/run_security_test.sh` は統合テスト実体として維持する
- `test_csrf.sh`
  - `ops/scripts/` または `scripts/` へ移動する
  - `python main.py` 前提の案内を `uv run --locked uvicorn koiki_ref_app.asgi:app ...` へ更新する
- `start-local-dev.ps1`
  - `scripts/` へ移動する候補
  - 起動先は `koiki_ref_app.asgi:app` に更新する
- `start-docker.ps1` / `start-docker.sh`
  - 頻繁に使う Docker entry helper として root 維持も許容
  - 移動する場合は `DOCKER_SETUP.md` と README の参照更新が必要

完了条件:

- root に残る shell / PowerShell が entrypoint helper として説明できる
- 移動した script の参照が README / docs / Makefile / scripts で更新されている
- `app.main:app` や `python main.py` を新規推奨起動経路として提示していない

検証コマンド:

```powershell
Get-ChildItem -File *.sh,*.ps1 | Select-Object -ExpandProperty Name
rg -n "run_security_test\.sh|test_csrf\.sh|start-local-dev\.ps1|start-docker\.ps1|start-docker\.sh|python main\.py|app\.main:app" README.md docs ops scripts *.sh *.ps1
```

実施結果:

- root `run_security_test.sh` を削除し、利用者向けの推奨入口を `./ops/scripts/run_tests.sh` に統一した
- `test_csrf.sh` を `scripts/test_csrf.sh` へ移動した
- `start-local-dev.ps1` を `scripts/start-local-dev.ps1` へ移動した
- `scripts/start-local-dev.ps1` の起動先を `uv run --locked uvicorn koiki_ref_app.asgi:app ...` へ更新した
- `scripts/test_csrf.sh` と `ops/tests/test_csrf_validation.py` の `python main.py` 案内を現行 ASGI 起動コマンドへ更新した
- `README.md`、`docs/testing/QUICK_TEST_GUIDE.md`、`ops/README.md`、`docs/csrf-testing-guide.md` の script path を更新した
- `start-docker.ps1` / `start-docker.sh` / `docker-entrypoint.sh` は root entry helper として維持した

検証結果:

- root に残る shell / PowerShell は `docker-entrypoint.sh`、`start-docker.sh`、`start-docker.ps1` のみ
- `run_security_test.sh` の残存参照は `ops/scripts/run_security_test.sh` の実体、または計画文書内の履歴説明に限定されている
- `test_csrf.sh` / `start-local-dev.ps1` の利用者向け参照は `scripts/` 配下へ更新済み

状態:

- `完了`

## Root Cleanup RC-3: root `main.py` の扱い整理

対象:

- `main.py`
- `app/main.py`
- `app/__init__.py`

現状:

- 現行 ASGI 正本は `koiki_ref_app.asgi:app`
- root `main.py` は `app.main:app` 互換導線をさらに包む補助入口になっている
- Dockerfile は root `main.py` を copy しているが、CMD は `koiki_ref_app.asgi:app` を使っている
- 業務アプリ固有 API の composition は `docs/dev/apps-plugin-composition-plan.ja.md` で別タスクとして扱う

推奨方針:

1. `python main.py` を案内している docs / scripts を更新する
2. Dockerfile の `COPY ./main.py ./` が不要なら削除する
3. root `main.py` を削除するか、残す場合は `koiki_ref_app.asgi:app` への薄い legacy convenience entrypoint にする
4. `app/main.py` は `app.main:app` 互換が必要な期間だけ薄い wrapper として残す

完了条件:

- root `main.py` の必要性が説明できる
- 削除する場合、`python main.py` 参照が現行手順から消えている
- 残す場合、`app.main:app` ではなく `koiki_ref_app.asgi:app` 標準へ誘導している

検証コマンド:

```powershell
rg -n "python main\.py|uvicorn main:app|from main import app|import main|COPY \./main.py|app\.main:app|koiki_ref_app\.asgi:app" --glob "!**/.git/**" --glob "!**/.venv/**" .
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.title)"
```

## Root Cleanup RC-4: 生成物 / local artifact の整理

対象候補:

- `.coverage`
- `.env.backup`
- `agent-skill-evaluation.json`
- `agent-skill-results.json`
- `.pytest_cache/`
- `.venv/`

推奨方針:

- `.coverage`
  - Git 管理されていれば削除し、`.gitignore` 対象であることを確認する
- `.env.backup`
  - ローカルバックアップであれば削除する
- `agent-skill-evaluation.json` / `agent-skill-results.json`
  - 作業成果物として残す必要があれば `docs/dev/` 配下へ移動する
  - 再生成可能な評価出力なら Git 管理から外す
- `.pytest_cache/` / `.venv/`
  - Git 管理対象ではないことを確認する

完了条件:

- root に生成物が Git 管理対象として残っていない
- local artifact の ignore ルールが説明できる

検証コマンド:

```powershell
git ls-files .coverage .env.backup agent-skill-evaluation.json agent-skill-results.json .pytest_cache .venv
git status --short
```

## 推奨実行順

1. RC-1: Markdown 文書の配置整理
2. RC-2: root スクリプトの配置整理
3. RC-3: root `main.py` の扱い整理
4. RC-4: 生成物 / local artifact の整理

## 注意事項

- 移動は `git mv` を使い、履歴を追いやすくする
- 移動後は `rg` で旧 path 参照を確認する
- root からの利便性だけを理由にファイルを残す場合は、README で入口として明示する
- 履歴文書は削除よりも `docs/archive/` または `docs/releases/` へ移すことを優先する
- Docker / CI / local setup の標準起動は `koiki_ref_app.asgi:app` に統一する
