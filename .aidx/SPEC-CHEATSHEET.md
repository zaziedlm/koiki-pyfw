# Spec記述チートシート

*AI駆動開発フレームワーク D-03 準拠 ／ OpenSpec v1.7.0（OPSX）*
**日常はこの1枚だけ。迷ったら D-03 付録A。**

---

## ① 骨格 ── これだけ覚える

```markdown
## ADDED Requirements                            ← ## は2つ。この配下にすべてを書く

### Requirement: 問い合わせ受付の受理             ← ### は3つ

- 【SHALL】システムは、必須項目が充足された問い合わせ登録要求を受理し、受付番号を発行しなければならない。
- 【SHALL NOT】システムは、受付番号を利用者の入力値から導出してはならない。

受付番号の採番方式は design.md を参照する。      ← ラベルなしの補足行は自由に書ける

#### Scenario: 正常系 - 必須項目充足              ← #### は4つ。ちょうど4つ
- **WHEN** 認可された利用者が必須項目を充足した要求を送信する
- **THEN** HTTP 201 と受付番号を返す

#### Scenario: 異常系 - 必須項目の欠損
- **WHEN** 必須項目が欠損した要求を送信する
- **THEN** HTTP 400 と欠損項目を示すエラーを返す

#### Scenario: 境界値 - 添付ファイル上限
- **WHEN** 10MB ちょうどのファイルを添付して送信する
- **THEN** 受理される
```

**5つのルール**

1. 規範文は行頭に `【SHALL】`（必須）または `【SHALL NOT】`（禁止）。**1行に1文**
2. **ラベルを太字にしない**（`**SHALL**:` は本文から除外される）
3. Requirement 1つにつき Scenario 1つ以上。**正常系・異常系・境界値**を揃える
4. **受入条件は書かない。** Scenario がそのまま受入条件
5. 実装方式・技術選定の理由は書かない → `design.md` へ

---

## ② 沈黙して失敗する4つ ★ここだけ暗記

エラーが出ずに壊れます。**気づけるのは自分だけです。**

| # | やってしまうこと | 何が起きるか |
| --- | --- | --- |
| 1 | Scenario見出しを `###`（3つ）にする | Scenarioが**存在しない扱い**になる |
| 2 | `## ADDED Requirements` の**外**に表や説明を書く | archive時に**消える** |
| 3 | `## Purpose` にHTMLコメント（`<!-- -->`）を残す | Purposeが破棄され **TBD** に置換される |
| 4 | ラベルを太字にする（`**SHALL**:`） | 規範文が本文から**除外**される |

---

## ③ 覚えなくてよいこと

以下は `npx openspec validate` がエラーで教えてくれます。**暗記不要。**

SHALL/MUSTの不在 ／ Scenarioゼロ ／ `## Why` が50字未満 ／ 必須セクション欠落 ／ Requirement名の重複 ／ デルタゼロ ／ Requirement本文500字超（警告）

ただし、validation通過は内容の正しさを保証しません。上記「沈黙して失敗する4つ」は目視でも確認します。

---

## ④ 役割分担 ── `.aidx` / `openspec` / Skill

| 場所・仕組み | 役割 |
| --- | --- |
| `openspec/specs/<capability>/` | 機能Spec。capability全体が将来も満たすべき振る舞いの正本 |
| `openspec/changes/<change-name>/` | 実装Spec単位。一回の具体的変更に対する proposal / delta spec / design / tasks |
| `.aidx/loop-design/<案件名>/` | 複数changeを横断するSpec一覧・番台・依存関係・進捗・フィードバックループ |
| `docs/agent/skills/koiki-spec-authoring/SKILL.md` | KOIKI-FW固有の日本語【SHALL】記法と成果物の内容ルール |
| OpenSpec標準の `openspec-*` Skills / `/opsx:*` | OPSXの成果物生成・実装・検証・同期・アーカイブのワークフロー |

**OpenSpec標準Skillがワークフローを定義し、`koiki-spec-authoring` が内容の書き方を定義します。両者が食い違う場合はKOIKI-FW固有ルールを優先します。**

`openspec/specs/` は「満たすべき状態」、実装コードは「現在の状態」の正本です。乖離を見つけたら、どちらかを黙って書き換えず `openspec/changes/` を起票します。

機能Specには配下changeの一覧を書きません。個々の実装Spec単位は必ず1つの機能Specに属し、その一覧・番台・依存関係・進捗は `SPEC-MAP.md` が管理します。

---

## ⑤ どこに何を書くか

