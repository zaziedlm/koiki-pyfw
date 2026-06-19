# DM-15 Agent guidance / Skills consistency review

作成日: 2026-05-04

対象タスク:

- `docs/dev/deferred-maintenance-tasks.ja.md` の `DM-15`

## 1. 目的

Codex、Claude Code、GitHub Copilot などの AI コーディングエージェントが、KOIKI-FW の現行構成と作業境界を一貫して判断できるようにする。

特に `DM-14` で整理した API ownership / sample feature boundary policy を、agent-facing guidance と Skills 相当の導線へ過不足なく反映する。

この PR では、すぐに skill 実体の大改修や名称変更を行わない。
まず、現行の guidance / Skills 構成を棚卸しし、反映方針、検証方法、後続 PR の分割基準を明確にする。

## 2. 現行構成

### 2.1 tool-neutral guidance

正本となる共有 guidance:

- `AGENTS.md`
- `docs/agent/README.md`
- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/environment.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`

役割:

- repository boundary / architecture / validation / environment caveat を tool-neutral に記録する
- Codex / Claude Code / GitHub Copilot などで共通して参照される運用ルールを置く
- historical design docs より current implementation と shared agent docs を優先する

### 2.2 canonical Agent Skills

canonical skill content:

- `docs/agent/skills/koiki-project-overview/`
- `docs/agent/skills/koiki-app-feature-work/`
- `docs/agent/skills/koiki-libkoiki-feature-work/`
- `docs/agent/skills/koiki-auth-security/`
- `docs/agent/skills/koiki-testing/`

補助文書:

- `docs/agent/skills/README.md`
- `docs/agent/skills/testing-plan.md`
- `docs/agent/skills/future-role-alignment.md`

役割:

- agent が具体タスクに入るときの短い task-specific guidance を提供する
- `SKILL.md` は簡潔に保ち、詳細は `references/` へ逃がす
- trigger されるべき条件は frontmatter `description` に明確に書く
- OpenAI 向け metadata は各 skill の `agents/openai.yaml` に置く

### 2.3 Claude Code wrappers

Claude Code discovery wrappers:

- `.claude/skills/`

役割:

- canonical skill content を複製しない
- `docs/agent/skills/` への薄い adapter として維持する
- wrapper の frontmatter / description は canonical skill とずれないようにする

### 2.4 GitHub Copilot instructions

GitHub Copilot guidance:

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`

役割:

- Copilot が repository boundary と layer ownership を短く把握できるようにする
- 詳細は `docs/agent/` へ誘導する
- `docs/agent/skills/` と同じ判断ができる最低限の境界ルールを持つ

### 2.5 Skill validation

検証用資産:

- `tests/unit/agent_guidance/prompt_cases.yaml`
- `tests/unit/agent_guidance/`
- `scripts/agent_skill_smoke.py`
- `docs/dev/agent-skill-checklist.md`

役割:

- canonical skill / metadata / wrapper の構造を repository-side test で検証する
- 実 agent runtime の routing smoke test 用 prompt catalog を管理する
- agent ごとの実選択結果は外部または手動 smoke test として記録する

## 3. DM-14 反映観点

DM-14 の結論:

- Todo API は当面 `libkoiki` の `framework sample / starter capability` として維持する
- Todo を business-specific API 配置の前例にしない
- 新規 business API は原則 `components/koiki_ref_app/` または `apps/` 側から始める
- `components/libkoiki/` に置く API は reusable framework capability または明示された starter/sample capability に限る

DM-15 では、この判断が次の導線に反映されているか確認する。

- ambiguous task routing
- app feature skill
- libkoiki feature skill
- Copilot instructions
- Claude wrappers
- prompt cases / smoke checklist

## 4. 作業方針

### 4.1 最初は棚卸しと小さな整合修正に留める

DM-15 初回 PR では、次を優先する。

- canonical / wrapper / metadata / Copilot instructions の対応関係を棚卸しする
- DM-14 の API ownership policy が明確に参照されるようにする
- prompt catalog に不足する代表ケースを追加するか判断する
- 既存 skill 名は変更しない
- skill 実体の大改修や分割は行わない

### 4.2 Skill 作成・更新の原則

Skills は context を消費するため、`SKILL.md` は短く保つ。

方針:

- trigger 条件は frontmatter `description` に含める
- `SKILL.md` は workflow / guardrails / read-next に絞る
- 詳細な repository policy は `docs/agent/` または `references/` へ置く
- wrapper は canonical skill を参照する薄い adapter にする
- OpenAI metadata と wrapper description は canonical skill から乖離させない

### 4.3 すぐに新 skill を増やさない

DM-15 初回では、原則として新 skill を増やさない。

理由:

- 現行 skill set は既に repository overview / app / libkoiki / auth-security / testing の主要軸を持っている
- DM-14 の API ownership policy は既存 overview / app / libkoiki skill の判断精度を上げる内容であり、すぐに新 skill が必要とは限らない
- frontend 専用 skill や maintainer/template split は、future role alignment で後続候補として扱われている

新 skill を検討する条件:

