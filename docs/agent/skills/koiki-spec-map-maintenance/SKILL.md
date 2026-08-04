---
name: koiki-spec-map-maintenance
description: Use right after openspec/opsx:new, opsx:propose/opsx:ff, or opsx:sync/opsx:archive completes, to register a new 実装Spec単位 or update 状態/依存関係/進捗サマリ in a .aidx/loop-design/<案件名>/SPEC-MAP.md ledger. Keeps Spec identity, capability ownership, dependencies, and lifecycle state; does not duplicate Requirement, Scenario, Design, Tasks, or loop-record content.
---

# KOIKI SPEC-MAP Maintenance

Use this skill whenever a `SPEC-MAP.md` ledger under `.aidx/loop-design/<案件名>/` needs to be created, registered, or updated.

`SPEC-MAP.md` is a 台帳 (ledger), not authored prose. It tracks *which* Specs exist, *who* owns them, *how* they depend on each other, and *what state* they are in. It does not hold Requirement text, Scenario text, design rationale, task lists, or the AI/human judgment record of a loop — those live in `openspec/` and in the Spec's own `feedback-loop.md`.

## When this fires

`openspec new` / `opsx:*` commands do not touch `.aidx/loop-design/` on their own — nothing links the two automatically. This skill is the manual bridge, triggered right after specific OPSX checkpoints actually complete:

| Just completed | Update in SPEC-MAP.md |
| --- | --- |
| `opsx:new` (change directory created, initiative has no `.aidx/loop-design/<案件名>/` yet) | create `<案件名>/` and `SPEC-MAP.md` (第1〜2節) |
| `opsx:propose` / `opsx:ff` (proposal.md, delta spec confirmed) | add a row to 第3節・第4節 (Spec番号 as a hypothesis) |
| `opsx:sync` / `opsx:archive` | 第4節 状態→完了, 完了日, recompute 第7節 進捗サマリ |

The full mapping, including the steps this skill does *not* own (②設計・③実装・④テスト belong to `koiki-feedback-loop-recording`), is in `.aidx/loop-design/README.md`. Never update a section for a checkpoint that has not actually completed yet.

## Scope

- `.aidx/loop-design/<案件名>/SPEC-MAP.md` — the target file
- `.aidx/loop-design/SPEC-MAP-TEMPLATE.md` — the template it was copied from (never edit this file itself)
- `.aidx/loop-design/examples/SPEC-MAP-EXAMPLE-start.md` — what a freshly started SPEC-MAP looks like
- `.aidx/loop-design/README.md` — the operating rules for this directory

## Before editing

1. Locate the initiative's `SPEC-MAP.md`. If none exists for the named 案件, do not invent one — confirm the 案件名 and create it by copying `SPEC-MAP-TEMPLATE.md`, then delete its explanatory 第0節, per the README's 使い方.
2. Read the whole file, including blank cells. Blank is the normal state for a ledger in progress — never fill a blank cell with an assumption to make the table "look complete."
3. Identify which section the requested change actually touches (see below) before writing anything.
4. Cross-check the fact against real evidence — `openspec/changes/<change-name>/`, its `openspec/changes/archive/<date>-<change-name>/` location once archived, the Spec's `feedback-loop.md` ループ完了記録 — rather than from memory or the request's wording alone.

## Section map

| # | Section | Typically updated when |
| --- | --- | --- |
| 1 | 基本情報 | at 案件 kickoff only |
| 2 | ループ共通設定 | at 案件 kickoff, or when Skills supplied change |
| 3 | 機能Spec一覧 | a capability spec is created; レイヤに関する所見 firms up during ③実装 |
| 4 | 実装Spec単位一覧 | a Spec unit is registered (①要件定義直後, as a hypothesis) or its 状態/完了日/Harvest候補 changes |
| 5 | Spec単位間の依存関係 | derived from section 4 changes; レイヤ横断の波及 fills in during ③実装 |
| 6 | 全体整合の確認 | an explicit cross-Spec consistency check was actually performed |
| 7 | 進捗サマリ | recompute from sections 3/4 whenever either changes — never hand-adjust the numbers independently |
| 8 | 全体振り返り | 案件 completion, or an explicit interim retrospective |

Section 4 is the only section that requires judgment at kickoff (how the 案件 splits into Spec units). Every other section is either clerical or fills in naturally as loops run — do not force sections 6 or 8 to be non-empty before the events they describe have actually happened.

## Workflow

1. Confirm the invoking user is, or is acting for, this 案件's 適用オーナー — `SPEC-MAP.md` is edited by that role only (README: "複数人が触ると全体地図が壊れる"). If unclear, ask before writing.
2. Edit only the section(s) identified above. Preserve the existing table structure, column order, status vocabulary (e.g. 未着手／進行中／完了), and date format already used in that file — do not introduce new terms like "Archived" or "Completed" even if they read more naturally in English.
3. For a new Spec unit row: fill Spec番号, change-name, 所属機能Spec, and 実装Spec種別 (共通機能／API連携／データ・DB／外部サービス連携／セキュリティ横断／画面・UI). Leave 担当者/状態/完了日/Harvest候補 blank unless already known.
4. For a status transition: update 状態 and, on completion, 完了日. Then recompute 進捗サマリ (第7節) from the actual row counts.
5. Report exactly which section(s) and rows changed, and what evidence backed the change.

## Guardrails

- Do not create a second `SPEC-MAP.md` for an initiative that already has one.
- Do not hand-edit `SPEC-MAP-TEMPLATE.md` or `feedback-loop-TEMPLATE.md`. If the template itself seems wrong, that is a 標準化責任者 escalation (README), not a direct edit.
- Do not add a relative link from `SPEC-MAP.md` to `openspec/changes/<change-name>/`. Archiving moves that path, so this repo keys on the change-name string and locates it by repository search when needed (README A-2③) — do not add an "archive path" column; none exists in the template.
- Do not renumber an existing Spec番号 to close a gap. Numbering is one 番台 per 機能Spec, fixed at kickoff; skipped numbers are not reused (D-03 4-3).
- Do not copy Requirement, Scenario, Design, Tasks, or AI-input/output text into `SPEC-MAP.md`. If asked to record *why* a decision was made or what a loop produced, that belongs in the Spec's `feedback-loop.md` — use `koiki-feedback-loop-recording` for that instead.
- Do not mark Harvest候補 in section 4 from this skill's own judgment; that column mirrors the Harvest候補フラグ already decided in `feedback-loop.md`'s ループ完了記録 — read it from there, don't originate it here.
- Do not fabricate 完了日, 状態, or 進捗サマリ numbers that are not backed by an actual completed step.

## Read Next

- `.aidx/loop-design/README.md` — full editing rules and directory layout
- `.aidx/loop-design/SPEC-MAP-TEMPLATE.md` — section-by-section fill timing (its own 第0節)
- `.aidx/loop-design/poc-insurance-inquiry/SPEC-MAP.md` — a worked example mid-案件
- `docs/agent/skills/koiki-feedback-loop-recording/SKILL.md` — companion skill for the per-Spec loop record
- `docs/agent/skills/koiki-spec-authoring/SKILL.md` — writing the Spec artifacts this ledger tracks
- `docs/agent/boundaries.md` — レイヤ判断の根拠
