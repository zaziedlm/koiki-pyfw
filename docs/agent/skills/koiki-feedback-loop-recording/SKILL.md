---
name: koiki-feedback-loop-recording
description: Use right after openspec/opsx:propose (or opsx:ff), opsx:continue/opsx:update, opsx:apply, opsx:verify, or opsx:sync/opsx:archive completes, to append what happened — AI input/output, human judgment, deviations, lessons, and the Harvest-candidate flag — as a Loop #N entry in .aidx/loop-design/<案件名>/SPEC-<番号>_<change-name>/feedback-loop.md. Records judgment and evidence, not Requirement, Scenario, Design, or Tasks content.
---

# KOIKI Feedback Loop Recording

Use this skill after a step of the ①要件定義→②設計→③実装→④テスト→⑤評価・改善 loop actually completes for a Spec unit.

`feedback-loop.md` records what a human decided during a loop and why — not whether AI was used, and not the Spec content itself. Per `.aidx/loop-design/README.md`: "記録は「AIを使ったか」ではなく「人が何を判断したか」を残す." It is append-only: past `## Loop #N` sections are never rewritten, even to match a later outcome — the divergence itself is the record's value.

## When this fires

`openspec new` / `opsx:*` commands do not touch `.aidx/loop-design/` on their own. This skill is the manual bridge, triggered right after specific OPSX checkpoints actually complete:

| Just completed | Fill in `feedback-loop.md` |
| --- | --- |
| `opsx:propose` / `opsx:ff` (proposal.md, delta spec confirmed) | create the file if missing (register the row in `SPEC-MAP.md` too, via `koiki-spec-map-maintenance`); fill ①要件定義 |
| `opsx:continue` / `opsx:update` (design.md confirmed) | ②設計 |
| `opsx:apply` (tasks implemented) | ③実装, and ④テスト once tests are actually written |
| `opsx:verify` | ④受入条件充足状況, ⑤評価・改善 |
| `opsx:sync` / `opsx:archive` | ループ完了記録 (次ループのパターン, Harvest候補フラグ) |

The full mapping, including the `SPEC-MAP.md` side that `koiki-spec-map-maintenance` owns, is in `.aidx/loop-design/README.md`. Never fill a step for a checkpoint that has not actually completed yet — a planned `opsx:apply` is not the same as a finished one.

## Scope

- `.aidx/loop-design/<案件名>/SPEC-<番号>_<change-name>/feedback-loop.md` — the target file
- `.aidx/loop-design/feedback-loop-TEMPLATE.md` — the template it was copied from (never edit this file itself)
- `.aidx/loop-design/poc-insurance-inquiry/SPEC-101_inquiry-db/feedback-loop.md` — a worked example of the recording style

## Before writing

1. Locate the Spec unit's `feedback-loop.md`. If none exists, do not invent structure — create it by copying `feedback-loop-TEMPLATE.md`, per the README's 使い方, and add the corresponding row to the initiative's `SPEC-MAP.md` (use `koiki-spec-map-maintenance` for that half).
2. Read the whole file, including which `## Loop #N` is still open and which steps (①〜⑤) already have entries.
3. Gather real evidence for what you are about to record — `openspec validate` output, actual test results, `design.md`, `tasks.md`, git diff/log, `/opsx:verify` output. Never write a step up as done because it was planned; write it up because it happened and you can show what happened.

## Workflow

1. Determine whether this is a new step within the currently open Loop #N, or the start of a new Loop #N+1 (a new loop begins after ループ完了記録 has been filled for the previous one).
2. For each step you actually completed (①要件定義／②設計／③実装／④テスト), fill in: what was given to the AI, what the AI produced (summarized — not the full text, which belongs in `openspec/`), and the human's judgment (採用／修正／却下 and why). The judgment cell is the point of the record; do not leave it as a placeholder or a bare "採用."
3. For ②設計, also record any AIレビューでの指摘 (抜け漏れ, 曖昧表現, Requirement/Scenario count mismatches).
4. For ④テスト, record whether every Scenario has a corresponding test case — a count match/mismatch, not a vague "tests pass."
5. Only after ③実装 and ④テスト have actually happened, fill ⑤評価・改善 (Specの改善点／Skillsの過不足／Specと実装の乖離).
6. Close the loop by filling ループ完了記録: 次ループのパターン (A：改善／B：依存展開／C：次機能), the reason, うまくいったこと, 課題, 改善提案, and the Harvest候補フラグ with its reasoning. Do not set the flag without naming the specific reusable pattern.
7. Append the entry; report which Loop # and which steps were filled, and what evidence backed each.

## Guardrails

- Do not fabricate AI outputs, validation results, or test results that were not actually observed in this session.
- Do not condense a step to "N/A" or a one-word判断 when the human's reasoning is the reason this record exists.
- Do not copy full Requirement, Scenario, Design, or Tasks text into the loop record — summarize scope and point at the artifact instead.
- Do not rewrite or delete a previous `## Loop #N` section to match a later decision. Append a new loop instead.
- Do not fill ⑤評価・改善 or ループ完了記録 before ③実装/④テスト have actually happened for that loop.
- Do not invent a 標準化責任者へのフィードバック日 unless that feedback was actually given.
- Do not duplicate ledger-level facts (状態, 完了日, 進捗サマリ) here — those belong in `SPEC-MAP.md`; use `koiki-spec-map-maintenance` to update them once this loop's outcome is known.

## Read Next

- `.aidx/loop-design/README.md` — recording principle and directory layout
- `.aidx/loop-design/feedback-loop-TEMPLATE.md` — the per-step table structure and its own inline comments
- `.aidx/loop-design/poc-insurance-inquiry/SPEC-101_inquiry-db/feedback-loop.md` — worked example, including how a design-judgment escalation was written up
- `docs/agent/skills/koiki-spec-map-maintenance/SKILL.md` — companion skill for the ledger this loop feeds into
- `docs/agent/skills/koiki-spec-authoring/SKILL.md` — the artifacts referenced from ①/②