- prompt catalog で repeated routing miss が確認される
- 既存 skill の description を調整しても誤選択が解消しない
- frontend / downstream apps / maintainer-template split の具体例が増え、独立 skill としての再利用性が高い

## 5. 推奨確認手順

### 5.1 guidance surface の棚卸し

```powershell
rg -n "components/libkoiki|components/koiki_ref_app|apps/|app/|Todo|API ownership|Skills|Copilot|Claude|Codex" AGENTS.md docs/agent .github docs/dev/agent-skill-checklist.md -S
```

確認すること:

- `AGENTS.md` は短い entry point に留まっている
- `docs/agent/` が shared guidance の正本になっている
- `docs/agent/skills/` が canonical skill content になっている
- `.claude/skills/` は thin wrapper である
- `.github/*instructions*` は詳細を重複せず `docs/agent/` と矛盾しない

### 5.2 skill structure contract

```powershell
uv run --locked pytest tests/unit/agent_guidance/
```

確認すること:

- canonical skill directory が存在する
- 各 skill が `SKILL.md` と `agents/openai.yaml` を持つ
- frontmatter `name` が directory name と一致する
- Claude wrapper が canonical path を指す
- prompt catalog が well formed である

### 5.3 smoke checklist

```powershell
uv run --locked python scripts/agent_skill_smoke.py generate --output docs/dev/agent-skill-checklist.md
```

確認すること:

- prompt catalog が人間レビュー可能な checklist へ生成できる
- DM-14 の API ownership 判断を確認する prompt が不足していない
- `Todo` を business-specific API として扱う case と、framework sample として扱う case の期待 skill が説明できる

### 5.4 実 runtime smoke

実 agent runtime で、`docs/dev/agent-skill-checklist.md` の prompt を使って selected skills を記録する。

確認すること:

- ambiguous layer task は `koiki-project-overview` から始まる
- business API は `koiki-app-feature-work` に寄る
- reusable framework API は `koiki-libkoiki-feature-work` に寄る
- auth / SSO / SAML / RBAC は `koiki-auth-security` を含む
- test scope は `koiki-testing` を含む

## 6. DM-15 初回 PR の想定作業

初回 PR では次のどちらかに留める。

### Plan-only PR

- 本計画文書を追加する
- `docs/dev/deferred-maintenance-tasks.ja.md` の DM-15 を更新する
- 実 skill / wrapper / metadata はまだ変更しない

### Small alignment PR

Plan-only に加えて、次の小変更を行う。

- `docs/agent/skills/README.md` に DM-14 ownership policy の参照を追加
- `koiki-project-overview` / `koiki-app-feature-work` / `koiki-libkoiki-feature-work` の `description` または guardrails を最小調整する
- `tests/unit/agent_guidance/prompt_cases.yaml` に DM-14 由来の routing case を追加する
- `.github/copilot-instructions.md` に API ownership の短い注意を追加する

どちらを採用するかは、棚卸し結果で判断する。

## 7. 残タスク / 別 PR 候補

DM-15 初回 PR 後に残す作業は、失念防止のため次の単位で扱う。

### DM-15-A: DM-14 ownership policy の skill routing 反映

状態: `対応済み`

目的:

- DM-14 の API ownership policy を既存 skill の trigger / guardrails へ最小反映する

候補:

- `docs/agent/skills/koiki-project-overview/SKILL.md`
- `docs/agent/skills/koiki-app-feature-work/SKILL.md`
- `docs/agent/skills/koiki-libkoiki-feature-work/SKILL.md`
- 各 `agents/openai.yaml`
- `.claude/skills/*/SKILL.md`
- `.github/copilot-instructions.md`

注意:

- 既存 skill 名は変更しない
- `SKILL.md` は短く保つ
- wrapper は canonical skill を参照する薄い adapter のままにする

実施結果:

- `koiki-project-overview` に `apps/` ownership と Todo sample 例外の routing rule を追加した
- `koiki-app-feature-work` に reference-app business scope と downstream/customer-specific API の guardrail を追加した
- `koiki-libkoiki-feature-work` に reusable framework / explicit starter-sample API の条件を追加した
- 各 `agents/openai.yaml` の short description / default prompt を ownership 判断に追随させた
- `.claude/skills/*/SKILL.md` の wrapper description を canonical skill の意図に合わせた
- `.github/copilot-instructions.md`、`.github/instructions/*.instructions.md`、`docs/agent/app.md`、`docs/agent/libkoiki.md`、`docs/agent/skills/README.md` に API ownership の短い注意を追加した
- `uv run --locked pytest tests/unit/agent_guidance` で agent guidance tests が通ることを確認した

### DM-15-B: prompt catalog / smoke checklist の拡充

状態: `対応済み`

目的:

- DM-14 由来の API ownership 判断を regression prompt として残す

候補:

- `tests/unit/agent_guidance/prompt_cases.yaml`
- `docs/dev/agent-skill-checklist.md`
- `scripts/agent_skill_smoke.py` の出力確認

追加したいケース:

- Todo を business-specific API として変更する依頼
- Todo を framework sample / starter capability として扱う依頼
- downstream `apps/` に案件固有 API を追加する依頼
- API ownership が曖昧な依頼

