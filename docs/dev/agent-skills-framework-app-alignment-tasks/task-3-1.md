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

未実施。
