# Task 0-1: Skill catalog / validation inventory

## 目的

現行 Agent Skills の構成、発見導線、検証導線を棚卸しし、後続の改定範囲を確定する。

## 対象

- `docs/agent/skills/`
- 各 Skill の `agents/openai.yaml` と `references/`
- `.claude/skills/`
- `.github/copilot-instructions.md` と `.github/instructions/`
- `AGENTS.md`
- `docs/agent/skills/testing-plan.md`
- prompt catalog と Agent Skills contract test

## 実施手順

1. 既存 Skill ごとに、対象利用者、起動条件、責務、Read Next、metadata、Claude wrapper、Copilot guidance、Codex 導線、テストを一覧化する。
2. `koiki-project-overview`、`koiki-business-app-feature-work`、`koiki-auth-security`、`koiki-testing` を優先して、業務アプリ開発者の task routing を確認する。
3. `koiki-libkoiki-feature-work` と `koiki-refapp-feature-work` は、業務アプリ側が変更してよい境界を説明できるか確認する。
4. `future-role-alignment.md` の将来案と `CONTEXT.md` の確定用語に矛盾がないか確認する。
5. Codex、Claude Code、GitHub Copilot のいずれかで task routing や用語が乖離する箇所を記録する。
6. metadata / wrapper / Copilot guidance / catalog / test の更新が必要な箇所を記録する。

## 完了条件

- 既存 Skill の構成と検証導線が一覧化されている。
- `apps/` が backend 専用であることと矛盾する将来案が特定されている。
- 後続タスクで更新するファイル群が明確である。
- 3つの agent surface ごとの discovery / instruction 導線が記録されている。

## 実施結果

完了（2026-07-11）。

### 1. Canonical Skill inventory

| Skill | 主な対象・責務 | metadata / reference | frontend contract の現状 |
| --- | --- | --- | --- |
| `koiki-project-overview` | 変更レイヤの分類と後続 Skill への routing | `agents/openai.yaml`、reference なし | `frontend/` を分類対象に含むが、frontend 専用 Skill がない前提で詳細な routing はない。 |
| `koiki-business-app-feature-work` | `apps/` の業務固有 backend API / ASGI composition | metadata、`business-app-patterns.md` | workflow に frontend contract 確認が1項目ある。`apps/` は backend 専用として明確。 |
| `koiki-refapp-feature-work` | `components/koiki_ref_app/` の reference app backend | metadata、`app-extension-patterns.md` | workflow に frontend contract 確認が1項目ある。具体的な SPA contract は未記載。 |
| `koiki-libkoiki-feature-work` | `components/libkoiki/` の reusable / sample backend | metadata、`framework-patterns.md` | app-facing behavior の確認に留まり、frontend contract の確認は未記載。 |
| `koiki-auth-security` | auth / RBAC / token / SSO / SAML | metadata、`auth-security-reference.md` | browser flow を対象に含むが、backend-owned Cookie session / CSRF contract の明示が不足する。 |
| `koiki-testing` | test scope / validation / CI scope | metadata、reference なし | description と対象が backend test 中心で、frontend test と backend/frontend contract の境界は未記載。 |

全 canonical Skill は `SKILL.md` と `agents/openai.yaml` を持つ。`koiki-project-overview` と `koiki-testing` には Skill-local reference がないが、共通 `docs/agent/` を Read Next としている。

### 2. Agent surface inventory

| Agent surface | 現行導線 | 確認結果 |
| --- | --- | --- |
| Codex | root `AGENTS.md` → `docs/agent/` → `docs/agent/skills/` | 共通 guidance と canonical Skill の入口はある。Skill ごとの Codex adapter / routing contract はない。 |
| Claude Code | `.claude/skills/<skill>/SKILL.md` | `koiki-*` の6 wrapper は canonical Skill を `@docs/agent/skills/.../SKILL.md` で参照する thin adapter。`grill-with-docs` は別の repository-local skill であり canonical catalog の対象外。 |
| GitHub Copilot | `.github/copilot-instructions.md` と `.github/instructions/*.instructions.md` | API ownership と backend path guidance はあるが、canonical Skill の参照・Skill routing・root `frontend/` 専用 instruction はない。 |

### 3. Catalog / contract test inventory

- `tests/unit/agent_guidance/prompt_cases.yaml` は現行6 Skill を列挙し、各 Skill の positive coverage を持つ。
- `frontend-only-change` は現時点で `koiki-project-overview` を expected first skill としている。`koiki-frontend-work` 新設時に置換する。
- `test_skill_catalog.py` は canonical Skill、OpenAI metadata、Claude wrapper、API ownership 用語、Copilot / shared agent docs の一部を検証する。
- repository-side test は Claude wrapper の canonical path を検証するが、Codex の Skill routing と Copilot の canonical Skill 到達性は検証していない。
- runtime selection は repository-side test の対象外であり、`agent_skill_smoke.py` と prompt catalog による Codex / Claude Code / GitHub Copilot の別途 smoke 記録が必要である。

### 4. 後続タスクへ渡す不整合・更新候補

1. `docs/agent/skills/future-role-alignment.md` に、project-specific frontend を `apps/<project-slug>/frontend/` へ置く将来案が残る。`CONTEXT.md` と本計画の「`apps/` は backend 専用」に反するため、Task 1-1 で改定する。
2. `koiki-project-overview` と prompt catalog は frontend 専用 Skill が存在しない前提である。Task 2-1 で `koiki-frontend-work` を追加し、frontend-only case と API client / auth contract case を追加する。
3. 既存 backend Skills には frontend contract の確認を明確化する余地がある。特に `koiki-business-app-feature-work`、`koiki-refapp-feature-work`、`koiki-libkoiki-feature-work`、`koiki-auth-security`、`koiki-testing` が Task 0-2 / Task 1-1 の更新候補である。
4. Codex / Claude Code / Copilot で同じ guidance に到達させるため、Task 1-1 / Task 2-1 では `AGENTS.md`、`.claude/skills/`、`.github/copilot-instructions.md`、`.github/instructions/` と contract test の役割を整理する。既存 Claude wrapper は新 Skill 分を追加する以外、thin adapter のまま維持する。

### 5. Validation

- `DEBUG=False uv run --locked pytest tests/unit/agent_guidance/`
  - 17 passed in 1.18s
- `git diff --check`
  - 成功
