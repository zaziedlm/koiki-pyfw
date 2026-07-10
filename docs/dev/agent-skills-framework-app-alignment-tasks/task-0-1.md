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

未実施。
