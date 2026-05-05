# 先送り保守事項 対応プラン

最終更新: 2026-05-02

## 1. 目的

本書は、`uv` 移行前後から先送りされてきた warning、設定、DB/Alembic、IDE 実行導線、security follow-up を横断的に整理し、対応方針を明文化する。

既存の `docs/dev/v0.7-stage2-uv-follow-up-plan.ja.md` は、依存管理を Poetry から `uv` へ切り替える follow-up を主対象とする。
本書は、その後に残った保守性・将来互換性・実行導線の課題を対象とする。

## 2. 今回確認した現状

確認時点のブランチ:

- `topic/deferred-maintenance-plan`

確認したコマンド:

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'; uv lock --check
$env:UV_CACHE_DIR='.uv-cache-codex'; $env:DEBUG='true'; uv run --locked python -c "import libkoiki, koiki_ref_app; from libkoiki.core.config import Settings; print(libkoiki.__name__, koiki_ref_app.__name__, Settings.__name__)"
$env:UV_CACHE_DIR='.uv-cache-codex'; $env:DEBUG='true'; uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

結果:

- `uv lock --check` は成功した
- `libkoiki` / `koiki_ref_app` / `Settings` の import は成功した
- collect-only は `203 selected / 37 deselected` まで成功した
- 既定の user cache `C:\Users\kataoka\AppData\Local\uv\cache` では権限エラーが出たため、確認時は `UV_CACHE_DIR=.uv-cache-codex` を指定した

観測 warning:

- `LoginAttemptModel` の SQLAlchemy `SAWarning`
- `libkoiki.core.config.Settings` の Pydantic v1 style `@validator` deprecation
- `koiki_ref_app.schemas.kkbiz.business_clock` の Pydantic v1 style `@validator` deprecation
- Pydantic class-based `Config` deprecation
- 一部 `.dict()` 利用による Pydantic v2 deprecation

## 3. 重要度別の判断

### P0: 設定生成バグ候補

`components/libkoiki/src/libkoiki/core/config.py` では、`DATABASE_URL` 用 validator が decorator として機能していない。

該当箇所:

```python
raise ValueError(v)    @validator("DATABASE_URL", pre=True)
```

この行は Python の `@` 演算子として解釈されるため、`DATABASE_URL` 未指定時の組み立て処理が validator として登録されない。
実際に `Settings(_env_file=None, POSTGRES_...指定)` で確認したところ、`DATABASE_URL` は `None` のままだった。

これは warning ではなく、設定生成の実動作に関わるため最優先で扱う。

### P1: ORM timestamp alias の明確化

`components/libkoiki/src/libkoiki/models/login_attempt.py` では、`attempted_at` と `created_at` を同じ `Column` オブジェクトに割り当てている。

```python
attempted_at = Column(...)
created_at = attempted_at
```

この実装意図は、以下を両立しようとしたものと推定する。

- 共通 `Base` の `created_at` 契約をなるべく満たしたい
- ログイン試行履歴としては `created_at` より `attempted_at` を正式な業務語彙にしたい
- 既存 migration の DB カラム名 `attempted_at` を変えたくない
- repository / service / test の既存利用箇所を極力変えたくない

この意図を尊重し、他箇所の変更を最小化する場合は `sqlalchemy.orm.synonym("attempted_at")` を使う。

```python
from sqlalchemy.orm import relationship, synonym

attempted_at = Column(...)
created_at = synonym("attempted_at")
updated_at = None
```

これにより、DB カラム名と正式利用名は `attempted_at` のまま維持しつつ、`created_at` 互換も残せる。
Migration 変更、repository 変更、service 変更は原則不要とする。

### P2: Pydantic v2 移行

Pydantic v2 deprecation は、`@validator` だけではなく以下も対象に含めて整理する。

- `@validator` から `@field_validator` / `@model_validator` への移行
- `class Config` から `model_config = ConfigDict(...)` への移行
- `.dict()` から `.model_dump()` への移行

ただし、影響範囲が広いため、P0/P1 と同じ変更単位に混ぜない。
まず `Settings` の実動作修正を優先し、その後 schema / service / repository に範囲を広げる。

### P3: Alembic / DB 実行導線

現行の Alembic 正規導線は以下。

```powershell
uv run --locked alembic -c components/koiki_ref_app/alembic.ini upgrade head
```

`components/koiki_ref_app/alembic.ini` の `script_location` は component root 基準で成立している。
一方で、ini 内のデフォルト `sqlalchemy.url` は `@db` を含む Docker 内向けの値である。

