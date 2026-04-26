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

CI と同じ lockfile 固定の前提で確認する場合:

```bash
uv run --locked pytest --collect-only
```

live PostgreSQL を使う `db_integration` は標準 CI から分離しています。
詳細は `docs/dev/db-integration-testing.md` を参照してください。
