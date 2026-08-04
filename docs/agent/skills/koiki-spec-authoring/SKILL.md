---
name: koiki-spec-authoring
description: Use when writing or editing any OpenSpec artifact in this repository — capability specs under openspec/specs/, change proposals and delta specs under openspec/changes/, loop records under .aidx/loop-design/ — or when running openspec new change, openspec validate, or openspec archive. Defines the Japanese 【SHALL】 notation this repository requires, which overrides the English SHALL prose the built-in openspec-* skills produce.
---

# KOIKI Spec Authoring

Use this skill for every OpenSpec artifact in this repository.

The built-in `openspec-*` skills define the OpenSpec *workflow*. This skill defines how this repository writes the *content*. Where they disagree, this skill wins.

Requirement text is written in Japanese. The `SHALL` / `SHALL NOT` keywords stay in ASCII uppercase because `openspec validate` matches them literally with `/\b(SHALL|MUST)\b/`.

## Scope

Typical targets:

- `openspec/specs/<capability>/spec.md` — 機能Spec（業務ドメイン単位）
- `openspec/changes/<change-name>/proposal.md` — 実装Spec単位のメタ情報と変更理由
- `openspec/changes/<change-name>/specs/<capability>/spec.md` — デルタSpec（振る舞い・制約）
- `openspec/changes/<change-name>/design.md` — 実装方式・技術選定
- `.aidx/loop-design/<案件名>/SPEC-MAP.md` — Spec一覧・番台・依存関係

## Notation

規範文は、箇条書きの行頭に `【SHALL】`（必須）または `【SHALL NOT】`（禁止）を置いた日本語で書く。

```markdown
## ADDED Requirements

### Requirement: 問い合わせ受付の受理

- 【SHALL】システムは、必須項目が充足された問い合わせ登録要求を受理し、受付番号を発行しなければならない。
- 【SHALL NOT】システムは、受付番号を利用者の入力値から導出してはならない。

受付番号の採番方式は design.md を参照する。

#### Scenario: 正常系 - 必須項目充足
- **WHEN** 認可された利用者が必須項目を充足した要求を送信する
- **THEN** HTTP 201 と受付番号を返す

#### Scenario: 異常系 - 必須項目の欠損
- **WHEN** 必須項目が欠損した要求を送信する
- **THEN** HTTP 400 と欠損項目を示すエラーを返す

#### Scenario: 境界値 - 添付ファイル上限
- **WHEN** 10MB ちょうどのファイルを添付して送信する
- **THEN** 受理される
```

Rules:

- 規範文は1行に1文。行頭ラベルは `【SHALL】` と `【SHALL NOT】` の2種類のみ
- ラベルを太字にしない。`**SHALL**:` の形式は使用禁止
- 推奨・非推奨・任意（SHOULD / MAY 相当）は Requirement 本文に書かず、`design.md` または機能Specの補足に回す
- ラベルなしの補足説明行は同じ本文内に自由に書いてよい
- Scenario の `**WHEN**` / `**THEN**` にラベルを付けない
- 各 Requirement に Scenario を1つ以上置き、正常系・異常系・境界値を揃える
- 受入条件を独立セクションとして書かない。Scenario がそのまま受入条件になる

## Silent failures — verify before finishing

These break the artifact without producing a validation error.

- Scenario 見出しを `###`（3つ）にすると、Scenario が存在しない扱いになる。必ず `####`（4つ）
- `## ADDED / MODIFIED / REMOVED / RENAMED Requirements` の外に書いた表や説明は、archive 時に失われる
- `## Purpose` に HTML コメント（`<!-- -->`）が残っていると、Purpose が破棄され TBD に置換される
- ラベルを太字にすると、パーサがメタデータ行と判定して規範文を本文から除外する

## Workflow

1. classify the artifact: 機能Spec（capability全体の業務ルール） or 実装Spec単位（個別の振る舞い）
2. confirm the owning capability and the target layer against `docs/agent/boundaries.md`
3. for a new change, write `proposal.md` first: `## メタ情報` → `## Why`（50字以上） → `## What Changes` → `## Capabilities` → `## Impact`
4. write the delta spec: split requirements by meaning, not by document section. 定義表が大きくなるときは Requirement を分割する
5. derive scenarios from the behavior, then check that 正常系・異常系・境界値 are all present
6. move any implementation choice, library selection, or tradeoff into `design.md`
7. run validation and fix before handing over

## Guardrails

- do not write English SHALL prose (`The system SHALL ...`); this repository uses the 【SHALL】 label form
- do not add `## Purpose` to a delta spec when the capability spec already exists — it is ignored
- do not create a requirement just to satisfy validation. This repository's `spec-driven` schema has no capability-less path: `tasks` requires `specs`, and `specs` requires at least one capability. When a change looks non-business (cross-cutting, technical-only), look for the business domain it actually serves — audit, observability, and operational-monitoring concerns are legitimate capabilities in a regulated business, not just "infra" — and scope the Requirement narrowly to what the change implements. Do not invent a capability-skip mechanism; none exists in the installed `openspec` CLI
- do not put 配下の実装Spec単位一覧 in the 機能Spec; SPEC-MAP.md owns it
- do not put インデックス方針, 実装方式, or 技術選定の理由 in a spec file; they belong in `design.md`
- do not leave a 制約条件 without a measurable scenario — if the measurement condition cannot be stated, the constraint belongs in `design.md`
- do not exceed 500 characters in a requirement body; split the requirement instead
- do not use 曖昧表現: 適切に / なるべく / 必要に応じて / 〜できる / 〜を考慮する

## Validate

```bash
openspec validate <change-name> --strict   # 単体
openspec validate --changes                # 進行中の change をすべて
openspec validate --all --strict           # 提出前
```

- fix every ERROR before handing over
- treat the 500-character warning as a signal to split the requirement, not as noise
- validation passing does not mean the spec is correct: the four silent failures above are not detected

## Read Next

- `references/requirement-patterns.md` — 実装Spec種別ごとの Requirement 骨格
- `.aidx/SPEC-CHEATSHEET.md` — 1枚版
- `docs/agent/boundaries.md` — レイヤ配置の判断
- `openspec/config.yaml` — このリポジトリの spec 記述ルール
- `../koiki-spec-map-maintenance/SKILL.md` — この Spec の一覧・依存関係を `SPEC-MAP.md` に反映する
- `../koiki-feedback-loop-recording/SKILL.md` — このループの判断・学びを `feedback-loop.md` に記録する