`env.py` が `settings.DATABASE_URL` で上書きする前提のため、通常の標準導線では問題になりにくい。
ただし、環境変数が欠落した実行、素の Alembic 実行、ローカルから `db` host を引く実行では hostname 解決失敗につながる。

対策は次のいずれかを検討する。

- docs / scripts で `-c components/koiki_ref_app/alembic.ini` と `DATABASE_URL=...@localhost...` を明示する
- `alembic.ini` のデフォルト URL を事故りにくい dummy または localhost に寄せる
- env.py のエラーメッセージを、標準実行コマンドと必要環境変数が分かる形へ改善する

### P4: IDE / local 実行導線

`.vscode/settings.json` の pytest args は現在 `tests` のみを対象としている。
CI は以下も対象に含めている。

- `components/libkoiki/tests`
- `components/koiki_ref_app/tests`
- `tests/unit/agent_guidance`
- `tests/integration/services`

IDE での検出範囲と CI の検出範囲がずれるため、後続で `.vscode/settings.json` の `python.testing.pytestArgs` を現行構成に合わせるか、IDE 向けの軽量 test profile を明示する。

### P5: Security follow-up

`docs/dev/v0.7-stage2-uv-follow-up-plan.ja.md` に記録済みの security follow-up は、依存管理移行とは別に残っている。

対象:

- `pip-audit` で検出された依存脆弱性の修正
- `bandit` false positive の抑制方針整理
- `components/koiki_ref_app/src/koiki_ref_app/services/saml_metadata_loader.py` の XML parser hardening
- audit report 生成物の `.gitignore` 対象化要否

SAML metadata は外部 XML を扱うため、`xml.etree.ElementTree` から `defusedxml` 系への置換を検討する。

## 4. 推奨対応順

1. `Settings` の `DATABASE_URL` 組み立てバグを修正する
2. `LoginAttemptModel` の `created_at` alias を `synonym("attempted_at")` に置き換える
3. Pydantic v2 deprecation を段階的に解消する
4. Alembic / DB 実行導線を明文化・補強する
5. `.vscode` / local pytest 導線を CI と整合させる
6. security follow-up を個別に処理する

## 5. 対応単位の原則

- P0 と P1 は小さく分けて実装する
- migration を伴わない修正を優先する
- `LoginAttemptModel` では DB カラム名 `attempted_at` を維持する
- `LoginAttemptModel` では既存の repository / service / test 呼び出し変更を原則避ける
- Pydantic v2 sweep は影響範囲が広いため、設定修正と分離する
- Alembic / DB 導線は、Docker 内とローカル実行で host 名が異なる前提を明示する

## 6. 検証方針

最小検証:

```powershell
$env:UV_CACHE_DIR='.uv-cache-codex'
$env:DEBUG='true'
uv lock --check
uv run --locked python -c "import libkoiki, koiki_ref_app; from libkoiki.core.config import Settings; print(Settings.__name__)"
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

`Settings` 修正時:

- `DATABASE_URL` 明示指定時にその値が優先されること
- `DATABASE_URL` 未指定時に `POSTGRES_*` から構築されること
- `BACKEND_CORS_ORIGINS` の文字列入力が list 化されること
- import error が発生しないこと

`LoginAttemptModel` 修正時:

- model import 時に `SAWarning` が再発しないこと
- `attempted_at` が従来どおり利用できること
- `created_at` 互換が必要最小限維持されること
- migration 差分が不要であること

Pydantic v2 sweep 時:

- deprecation warning の件数が減ること
- schema serialization / validation の既存挙動が維持されること
- auth / SSO / SAML 関連の validation を壊さないこと

Alembic / DB 導線確認:

```powershell
$env:DATABASE_URL='postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db'
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
```

DB コンテナがない環境では、DB 接続を要する検証はスキップし、コマンドと環境変数の文書整合を確認する。

## 7. 許容 warning と NG 条件

当面の許容 warning:

- `LoginAttemptModel` の SQLAlchemy warning
- Pydantic v1 validator / config / `.dict()` deprecation

ただし、上記は本計画の解消対象であり、恒久的に許容するものではない。

NG 条件:

- import error
- lock mismatch
- `poetry` 不在による実行失敗
- Alembic path 不一致
- ローカル実行時の `db` hostname 解決失敗
- `DATABASE_URL` 未指定時の設定生成不備を見落とすこと

