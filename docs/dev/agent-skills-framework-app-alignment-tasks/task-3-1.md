# Task 3-1: Skill routing validation and final documentation

## 目的

改定・新設した Skills が、業務アプリ開発と root frontend 開発の代表タスクを正しく routing し、関連文書と整合していることを確認する。

## 事前条件

- Task 1-1 と Task 2-1 が完了している。

## 実施手順

1. prompt catalog / contract test を実行し、Skill 名、metadata、Claude wrapper、Codex 導線、Copilot guidance、reference の整合を確認する。
2. 次の代表シナリオで expected Skill を確認する。
   - `apps/` の業務 API 追加
   - reusable framework API の追加
   - reference app API の追加
   - session auth / CSRF の変更
   - SSO / SAML の変更
   - root `frontend/` の新規画面・API client・test 追加
   - frontend 影響を伴う backend API schema 変更
3. `docs/agent/`、Skill README、future role alignment、CONTEXT の用語が矛盾しないことを検索で確認する。
4. Codex、Claude Code、GitHub Copilot で利用できる runtime smoke の結果を記録する。repository-side contract test だけで実際の runtime selection を証明しない。
5. 実行した validation、未対応事項、将来の再点検条件を記録する。

## 検証

- Agent Skills の既存 contract test
- prompt catalog の検証
- 関連する focused test
- `git diff --check`

## CI 移行の申し送り

`dev/v0.7-react-only` は既存 workflow の push 対象外であるため、本タスクではローカル validation を証跡として残す。新規開発線 `dev/v0.8` の開設時に、GitHub Actions workflow の対象 branch と required check を整備し、`tests/unit/agent_guidance/` を含む CI が push / pull request で発動することを確認する。この CI 設定変更は本タスクの code change に含めない。

## 完了条件

- 代表シナリオが適切な Skill へ routing する。
- 新 Skill を含む catalog、metadata、wrapper、test が整合する。
- Codex、Claude Code、GitHub Copilot の各導線で、同じ task routing と共通用語を確認できる。
- 業務 backend API の変更と root frontend の変更の責務境界が説明できる。
- 実施結果と残課題が記録されている。
- `dev/v0.8` 開設時に行う CI trigger / required check 整備が申し送りとして記録されている。

## 実施結果

完了（repository-side validation、2026-07-11）。

### Routing / 導線の確認

`tests/unit/agent_guidance/prompt_cases.yaml` は 7 Skills、16 representative cases とした。Task 3-1 の代表シナリオは次の routing で catalog に固定されている。

| 代表シナリオ | required first Skill | 併用 Skill |
| --- | --- | --- |
| `apps/` の業務 API 追加 | `koiki-business-app-feature-work` | frontend consumer があれば `koiki-frontend-work`、test は `koiki-testing` |
| reusable framework API 追加 | `koiki-libkoiki-feature-work` | frontend contract に影響する場合は `koiki-frontend-work` |
| reference app API 追加 | `koiki-refapp-feature-work` | frontend contract に影響する場合は `koiki-frontend-work` |
| session auth / CSRF の変更 | `koiki-frontend-work`（browser consumer の変更） | `koiki-auth-security` |
| SSO / SAML の変更 | `koiki-auth-security` | `koiki-refapp-feature-work` |
| root `frontend/` の画面・API client・test 追加 | `koiki-frontend-work` | 必要な backend owner / auth / testing Skill |
| frontend 影響を伴う reference app API schema 変更 | `koiki-refapp-feature-work` | `koiki-frontend-work`、`koiki-testing` |

catalog / metadata / Claude wrapper / Codex `AGENTS.md` 導線 / Copilot global・path instruction は focused contract test で確認した。`koiki-frontend-work` の canonical Skill、OpenAI metadata、Claude wrapper、`AGENTS.md`、Copilot instruction が同じ名称を参照することも test に加えた。

### 文書・用語の確認

- 現行 guidance（`CONTEXT.md`、`docs/agent/`、Skill README、future role alignment、Codex / Copilot guidance）は、`apps/` を backend-only とし、root `frontend/` を frontend placement とする。
- `apps/<project-slug>/frontend/` の旧案は active guidance から除去済みである。過去の判断記録で同案を記す `docs/dev/v0.7-task-instructions/task-4-3.md` と `task-4-5.md` には、現行方針ではないことと正本への参照を注記した。
- `docs/dev/agent-skill-checklist.md` を現行 catalog から再生成した。実際の runtime selection を記録する際は、同 checklist と `agent-skill-results.json`（git ignore 対象）を使用する。
- fresh Codex / Claude Code / GitHub Copilot session の統一手順は [Agent Skill Runtime Smoke 実行指示書](../agent-skill-runtime-smoke-instructions.ja.md) に分離した。期待値を評価対象 agent に渡さず、native Skill selection と instruction-only routing を区別して記録する。

### Runtime smoke の記録

この作業環境では repository 内 canonical Skill を選択する fresh Codex runtime、Claude Code runtime、GitHub Copilot runtime を起動・操作できない。そのため実際の Skill selection を推測して記録していない。

- Codex: この session の利用可能 Skill catalog は session 開始時の snapshot であり、repository 新設 Skill の selection を観測できない。
- Claude Code / GitHub Copilot: 対話 runtime への接続手段がない。

次回、各 runtime が repository の current guidance を読み込む fresh session で、生成済み checklist の 16 cases を実行し、`agent-skill-results.json` を `scripts/agent_skill_smoke.py evaluate` で評価する。runtime 選択結果は agent version / installation に依存するため、repository-side contract test の成功とは区別する。

### Validation

- `DEBUG=False uv run --locked pytest tests/unit/agent_guidance/`
  - 18 passed
- `DEBUG=False uv run --locked python scripts/agent_skill_smoke.py generate --output docs/dev/agent-skill-checklist.md`
  - 成功
- `git diff --check`
  - 成功

### CI 移行の申し送り

本 Task では CI workflow を変更していない。`dev/v0.8` 開設時に、GitHub Actions の trigger branch と required check を整備し、`tests/unit/agent_guidance/` を push / pull request で実行することを確認する。runtime smoke は CI の static contract test で置換せず、上記の fresh runtime smoke を別途行う。
