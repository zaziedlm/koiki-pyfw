# 開発環境セットアップガイド

## ローカル開発環境のセットアップ

このプロジェクトでは、`components/libkoiki` フレームワークと
`components/koiki_ref_app` 参照アプリを root workspace から同時に開発します。

標準の依存管理と実行コマンドは `uv` です。
推奨 Python バージョンは **3.11.7** です。

### 0. Python 3.11.7 のインストール

```powershell
pyenv install 3.11.7
pyenv local 3.11.7
```

### 1. uv の確認

```powershell
uv --version
```

未導入の場合は、uv の公式手順に従ってインストールしてください。

### 2. 依存関係の同期

root で実行します。

```powershell
uv sync
```

用途別の依存グループを明示する場合:

```powershell
uv sync --group test
uv sync --group security
```

CI と同じ lockfile 固定の確認をしたい場合:

```powershell
uv sync --locked
```

ローカルで開発・テスト用の依存まで lockfile に合わせる場合:

```powershell
uv sync --locked --group dev --group test
```

`pip-audit` や `bandit` などのセキュリティ検証も実行する場合:

```powershell
uv sync --locked --group dev --group test --group security
```

### 3. ローカル component の取り込み

追加の `pip install -e` は不要です。

root `pyproject.toml` の `tool.uv.workspace` と `tool.uv.sources` により、
次の component は workspace package として扱われます。

- `components/libkoiki`
- `components/koiki_ref_app`

### 4. アプリケーションの実行

正式な参照アプリ導線:

```powershell
uv run --locked uvicorn koiki_ref_app.asgi:app --reload
```

互換導線:

```powershell
uv run --locked uvicorn app.main:app --reload
```

補足:

- 実ソースの正本は `components/koiki_ref_app/src/koiki_ref_app/` にあります
- `app.main:app` は互換 wrapper です。新規起動手順では `koiki_ref_app.asgi:app` を使います。
- `koiki_ref_app.asgi:app` が新しい ASGI import path です

### 5. テスト実行

```powershell
uv run pytest
```

collect-only:

```powershell
uv run pytest --collect-only
```

coverage 付きの代表コマンド:

```powershell
uv run pytest --cov=koiki_ref_app --cov=libkoiki --cov-report=term-missing `
  components/libkoiki/tests/ `
  components/koiki_ref_app/tests/ `
  tests/unit/agent_guidance/ `
  tests/integration/services/
```

### 6. パッケージング

通常のローカル開発では package build は不要です。

`libkoiki` の配布物を確認する場合は、`components/libkoiki` の
`pyproject.toml` を対象に PEP 517 build を行います。

```powershell
uv run --with build python -m build components/libkoiki
```

この経路は日常開発ではなく、配布物確認時の例外的な手順です。
