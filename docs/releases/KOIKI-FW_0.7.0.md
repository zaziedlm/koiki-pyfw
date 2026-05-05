# KOIKI-FW v0.7.0 Release Notes

## 概要

KOIKI-FW v0.7.0 は、v0.6 系で整備した認証・監査・Todo sample 基盤を維持しながら、現行開発の正規構成を `components/libkoiki/` と `components/koiki_ref_app/` へ整理した release preparation 版です。

この release では、runtime / package metadata を `0.7.0` に揃え、開発者向け設計文書、README、agent guidance、API ownership 方針を v0.7 構成へ合わせます。

## 主要変更点

### v0.7 backend structure

- reusable framework layer を `components/libkoiki/` に整理
- reference application backend layer を `components/koiki_ref_app/` に整理
- root `app/` を `app.main:app` compatibility wrapper として限定
- `apps/` を downstream / customer-specific backend API の予約領域として明確化
- root `libkoiki/setup.py` など v0.6 由来の混同要素を整理済み

### API ownership policy

- framework API は reusable capability または明示された starter/sample capability に限定
- reference app API は current project の workflow / integration / UI-facing behavior を所有
- downstream customer-specific API は `apps/` から開始
- Todo API は `libkoiki` の framework sample / starter capability として暫定維持
- Todo API を新規 business API の `libkoiki` 配置前例として扱わない方針を明文化

### Security and dependency maintenance

- `passlib` 依存を runtime dependency から削除し、password hashing backend を `bcrypt` 直利用へ移行
- SAML metadata XML parser を hardening
- `pip-audit` / Bandit の検出結果と false positive 方針を整理
- Pydantic v2 deprecation 対応を進め、schema / settings / `.dict()` 周辺の warning を削減
- release final check で frontend runtime dependency の `next` と `axios` を更新し、production audit の critical / high を解消

### Developer experience

- `uv` / component package / current test layout を現行導線として整理
- Alembic 実行 path と DB host 使い分けを明確化
- VSCode pytest discovery を current component test layout に整合
- `docs/design_kkfw_0.7.0.md` を新規作成し、開発者向け v0.7 アーキテクチャ正本を追加
- README の v0.6 強調を v0.7 現行説明へ更新

### Agent guidance

- `docs/agent/` と `docs/agent/skills/` を shared guidance / canonical Agent Skills として整理
- `.claude/skills/` は canonical skill への thin wrapper として維持
- GitHub Copilot instructions に API ownership / layer boundary を反映
- prompt catalog / smoke checklist / repository-side contract tests を拡充

## Compatibility Notes

- `koiki_ref_app.asgi:app` が標準 ASGI entrypoint です。
- `app.main:app` は互換 wrapper として v0.7.0 時点では維持します。
- root `app/` へ新規実装は追加しません。
- `app.main:app` 互換終了は v0.7.0 では実施せず、v0.7.x 以降で外部利用状況を確認して再判断します。
- `docs/design_kkfw_0.6.0.md` と v0.6 release docs は履歴資料として維持します。

## Migration Notes

v0.6 系の root `app/` / root `libkoiki/` 前提で作業していた場合は、v0.7.0 では次を優先してください。

- framework changes: `components/libkoiki/`
- reference app backend changes: `components/koiki_ref_app/`
- downstream customer-specific changes: `apps/`
- ASGI startup: `koiki_ref_app.asgi:app`
- Alembic config: `components/koiki_ref_app/alembic.ini`

## Validation

Release preparation validation:

```powershell
uv lock --check
uv run --locked python -c "import libkoiki; print(libkoiki.__version__)"
uv run --locked python -c "from koiki_ref_app.asgi import app; print(app.version)"
uv run --locked pytest --collect-only components/libkoiki/tests tests/unit/agent_guidance components/koiki_ref_app/tests tests/integration/services -m "not db_integration"
```

Optional container validation:

```powershell
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
```

Confirm:

- container health
- password login
- Todo list / create / update / completion toggle / delete
- backend logs without import/runtime errors
- `/health` reports version `0.7.0`

Final release check evidence is tracked in:

- `docs/dev/v0.7.0-final-release-check-plan.ja.md`
- `docs/dev/v0.7.0-final-release-check-results.ja.md`

## Related Documents

- `docs/design_kkfw_0.7.0.md`
- `docs/dev/deferred-maintenance-tasks.ja.md`
- `docs/dev/v0.7.0-final-release-check-plan.ja.md`
- `docs/dev/v0.7.0-final-release-check-results.ja.md`
- `docs/dev/dm12-legacy-compatibility-inventory.ja.md`
- `docs/dev/dm14-api-ownership-boundary-policy.ja.md`
- `docs/dev/dm15-agent-guidance-skills-consistency.ja.md`
- `docs/agent/`
