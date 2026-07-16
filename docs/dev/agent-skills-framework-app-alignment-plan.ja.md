# Agent Skills: 業務アプリ開発・Frontend Contract 整備計画

## 目的

本計画は、KOIKI-FW で業務アプリを構築・保守する開発者が、現行の backend API 契約と frontend contract を正しく利用できるよう、`docs/agent/skills/` の Agent Skills 群を点検・改定・拡張するためのものである。

主利用者は `apps/` で業務固有 backend API を構築する開発者とし、KOIKI-FW 本体の保守者向け詳細は既存の共通 guidance と個別 Skill で補完する。

## 確定した境界

- `apps/` は業務固有 backend API の配置・合成層である。frontend の配置先にはしない。
- root `frontend/` は reference application と組になる上流 frontend である。
- Vite + React SPA は現在の標準・推奨 frontend 実装である。ただし、API・認証・セキュリティの frontend contract は将来の別技術にも適用する。
- backend API を実装・変更する作業は既存 backend Skills が所有する。frontend Skill は root `frontend/` の画面、API client、routing、state、frontend test を扱う。
- `koiki-frontend-work`（仮称）は、本計画の最終成果物として必ず新設する。

用語の正本は root `CONTEXT.md` を参照する。

## 対象

- `docs/agent/skills/` の既存 Skill、reference、`agents/openai.yaml`
- `.claude/skills/` の discovery wrapper
- `.github/copilot-instructions.md` と `.github/instructions/` の Copilot guidance
- Codex の `AGENTS.md` と canonical Skill discovery 導線
- Agent Skills の prompt catalog / contract test / testing plan
- `docs/agent/` の共通 guidance
- `docs/agent/skills/future-role-alignment.md`
- 現行 backend API、認証・SSO/SAML、frontend SPA の公開契約を示す code / docs

## 対象外

- 個別 endpoint の完全な API リファレンス作成
- 業務固有 API の実装変更
- `apps/` 配下への frontend directory 導入
- frontend 技術を Vite + React だけに限定する決定

## 実行順序

1. Task 0-1: Skill catalog / validation inventory
2. Task 0-2: Backend API / frontend contract impact map
3. Task 1-1: Existing backend Skills and shared guidance alignment
4. Task 2-1: `koiki-frontend-work` design and implementation
5. Task 3-1: Skill routing validation and final documentation

詳細は `docs/dev/agent-skills-framework-app-alignment-tasks/` を参照する。

## 完了条件

- 既存 Skill の役割・重複・frontend contract への影響が記録されている。
- 業務 backend API の変更時に、frontend contract、認証、テストへの影響を確認する導線が既存 Skill にある。
- `apps/` が backend 専用であり、root `frontend/` が frontend の配置先であることが全 Skill で矛盾なく示される。
- Vite + React SPA を標準・推奨として具体的に案内しつつ、将来の frontend 技術を禁止しない `koiki-frontend-work` が存在する。
- Skill 本文、metadata、wrapper、catalog、contract test が整合し、代表的な業務アプリ開発タスクで適切に routing できる。

## Change Control

`docs/agent/skills/` を Skill 本文の正本とし、Codex、Claude Code、GitHub Copilot で同じ境界・用語・routing が利用できるようにする。Skill の名称、対象範囲、metadata、Claude wrapper、Copilot guidance、prompt catalog、contract test は一つの変更単位で更新する。Skill を追加・改名・削除する場合は、利用者への migration note と `future-role-alignment.md` を同じ change window で更新する。

## CI 移行上の扱い

本計画を実施する `dev/v0.7-react-only` は既存 GitHub Actions workflow の push 対象外である。各タスクでは `tests/unit/agent_guidance/` をローカルで実行して repository-side contract を確認する。新しい開発線 `dev/v0.8` を開設する時点で、CI workflow の対象 branch と required check を整備し、Agent Skills contract test を含む既存 CI を発動させる。
