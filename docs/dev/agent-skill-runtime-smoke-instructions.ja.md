# Agent Skill Runtime Smoke 実行指示書

## 目的

Codex、Claude Code、GitHub Copilot の各 runtime が、リポジトリで定義した Agent Skill を実際に発見・選択できるかを確認する。これは repository-side contract test とは別の確認であり、実際に利用可能な Skill、選択順、未発見の理由を記録する。

期待 Skill 名・期待順・禁止 Skill は operator 専用の [Agent Skill Smoke Checklist](./agent-skill-checklist.md) を正本とする。この指示書または catalog の期待値を、評価対象の agent に見せてはならない。

## 実施単位と前提

- 対象 runtime: Codex、Claude Code、GitHub Copilot
- 対象 repository revision: 実行前に `git rev-parse HEAD` で記録する。
- 各 prompt case は **新しい対話 session** で実行する。先行 case で読み込まれた Skill や会話文脈が次 case の選択に影響しないようにする。
- 新 session は、この repository の root を workspace / working directory として開く。
- 対象 runtime で Skill / instruction discovery を有効にする。project Skill が runtime の利用可能一覧に現れない場合、それを失敗として取り繕わず `unavailable` と記録する。
- agent に Skill 名の期待値、checklist、`tests/unit/agent_guidance/prompt_cases.yaml`、この指示書を読ませない。operator だけがそれらを参照する。
- source code・設定・Skill 文書を編集させない。これは routing 観測であって実装 task ではない。

## Operator の事前準備

repository root で次を実行し、実行日時、revision、runtime 名・version、OS を記録する。

```powershell
git rev-parse HEAD
uv run --locked python scripts/agent_skill_smoke.py template --output agent-skill-results.json
```

`agent-skill-results.json` は local runtime result 用であり、通常は Git に commit しない。release または回帰調査の証跡として残す場合は、結果を日付付きの `docs/dev/` 文書に転記する。

## 各 case の実施手順

1. target runtime で新しい session を開始し、repository root を開く。
2. runtime が開始時に表示する available Skills、読み込んだ instructions、Skill invocation log があれば、operator が記録する。期待値との比較はまだ行わない。
3. 下記の「agent への共通依頼」を最初に与える。続けて、checklist の当該 case にある **`Prompt:` の本文だけ** を与える。Expected / Forbidden / Rationale は渡さない。
4. agent が明示する Skill invocation、UI の Skill invocation 表示、または runtime log を、実際に選択された順で記録する。agent 自己申告だけの場合は、その旨も notes に記録する。
5. agent が repository Skill を利用できない、または Skill を選択しない場合は、そのまま `observed_skills: []` とし、available Skills と理由を notes に残す。手動で Skill 本文を貼り付けたり、期待名を教えたりして再実行してはならない。
6. operator が checklist の Expected / Required first / Forbidden と比較し、Pass / Fail / unavailable を記録する。agent がファイルを変更しようとした場合は中止する。
7. 次 case は必ず別の新 session で行う。

## agent への共通依頼

次の文章を、各 case の prompt の前に渡す。`[ここに case の Prompt 本文を貼る]` は operator が置き換える。

```text
これは Agent Skill routing の観測テストです。実装・ファイル編集・設定変更・テスト実行は行わないでください。

この session で runtime が実際に利用可能にした Skill または instruction だけを使って、次の依頼の着手に必要な Skill を選択してください。選択した Skill が runtime UI / tool log に表示されない場合は、実際に選択・読み込みできた Skill 名と順序だけを簡潔に報告してください。利用可能な repository Skill がない、または選択できない場合は、その事実と理由を報告して停止してください。

期待される Skill 名、テスト catalog、checklist は探索・参照しないでください。

依頼:
[ここに case の Prompt 本文を貼る]
```

## Tool 別の観測点

### Codex

- 新しい Codex conversation を repository root で開始する。
- session 開始時の available Skills に repository Skill が存在するかを確認する。
- Skill invocation 表示または agent の明示報告を記録する。
- `docs/agent/skills/` を手動で読ませた場合は native discovery の成功とは扱わず、notes に `manual guidance only` と記録する。

### Claude Code

- 新しい Claude Code session を repository root で開始する。
- `.claude/skills/` discovery wrapper が認識されるかを確認する。
- wrapper 経由で canonical Skill を実際に読んだことが観測できる場合のみ、選択済みとして記録する。

### GitHub Copilot

- 新しい Copilot Chat session を repository root / VS Code workspace で開始する。
- `.github/copilot-instructions.md` および path instruction の適用状況を確認する。
- Copilot surface に native Skill invocation がない場合、instruction を読んだことと task routing の回答を notes に記録し、`observed_skills` は空のままにする。instruction 適用は native Skill selection の代替ではない。

## 結果の記録と評価

各 runtime ごとに別の `agent-skill-results.json` を作成するか、実行直後に別名で退避する。最低限、次を残す。

- runtime 名・version、実行日時、repository revision
- case ID
- 実際に選択された Skill 名と順序（`observed_skills`）
- available Skills / instructions の観測結果
- unavailable、逸脱、手動誘導の有無

記録済みの結果は次で評価する。

```powershell
uv run --locked python scripts/agent_skill_smoke.py evaluate --results agent-skill-results.json
```

この評価は、全 case が記録されて初めて `passed` になる。runtime が project Skill を発見できなかった case は失敗として隠さず、`unavailable` の根拠を notes に残す。runtime ごとに version や Skill discovery の能力が異なるため、評価結果を横断比較するときは Skill 名だけでなく観測方法も確認する。

## 完了判断

runtime ごとに、次を満たす場合に smoke 実施済みとする。

- 新 session・対象 revision・runtime version が記録されている。
- prompt case を期待値なしで投入した。
- native Skill selection と instruction-only routing を区別して記録した。
- `agent-skill-results.json` の評価結果、または unavailable の理由が残っている。

この smoke は runtime の実装・設定・version に依存する。repository-side contract test が成功していても、runtime smoke の未実施・unavailable を成功に読み替えない。
