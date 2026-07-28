# Spec記述チートシート

*AI駆動開発フレームワーク D-03 準拠 ／ OpenSpec v1.6.0*
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

以下は `openspec validate` がエラーで教えてくれます。**暗記不要。**

SHALL/MUSTの不在 ／ Scenarioゼロ ／ `## Why` が50字未満 ／ 必須セクション欠落 ／ Requirement名の重複 ／ デルタゼロ ／ Requirement本文500字超（警告）

---

## ④ どこに何を書くか

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

## ⑤ コマンド

```bash
openspec new change <name>        # change の雛形を生成
openspec validate <name>          # 単体を検証
openspec validate --changes       # 進行中の change をすべて検証
openspec validate --all --strict  # 全件を厳格モードで検証（提出前）
openspec list                     # change 一覧（--specs で spec 一覧）
openspec show <name>              # 内容を表示
openspec archive <name>           # 完了した change を specs/ へ反映してアーカイブ
```

---

## ⑥ 書く前の3つの問い

1. **これは「何を満たすか」か、「どう実現するか」か。** 後者なら `design.md`
2. **Scenario が書けるか。** 書けないのは計測条件を決めていないから → 決めるか `design.md` へ
3. **異常系と境界値を飛ばしていないか。** 正常系だけのSpecはレビューで却下される

---

## ⑦ 迷ったときの参照先

| 知りたいこと | 参照先 |
| --- | --- |
| テンプレートの全体像・5種の書き分け | D-03 付録A |
| 記述強度・曖昧表現の禁止リスト | D-03 第5章 |
| 番台採番・依存関係の記法 | D-03 第4章 |
| レビュー観点・却下条件 | D-03 第7章 |
| Harvest候補フラグの判定基準 | D-07 4-3 |
| このリポジトリのレイヤ配置ルール | `docs/agent/boundaries.md` |
