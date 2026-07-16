# Task 1-1: Existing backend Skills and shared guidance alignment

## 目的

既存 backend Skills と共通 agent guidance を、業務アプリ開発者が backend API 変更時の frontend contract を見落とさない形へ改定する。

## 事前条件

- Task 0-1 と Task 0-2 が完了している。

## 対象

- `koiki-project-overview`
- `koiki-business-app-feature-work`
- `koiki-libkoiki-feature-work`
- `koiki-refapp-feature-work`
- `koiki-auth-security`
- `koiki-testing`
- `docs/agent/*.md`
- `docs/agent/skills/future-role-alignment.md`
- `.claude/skills/`
- `.github/copilot-instructions.md` と `.github/instructions/`
- `AGENTS.md`

## 実施手順

1. 各 backend Skill に、変更対象の API schema、auth、config、migration、frontend contract、test への影響確認を必要な範囲で追加する。
2. `koiki-business-app-feature-work` では、`apps/` が backend 専用であることを維持し、frontend の配置先と読める記述を置かない。
3. `koiki-auth-security` では、backend-owned Cookie/CSRF と frontend の利用責務を明確にする。
4. `koiki-testing` では、backend API contract と frontend contract の unit / integration / frontend test 境界を明確にする。
5. `future-role-alignment.md` から `apps/<project>/frontend/` を前提にした将来案を削除または現行方針に更新する。
6. 更新した Skill の metadata、Claude wrapper、Codex 導線、Copilot guidance、catalog、contract test を同じ change window で整合させる。

## 完了条件

- 業務 backend API の変更時に frontend contract 確認の導線がある。
- `apps/` と root `frontend/` の配置境界が全 guidance で一貫している。
- 既存 backend Skill の役割重複が増えていない。
- Codex、Claude Code、GitHub Copilot の guidance が同じ API ownership と frontend contract を示す。

## 実施結果

完了（2026-07-11）。

### 更新内容

- `docs/agent/` の boundaries、architecture、libkoiki、reference app、auth-security、testing、README に、backend API 変更時の frontend contract 確認を追加した。
  - 確認対象は schema、status/error、authorization、Cookie/CSRF、public config、frontend cache / test である。
- 既存 backend Skills を更新した。
  - `koiki-business-app-feature-work`、`koiki-refapp-feature-work`、`koiki-libkoiki-feature-work` は、frontend contract 影響と consumer validation を確認するようにした。
  - `koiki-auth-security` は Cookie session / CSRF と Bearer client の境界、browser storage 非保持、browser integration coverage を明記した。
  - `koiki-testing` は backend enforcement test と frontend transport / cache / UI test の責務分離を明記した。
  - `koiki-project-overview` は root `frontend/` を確認し、`apps/` を frontend placement としない判断を明記した。
- `future-role-alignment.md` を現行境界へ更新した。
  - `apps/<project-slug>/frontend/` を前提にする案を削除した。
  - root `frontend/` を起点とする frontend adoption と、`apps/` の backend-only 境界を明記した。
- Codex、Claude Code、GitHub Copilot の導線を整合した。
  - `AGENTS.md` に root frontend / browser contract の確認導線を追加した。
  - Claude Code wrapper の description を canonical Skill の frontend contract 範囲へ整合した。wrapper 本体は canonical Skill を参照する thin adapter のまま維持した。
  - Copilot global instruction を補強し、root `frontend/` 専用の `.github/instructions/frontend.instructions.md` を追加した。
- `tests/unit/agent_guidance/test_skill_catalog.py` を拡張し、既存 Skill の frontend contract guidance と、Codex / Copilot / shared agent docs の root frontend・`apps/` backend-only 境界を contract test で確認するようにした。

### Catalog の扱い

`prompt_cases.yaml` はこのタスクでは変更していない。現時点では frontend-only task が overview へ routing する現行 catalog が正しい。Task 2-1 で `koiki-frontend-work` を追加する同一 change window に、catalog と smoke script fixture を更新する。

## Validation

- `DEBUG=False uv run --locked pytest tests/unit/agent_guidance/`
  - 17 passed in 1.10s
- `git diff --check`
  - 成功
