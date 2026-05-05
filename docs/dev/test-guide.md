# Test Guide

pytest は root workspace から `uv run` で実行します。

```bash
uv run pytest
```

収集確認:

```bash
uv run pytest --collect-only
```

代表的な component / integration 実行:

```bash
uv run pytest \
  components/libkoiki/tests/ \
  components/koiki_ref_app/tests/ \
  tests/unit/agent_guidance/ \
  tests/integration/services/
```

VSCode の Test Explorer も同じ軽量範囲を既定にしています。
`.vscode/settings.json` の `python.testing.pytestArgs` は、component tests と root 側の agent / service tests を収集し、`db_integration` は除外します。

同じ条件を CLI で確認する場合:

```bash
uv run --locked pytest --collect-only \
  components/libkoiki/tests \
  tests/unit/agent_guidance \
  components/koiki_ref_app/tests \
  tests/integration/services \
  -m "not db_integration"
```

CI と同じ lockfile 固定の前提で確認する場合:

```bash
uv run --locked pytest --collect-only
```

live PostgreSQL を使う `db_integration` は標準 CI から分離しています。
詳細は `docs/dev/db-integration-testing.md` を参照してください。