実施結果:

- `tests/unit/agent_guidance/prompt_cases.yaml` に DM-14 由来の API ownership 判断ケースを追加した
- `docs/dev/agent-skill-checklist.md` を prompt catalog から再生成した
- smoke result 評価テストの valid result template を追加ケースへ追随させた
- `uv run --locked pytest tests/unit/agent_guidance` で agent guidance tests が通ることを確認した

### DM-15-C: repository-side contract test の強化

状態: `対応済み`

目的:

- canonical skill / OpenAI metadata / Claude wrapper の drift を早めに検出する

候補:

- `tests/unit/agent_guidance/`
- `scripts/agent_skill_smoke.py`

確認したいこと:

- `.claude/skills/*/SKILL.md` が canonical skill path を参照している
- wrapper description と canonical description が大きく乖離していない
- `agents/openai.yaml` の default prompt が正しい `$skill-name` を参照している
- prompt catalog が全 skill を代表ケースで覆っている

実施結果:

- `tests/unit/agent_guidance/test_skill_catalog.py` に API ownership routing surface の drift 検出を追加した
- canonical skill / OpenAI metadata / Claude wrapper / Copilot instructions / scoped GitHub instructions / shared agent docs に `apps/`、API ownership、reference-app、starter/sample などの ownership 用語が残ることを検証するようにした
- 既存の wrapper canonical path 参照、OpenAI default prompt、prompt catalog coverage の検証と合わせて repository-side contract を強化した
- `uv run --locked pytest tests/unit/agent_guidance` で agent guidance tests が通ることを確認した

### DM-15-D: real runtime smoke result の記録方式

状態: `対応済み`

目的:

- Codex / Claude Code / GitHub Copilot で、実際にどの skill / guidance が選ばれたかを記録できるようにする

候補:

- `docs/dev/agent-skill-checklist.md`
- `agent-skill-results.json` の保存方針
- 実 runtime smoke の実施手順

注意:

- runtime 固有の挙動は repository-side test では完全に証明できない
- 結果記録は必要なときだけ残し、通常開発のノイズにしない

実施結果:

- `docs/agent/skills/testing-plan.md` に runtime smoke result の記録方針を追加した
- 通常は `.gitignore` 済みの `agent-skill-results.json` をローカル記録として使う方針を明記した
- release / regression investigation で結果を残す場合は、runtime、日付、prompt catalog revision、選択 skill、期待との差分を `docs/dev/` の dated document として残す方針にした
- repository-side contract tests は actual runtime routing の証明ではないことを明記した

### DM-15-E: 新 skill / role split の要否判断

状態: `判断済み / 新 skill 追加なし`

目的:

- frontend 専用 skill、downstream `apps/` 向け skill、maintainer / template split の必要性を判断する

候補:

- `docs/agent/skills/future-role-alignment.md`
- `docs/agent/skills/README.md`
- 新規 skill の作成可否

判断条件:

- 既存 skill の description / guardrails 調整では routing miss が解消しない
- frontend / downstream apps / maintainer-template split の具体例が十分にある
- skill 追加による discoverability 向上が、context / maintenance cost を上回る

判断結果:

- DM-15 follow-up では新 skill を追加しない
- frontend-only change と downstream `apps/` API placement は、現時点では `koiki-project-overview` で分類する
- reference-app backend work は `koiki-app-feature-work`、reusable framework / explicit starter-sample work は `koiki-libkoiki-feature-work` を継続利用する
- repeated routing miss が prompt catalog または runtime smoke result で確認された場合に、frontend / downstream apps / maintainer-template split を再判断する

#### 追記: v0.7.1 で downstream apps/ について再開

上記は DM-15 時点（2026-05-04）の判断であり、履歴として残す。v0.7.1 で downstream `apps/` レイヤーについてのみこの判断を再開し、命名衝突の解消（`koiki-app-feature-work` の `koiki-refapp-feature-work` へのリネーム）と、`apps/` 専用 skill `koiki-business-app-feature-work` の新設を行った。frontend 専用 skill と maintainer/template の full split は引き続き保留する。現行の skill 名・配置は本文の履歴ではなく、`docs/agent/skills/` と `docs/agent/skills/future-role-alignment.md` を正本とする。

## 8. 完了条件

- agent guidance / skills / wrappers / Copilot instructions の正本関係が説明できる
- DM-14 の API ownership policy をどこへ反映するかが決まっている
- skill 実体を大改修する場合の分割基準が明確である
- repository-side contract test と runtime smoke test の役割が分離されている
- DM-13 v0.7.0 release preparation 前に、agent-facing guidance の一貫性確認方針が固まっている

## 9. 結論

DM-15 は、AI agent 向け導線の一貫性を v0.7.0 release preparation 前に固めるためのタスクである。

初回は、既存の canonical skill set を尊重し、DM-14 の API ownership policy をどの guidance surface へ反映するかを確認する。

Skill の新規追加、名称変更、maintainer/template split は、実 runtime smoke の結果や downstream 具体例が揃ってから別 PR で扱う。
