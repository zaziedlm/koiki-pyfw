# .aidx/loop-design/

AI駆動開発 標準化フレームワーク（D-02 フィードバックループ設計書）に基づく、
ループ設計・実践記録の管理領域です。

## この領域の役割

`.aidx/` は、AI駆動開発フレームワークがプロジェクトに持ち込む**運用領域**です。
プロジェクトが元から持つAIガイダンス資産（`docs/agent/`）とは役割を分けています。

| 領域 | 位置づけ | 正本 |
| --- | --- | --- |
| `.aidx/loop-design/` | フレームワーク由来の運用記録（ループ設計・実践記録） | D-02 付録A |
| `openspec/` | Specの一次情報源（機能Spec・実装Spec単位） | OpenSpec標準 + D-03 |
| `docs/agent/` | プロジェクト固有のAIガイダンス・Skills正本 | 本リポジトリ |

`.aidx/` にSkillsは置きません。Skillsの正本は `docs/agent/skills/` です
（D-07 6-2「正本領域はプロジェクトの既存AIガイダンス領域に従う」）。

## ファイル構成

```
.aidx/loop-design/
├── README.md                     ← 本ファイル
├── SPEC-MAP-TEMPLATE.md          ← 全体地図テンプレート（変更しない）
├── feedback-loop-TEMPLATE.md     ← Spec単位ループ記録テンプレート（変更しない）
├── examples/
│   └── SPEC-MAP-EXAMPLE-start.md ← 着手時の姿（記入例）
└── <案件名>/
    ├── SPEC-MAP.md               ← 案件の全体地図（適用オーナーのみが編集）
    └── SPEC-<番号>_<change-name>/
        └── feedback-loop.md      ← Loop #1〜N の記録（Spec担当者が編集）
```

---

## ★ SPEC-MAPは「台帳」です

**SPEC-MAPは著述する文書ではなく、案件の進行につれて埋まっていく台帳です。**
着手時点で全欄が埋まることはなく、**空欄は未完成を意味しません。**

実際には起きていないことを想像で埋めると、台帳としての信頼性が落ちます。
空欄のまま置くことが、この文書では正しい振る舞いです。

**着手時に判断を要するのは「実装Spec単位一覧」（第4節）の分解だけです。**
案件をどの単位に割るかがプロジェクトの進めやすさを決めます。ここに時間をかけ、
残りは事務作業として埋めるか、ループを回して自然に埋まるに任せてください。

各セクションの記入タイミングは `SPEC-MAP-TEMPLATE.md` の第0節にまとめています。
着手直後の実際の姿は `examples/SPEC-MAP-EXAMPLE-start.md` を参照してください。

これに対し、機能Spec・実装Spec単位のSpecファイルは**スナップショット**です。
ある時点で完成しうる文書であり、書き上げることを目指します。性質が異なるため、
SPEC-MAPに同じ完成度を求める必要はありません。

なお `feedback-loop.md` は追記式で、構造そのものが時間軸を持っています。
Loop #1 を書いた時点で Loop #2 が空なのは当然であり、上記の注意は不要です。

---

## 使い方

### 案件を開始するとき

1. `<案件名>/` ディレクトリを作成する
2. `SPEC-MAP-TEMPLATE.md` をコピーし、`<案件名>/SPEC-MAP.md` として配置する
3. 第0節（説明用セクション）を削除する
4. 基本情報・ループ共通設定を記入する
5. ①要件定義の後、機能Spec一覧・実装Spec単位一覧・完了依存を記入する

### 実装Spec単位を追加するとき

1. `<案件名>/SPEC-<番号>_<change-name>/` ディレクトリを作成する
2. `feedback-loop-TEMPLATE.md` をコピーし、`feedback-loop.md` として配置する
3. `SPEC-MAP.md` の実装Spec単位一覧に行を追記する

ディレクトリ名の `<番号>` は番台採番規則（D-03 4-3）に従います。
1つの機能Specに1つの番台帯（100／200／300…）を割り当て、
配下の実装Spec単位に番台内の連番を振ります。案件開始時に固定し、欠番は再利用しません。

### ループを1周回したとき

