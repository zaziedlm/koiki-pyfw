# Agent Skills: 業務アプリ開発・Frontend Contract 整備タスク

本ディレクトリは [Agent Skills: 業務アプリ開発・Frontend Contract 整備計画](../agent-skills-framework-app-alignment-plan.ja.md) の個別タスクを収録する。

## 進め方

- 原則として番号順に進める。
- `apps/` は業務固有 backend API の配置・合成層であり、frontend の配置先にしない。
- root `frontend/` は上流・参照 frontend とし、Vite + React SPA を標準・推奨として扱う。
- backend API 変更と frontend 実装を混同せず、それぞれの Skill 境界を明示する。
- Skill の名称、本文、reference、metadata、wrapper、catalog、contract test は同じ change window で整合させる。
- Codex、Claude Code、GitHub Copilot の各導線で、canonical Skill と同じ境界・用語・task routing を利用できることを確認する。
- 各タスク完了時に、該当ファイルの `実施結果` を更新する。

## タスク一覧

1. [Task 0-1: Skill catalog / validation inventory](./task-0-1.md)
2. [Task 0-2: Backend API / frontend contract impact map](./task-0-2.md)
3. [Task 1-1: Existing backend Skills and shared guidance alignment](./task-1-1.md)
4. [Task 2-1: `koiki-frontend-work` design and implementation](./task-2-1.md)
5. [Task 3-1: Skill routing validation and final documentation](./task-3-1.md)
