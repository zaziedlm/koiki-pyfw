# テスト Warning フォローアップタスク整理

最終更新: 2026-04-09

## 1. 目的

本書は、`LOG-02` 関連テスト実行時に観測された warning を、
本筋の実装タスクとは分離して追跡できるよう整理した補助文書である。

対象 warning は、現時点ではテスト失敗を引き起こしていないが、
長期保守性、将来互換性、ORM 定義の健全性の観点から放置しない方がよい。

本書では warning を以下の観点で整理する。

- 発生箇所
- 現時点の影響
- 推奨される改善タスク
- 完了条件

## 2. 総括

今回の warning は、いずれも `LOG-02` の sanitizer 実装自体の誤りを示すものではない。
ただし性質は同一ではなく、優先度は分けて扱うべきである。

- `SQLAlchemy SAWarning` は ORM 定義の曖昧さを示しており、先に是正した方がよい
- `PydanticDeprecatedSince20` は将来互換性の問題で、計画的な移行対象とする
- `config` 再読み込みにより同一 warning が増幅されているため、テスト実装面の整理余地もある

## 3. フォローアップタスク一覧

| ID | 種別 | 優先度 | 概要 |
| --- | --- | --- | --- |
| `WARN-01` | ORM 定義是正 | High | `LoginAttemptModel` の `attempted_at` / `created_at` 多重定義 warning を解消する |
| `WARN-02` | Pydantic v2 対応 | Medium | `@validator` を `@field_validator` 等へ移行し、非推奨 warning を解消する |
| `WARN-03` | テスト実装整理 | Low | `config` の reload による warning 増幅を抑え、テスト観測を安定化する |

## 4. 個別タスク

## 4.1 `WARN-01` LoginAttemptModel の SAWarning 解消

- 優先度: `High`
- 発生箇所:
  - [`login_attempt.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/models/login_attempt.py#L11)
- 観測 warning:
  - `Column object 'attempted_at' named directly multiple times, only one will be used: attempted_at, created_at`

### 問題

[`LoginAttemptModel`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/models/login_attempt.py#L10) では
`attempted_at` を定義した後、`created_at = attempted_at` と再代入しており、
同一 `Column` が複数名でモデルに現れている。

これは SQLAlchemy にとって曖昧なマッピングであり、
どちらの属性名を正式な ORM 属性として扱うかが不明瞭になる。

### 現時点の影響

- テストは通るが、ORM マッピングの可読性と安全性が低い
- 将来のクエリ、シリアライズ、Alembic 追従で混乱を生みやすい
- warning を無視する文化につながる

### 推奨対応

- `created_at = attempted_at` のエイリアス方式をやめる
- 必要なら以下のいずれかへ寄せる
  - `attempted_at` のみを正式カラムとし、Base の `created_at` 前提を見直す
  - `orm.synonym` 等で明示的に別名を与える
  - `Base` 側の timestamp 契約を見直し、`login_attempts` だけ例外扱いしない設計へ寄せる

### 完了条件

- `SAWarning` が消える
- `LoginAttemptModel` の timestamp 属性が一義的に理解できる
- 関連テストまたは model import 時に warning が再発しない

### テスト観点

- モデル import 時に warning が出ないこと
- `attempted_at` の値生成が従来どおり動くこと
- 必要なら `created_at` 互換を使っているコードが壊れていないこと

## 4.2 `WARN-02` Pydantic validator 非推奨 warning 解消

- 優先度: `Medium`
- 発生箇所:
  - [`config.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/config.py#L63)
- 観測 warning:
  - `PydanticDeprecatedSince20: Pydantic V1 style @validator validators are deprecated`

### 問題

[`Settings`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/config.py#L4)
では Pydantic v1 スタイルの `@validator` を使用している。
現行バージョンではまだ動作するが、将来の Pydantic v3 で除去される見込みである。

加えて、現ファイルは validator 記述の可読性も低く、
`assemble_cors_origins` と `assemble_db_url` 周辺の整形不備も見られる。

### 現時点の影響

- 直ちに動作不良ではない
- ただし将来アップグレード時に一括修正が必要になる
- warning ノイズが増え、真に重要な warning を見落としやすくなる

### 推奨対応

- `@validator(..., pre=True)` を `@field_validator(..., mode="before")` 相当へ移行する
- 必要に応じて `@model_validator` を使い、DB URL 組み立て責務を整理する
- `Settings` 初期化ロジックも含め、Pydantic v2 の流儀に寄せる

### 完了条件

- `config.py` 由来の `PydanticDeprecatedSince20` warning が消える
- CORS origin と DB URL 組み立てロジックが現行挙動を維持する
- 設定読み込みテストが追加または更新される

### テスト観点

- `BACKEND_CORS_ORIGINS` の文字列入力が従来どおり list 化されること
- `DATABASE_URL` 未指定時に DB URL が期待どおり構築されること
- 明示 `DATABASE_URL` 指定時に優先されること

## 4.3 `WARN-03` テスト時 warning 増幅の抑制

- 優先度: `Low`
- 発生箇所:
  - [`test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py#L1)
- 背景:
  - `logging_module` fixture で `libkoiki.core.config` を reload しているため、
    同じ warning が複数回観測されやすい

### 問題

warning 自体は `config.py` 由来だが、テスト実装の都合で件数が増えて見える。
これにより、warning の実数と観測数がずれ、レビュー時に過剰なノイズになる。

### 現時点の影響

- テスト失敗はしない
- ただし warning サマリの可読性が悪化する
- 本当に新規に増えた warning を見分けにくい

### 推奨対応

- fixture の import / reload 戦略を見直し、必要最小限の reload に抑える
- 可能なら module-scoped fixture で共通化する
- ただし `WARN-02` 解消後は自然に軽減する可能性があるため、優先度は低い

### 完了条件

- 同一 warning の重複観測が減る
- テスト前提を壊さずに `logging` helper テストが安定実行できる

### テスト観点

- `test_logging_sanitizer.py` が引き続き独立実行できること
- reload 削減後も environment 前提が壊れないこと

## 5. 推奨着手順

1. `WARN-01` LoginAttemptModel の SAWarning 解消
2. `WARN-02` Pydantic validator 非推奨 warning 解消
3. `WARN-03` テスト時 warning 増幅の抑制

## 6. 補足

これら warning 対応は、`LOG-02` 本体の blocker ではない。
ただし `WARN-01` は ORM 定義の明確化として価値が高く、
別作業として早めに解消しておく方が保守性に有利である。