`feedback-loop.md` に Loop #N のセクションを追記します。上書きせず、必ず追記します。
ループ完了時にA/B/C判定とHarvest候補フラグ判定を記録し、
`SPEC-MAP.md` の状態欄・進捗サマリを更新します。

## 編集ルール

- **テンプレート2ファイルは変更しない。** 改善が必要な場合は標準化責任者へ提起する
- `SPEC-MAP.md` は適用オーナーのみが編集する（複数人が触ると全体地図が壊れる）
- `feedback-loop.md` はSpec単位で分かれているため、並行作業してもコンフリクトしない
- 記録は「AIを使ったか」ではなく「**人が何を判断したか**」を残す

## openspec/ との関係

| 記録するもの | 置き場所 |
| --- | --- |
| Specの内容そのもの（振る舞い・制約・受入条件） | `openspec/` |
| Specに至る過程・人の判断・ループの学び | `.aidx/loop-design/` |

`openspec/changes/<change-name>/` はアーカイブ時にパスが変わるため、
`SPEC-MAP.md` から相対リンクは張りません。change-name（文字列）をキーとして
一覧管理し、参照が必要な場合はリポジトリ内検索で特定します（D-02 A-2③）。

## OpenSpec（OPSX）コマンドとの対応タイミング

`openspec new` / `opsx:*` コマンド群は `.aidx/loop-design/` の存在を一切意識しません。
両者は独立した仕組みであるため、**OPSXの各ステップが完了した直後に、
人またはエージェントが明示的に `.aidx/loop-design/` を更新する**必要があります。
自動では連動しません。

| OPSXステップ | 確定する成果物 | D-02ループ | `.aidx/loop-design/` で行うこと |
| --- | --- | --- | --- |
| `opsx:new` | change ディレクトリ作成 | ①要件定義 開始 | 案件が未着手なら `<案件名>/` を新規作成し、`SPEC-MAP.md`（第1〜2節）を配置する。既存案件なら何もしない |
| `opsx:propose` / `opsx:ff`（proposal.md・デルタSpec確定） | 機能Spec／デルタSpec | ①要件定義 | `SPEC-MAP.md` 第3節・第4節に行を追加する（Spec番号は仮採番）。`<Spec単位>/feedback-loop.md` を新規作成し①要件定義欄を記入する |
| `opsx:continue` / `opsx:update`（design.md確定） | 設計判断 | ②設計 | `feedback-loop.md` ②設計欄を記入する |
| `opsx:apply`（tasks実装） | 実装コード | ③実装（＋④テスト） | `feedback-loop.md` ③実装欄、テストを書いた時点で④テスト欄を記入する |
| `opsx:verify` | 検証結果 | ⑤評価・改善の起点 | `feedback-loop.md` ④受入条件充足状況・⑤評価・改善欄を記入する |
| `opsx:sync` / `opsx:archive` | specs反映・archive | ループ完了 | `feedback-loop.md` のループ完了記録（次ループのパターン・Harvest候補フラグ）を記入する。`SPEC-MAP.md` 第4節の状態を完了に更新し完了日を記入、第7節 進捗サマリを再集計する |

この対応は `docs/agent/skills/koiki-spec-map-maintenance/SKILL.md` と
`docs/agent/skills/koiki-feedback-loop-recording/SKILL.md` の呼び出しタイミングの根拠です。
どちらのSkillも、対応するOPSXステップが実際に完了した後にのみ呼び出し、
計画段階やまだ発生していない事実で欄を埋めません。

## 関連ドキュメント

| 文書 | 参照する内容 |
| --- | --- |
| D-02 フィードバックループ設計書 | 5ステップ・人とAIの役割・A/B/C判定・設計シートの設計項目 |
| D-03 Spec記述標準 | 番台採番規則・Spec単位間の依存関係の記法・Specの書き方 |
| D-07 Skills体系設計書 | Spec Harvestの判断基準・Skillsの供給設計 |
| `.aidx/SPEC-CHEATSHEET.md` | Spec記述の1枚まとめ |
| `docs/agent/boundaries.md` | 本リポジトリのレイヤ配置ルール |
