# Task 2-1: `koiki-frontend-work` design and implementation

## 目的

root `frontend/` の上流・参照 frontend を対象とする独立 Skill を新設し、Vite + React SPA の推奨実装と frontend contract を案内できるようにする。

## 事前条件

- Task 0-1、Task 0-2、Task 1-1 が完了している。

## 対象

- `docs/agent/skills/koiki-frontend-work/`（新設）
- metadata、reference、Claude wrapper、Codex 導線、Copilot guidance
- Skill catalog、prompt catalog、contract test
- `docs/agent/skills/README.md`
- `docs/agent/skills/future-role-alignment.md`

## 必須の設計境界

- 対象は root `frontend/` であり、`apps/` 配下へ frontend を配置しない。
- Vite + React SPA、React Router、TanStack Query、backend-managed Cookie/CSRF を標準・推奨として具体的に案内する。
- API、認証、認可、Cookie/CSRF、error、設定、テストの frontend contract は、将来の別 frontend 技術にも適用する一般原則として分離する。
- backend API の実装・変更の ownership を奪わず、該当する backend Skill と `koiki-auth-security` / `koiki-testing` へ適切に接続する。

## 実施手順

1. Task 0-2 の代表シナリオから、frontend Skill の起動条件と非対象を決める。
2. `SKILL.md`、reference、`agents/openai.yaml`、Claude discovery wrapper を作成し、Codex と GitHub Copilot の発見・instruction 導線を追加または更新する。
3. 新規画面、backend API 利用、auth/CSRF、routing、Query、form/mutation、frontend test、frontend config/CI の標準手順を記載する。
4. 既存 Skill と責務が重ならないことを確認し、Read Next を設定する。
5. catalog と contract test に frontend task の正しい routing を追加する。

## 完了条件

- `koiki-frontend-work` が発見可能で、root `frontend/` の作業へ適切に選択される。
- Vite + React SPA の具体的な推奨と、技術非依存の frontend contract が区別されている。
- `apps/` への frontend 配置を示唆しない。
- backend / auth / testing Skills との連携が明確である。
- Codex、Claude Code、GitHub Copilot の各利用者が同じ frontend Skill と関連 guidance へ到達できる。

## 実施結果

完了（2026-07-11）。

### 新設した Skill

- canonical Skill: `docs/agent/skills/koiki-frontend-work/`
  - `SKILL.md`
  - `agents/openai.yaml`
  - `references/frontend-contract.md`
- Claude Code discovery wrapper: `.claude/skills/koiki-frontend-work/SKILL.md`

`koiki-frontend-work` は root `frontend/` の Vite + React SPA を対象にし、routes、UI、feature API、TanStack Query、Cookie/CSRF browser integration、config、frontend test を扱う。backend API ownership、backend authorization、Cookie issuance / validation、および `apps/` 配下への frontend 配置は対象外とした。

### 既存 guidance との接続

- `koiki-project-overview` は root frontend task を `koiki-frontend-work` へ routing し、API ownership が曖昧な場合は引き続き overview から開始する。
- backend API contract を変更する場合は、所有する backend Skill と `koiki-frontend-work` を併用する。
- Cookie session / CSRF / SSO / SAML browser flow は `koiki-auth-security` を併用する。
- test scope は `koiki-testing` を併用する。
- `AGENTS.md`、Copilot global / frontend instruction、Skill README、future role alignment を新 Skill へ接続した。

### Catalog / contract test

- `prompt_cases.yaml` に `koiki-frontend-work` を追加した。
- frontend-only UI change は `koiki-frontend-work` を required first skill とした。
- Cookie session response schema を消費する frontend API client change は、`koiki-frontend-work` を先頭に `koiki-auth-security` を併用する case とした。
- smoke script fixture と Agent Skill testing plan を新 routing に更新した。

## Validation

- skill-creator `quick_validate.py`（project locked environment）
  - `Skill is valid!`
- `DEBUG=False uv run --locked pytest tests/unit/agent_guidance/`
  - 17 passed in 1.01s
- `git diff --check`
  - 成功