| 書きたいこと | 書く場所 |
| --- | --- |
| 業務の背景・目的・利用場面 | `openspec/specs/<capability>/spec.md`（機能Spec） |
| capability全体に効く業務ルール | 同上の `## Requirements` |
| change のメタ情報・Harvest候補フラグ | `openspec/changes/<name>/proposal.md` の `## メタ情報` |
| 変更の理由・何が変わるか | 同 `proposal.md` の `## Why` / `## What Changes` |
| **振る舞い・制約・受入条件** | `openspec/changes/<name>/specs/<capability>/spec.md` |
| 実装方式・技術選定・トレードオフ | `openspec/changes/<name>/design.md` |
| 作業分解 | `openspec/changes/<name>/tasks.md` |
| Spec一覧・番台・依存関係・進捗 | `.aidx/loop-design/<案件名>/SPEC-MAP.md` |
| ループ記録・人の判断 | `.aidx/loop-design/<案件名>/SPEC-xxx_<name>/feedback-loop.md` |

---

## ⑥ AIチャットで使う `/opsx:*`

`/opsx:*` は**ターミナルではなく、AIコーディングアシスタントのチャット欄**へ入力します。

### Core（標準）

| コマンド | 用途 |
| --- | --- |
| `/opsx:explore` | コードを調査し、要件・方式・影響範囲を整理する。changeは作らない |
| `/opsx:propose <change-name>` | changeとplanning artifactsを一括生成する短縮ルート |
| `/opsx:apply <change-name>` | `tasks.md` に沿って実装し、完了チェックを更新する |
| `/opsx:sync <change-name>` | delta specを機能Specへ同期する。changeはactiveのまま |
| `/opsx:archive <change-name>` | 完了状態を確認し、必要ならsyncを提案して日付付きarchiveへ移動する |

### Expanded（段階レビュー用）

| コマンド | 用途 |
| --- | --- |
| `/opsx:new <change-name>` | changeのscaffoldだけを作る |
| `/opsx:continue [change-name]` | 依存関係上、次に作成可能なartifactを1つ作る。反復して使う |
| `/opsx:ff [change-name]` | 未作成のplanning artifactsを依存順に一括生成する |
| `/opsx:verify [change-name]` | proposal / specs / design / tasks と実装の整合を検証する |
| `/opsx:bulk-archive` | 複数の完了changeをまとめてarchiveする |
| `/opsx:onboard` | OPSXの一連の流れを対話形式で案内する |

Expandedコマンドを使える状態にする操作はターミナルで行います。

```bash
npx openspec config profile
npx openspec update
```

成果物の内容を修正するときは、対象changeと修正意図をAIへ自然文で指示します。実装中に方針が変わった場合も、コードだけで帳尻を合わせず、先に影響する proposal / specs / design / tasks を更新します。

---

## ⑦ ターミナルで使う `npx openspec`

このリポジトリは `package.json` でOpenSpec v1.7.0を固定しています。開発者ごとのグローバル版差異を避けるため、**CLIは `npx openspec` に統一**します。

```bash
npx openspec --version                       # リポジトリ固定版を確認
npx openspec list                            # active change 一覧（--specs で spec 一覧）
npx openspec show <change-name>              # change の状態と内容を表示
npx openspec validate <change-name> --strict # 対象changeを厳格検証
npx openspec validate --changes              # 進行中changeをすべて検証
npx openspec validate --all --strict          # 全件を厳格検証（提出前）
npx openspec view                            # 対話ダッシュボードを表示
npx openspec config profile                  # 利用するworkflow profileを選ぶ
npx openspec update                          # 選択したSkills / commandsを生成・更新
```

`npx openspec new change <name>` と `npx openspec archive <name>` は、AIを介さず雛形作成・archiveを行う補助CLIです。日常の成果物作成と完了処理は、文脈と整合性を確認できる `/opsx:new`・`/opsx:archive` を基本とします。

---

## ⑧ KOIKI-FW標準フロー（段階レビュー）

認証・認可、DB変更、外部サービス連携、API互換性変更など、影響やリスクがある変更はこの流れを使います。

```text
1. SPEC-MAPで所属Capability・Spec番号・依存関係を確認
2. /opsx:explore                         # 不明点がある場合
3. /opsx:new <change-name>
4. /opsx:continue <change-name>          # proposal
   レビュー
5. /opsx:continue <change-name>          # delta specs
   レビュー
6. /opsx:continue <change-name>          # design
   レビュー
7. /opsx:continue <change-name>          # tasks
   レビュー
8. SPEC-MAPへ登録・依存関係と状態を確定
9. /opsx:apply <change-name>
10. 最小範囲のテスト + npx openspec validate <change-name> --strict
11. /opsx:verify <change-name>
12. npx openspec validate --all --strict # PR・提出前
13. /opsx:sync <change-name>              # 同期を独立レビューする場合
14. /opsx:archive <change-name>           # 未同期ならsync確認あり
15. SPEC-MAPとfeedback-loopを完了状態へ更新
```

