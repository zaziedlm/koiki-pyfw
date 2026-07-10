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

未実施。