`/opsx:apply` はセクション単位に範囲を指定しても構いません。各テスト項目はdelta specのScenarioと1対1で対応させます。

### `SPEC-MAP.md` の更新タイミング

| タイミング | 更新内容 |
| --- | --- |
| change着手前 | 所属Capability・重複・依存・Spec番号を確認 |
| planning artifacts確定後 | change名、主分類、依存関係、状態を登録・確定 |
| archive後 | Archived状態、完了日、関連PR・コミット、学習事項、次Specへの影響、Harvest候補を記録 |

Proposalの試行錯誤中に台帳を細かく更新せず、planning artifactsが固まった時点とarchive後を正式更新点にします。

### `sync` と `archive`

- `/opsx:sync` はdelta specだけを `openspec/specs/` へ反映し、changeをactiveのまま残します。
- 長期change、並行changeが新しい機能Specを参照する場合、同期差分を別にレビューしたい場合は先にsyncします。
- 直ちに完了するchangeはsyncを省略でき、`/opsx:archive` が未同期deltaを検出したときにsyncを確認します。
- archive後に `.aidx` の進捗とfeedback-loopを更新して、単一changeの完了と案件全体の学習を接続します。

---

## ⑨ 短縮フロー（明確・小規模な変更）

軽微なUI変更、単純なCRUD、影響範囲が明確なバグ修正などは一括生成できます。バグ修正でも、修正後の振る舞いを表すScenarioを必ず記述します。

```text
1. SPEC-MAPで所属Capability・重複・依存を確認
2. /opsx:explore                         # 必要な場合だけ
3. /opsx:propose <change-name>           # proposal / specs / design / tasksを一括生成
4. 全artifactをレビュー
5. SPEC-MAPへ登録
6. /opsx:apply <change-name>
7. テスト + npx openspec validate <change-name> --strict
8. /opsx:verify <change-name>            # Expandedを有効化している場合
9. /opsx:archive <change-name>           # 必要ならarchive内でsync
10. SPEC-MAPとfeedback-loopを更新
```

途中まで段階レビューし、残りが明確になった時点で `/opsx:ff <change-name>` を使っても構いません。

---

## ⑩ 書く前・完了前の確認

### 書く前の3つの問い

1. **これは「何を満たすか」か、「どう実現するか」か。** 後者なら `design.md`
2. **Scenario が書けるか。** 書けないのは計測条件を決めていないから → 決めるか `design.md` へ
3. **異常系と境界値を飛ばしていないか。** 正常系だけのSpecはレビューで却下される

### 完了前チェック

```text
□ proposalのScopeを満たしている
□ 全Requirementを実装している
□ 全Scenarioに1対1で対応するテストがある
□ designと実装が一致している
□ tasksのチェック状態が実態と一致している
□ 「沈黙して失敗する4つ」を目視確認した
□ npx openspec validate <change-name> --strict が通る
□ PR・提出前に npx openspec validate --all --strict が通る
□ sync後の機能Specをレビューした、またはarchive時のsync結果を確認した
□ archive後にSPEC-MAPとfeedback-loopを更新した
```

---

## ⑪ 迷ったときの参照先

| 知りたいこと | 参照先 |
| --- | --- |
| テンプレートの全体像・5種の書き分け | D-03 付録A |
| 記述強度・曖昧表現の禁止リスト | D-03 第5章 |
| 番台採番・依存関係の記法 | D-03 第4章 |
| レビュー観点・却下条件 | D-03 第7章 |
| Harvest候補フラグの判定基準 | D-07 4-3 |
| KOIKI-FW固有のSpec記述規約 | `docs/agent/skills/koiki-spec-authoring/SKILL.md` |
| 実装Spec種別ごとのRequirement骨格 | `docs/agent/skills/koiki-spec-authoring/references/requirement-patterns.md` |
| このリポジトリのレイヤ配置ルール | `docs/agent/boundaries.md` |
| OpenSpecのプロジェクト設定 | `openspec/config.yaml` |
| OpenSpecの生成済みworkflow案内 | `openspec/AGENTS.md`（`npx openspec update` で生成。手編集しない） |
