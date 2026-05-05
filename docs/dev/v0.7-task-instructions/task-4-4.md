# Task 4-4: テンプレート複製モデルの運用方針整理

## 目的

copy-first 前提のテンプレート配布を現実的に回せるようにし、upstream 変更の還流方針、patch / minor / breaking の扱い、複製時の最小導入単位を定義する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-4-1.md`
- `docs/dev/v0.7-task-instructions/task-4-2.md`
- `docs/dev/v0.7-task-instructions/task-4-3.md`

## 事前条件

- [Task 4-3](./task-4-3.md) が完了している

## 確認観点

- upstream 変更の還流方針
- patch / minor / breaking の扱い
- 複製時の最小導入単位
- downstream 側の update 手順

## 実施手順

1. copy-first 採用モデルの前提を再確認する
2. downstream への最小導入単位を整理する
3. patch / minor / breaking の update 期待値を定義する
4. upstream へ戻す変更と downstream に閉じる変更の流れを整理する
5. update 時に必要なドキュメント成果物を定義する

## 成果物

- copy-first 運用方針メモ
- downstream update ルール

## 検証

- downstream へのテンプレート配布と update が説明可能
- upstream / downstream の責務境界が update 時にも崩れない

## 完了条件

- Task 4-5 で Stage 4 のテンプレート戦略を総合検証できる

## 実施結果

Task:

- Task 4-4: テンプレート複製モデルの運用方針整理

変更内容:

- copy-first 採用モデルの前提を次のように固定した
  - downstream は upstream template を複製して開始する
  - downstream と upstream が同一 workspace や live sync を共有することは必須としない
  - update は自動同期ではなく、明示的な取り込み判断と手動マージを前提にする
  - reusable 改善は upstream に還流し、customer 固有変更は downstream `apps/` に閉じる
- downstream への最小導入単位を次のように定義した
  - backend starter のみ採用
    - `components/libkoiki`
    - `components/koiki_ref_app`
  - backend + UI/BFF starter を採用
    - `components/libkoiki`
    - `components/koiki_ref_app`
    - root `frontend/`
  - customer 固有実装へ進んだ段階
    - `apps/<project-slug>/backend`
    - `apps/<project-slug>/frontend`
    - 必要に応じて `shared` / `ops`
- update の単位も次のように整理した
  - `libkoiki`
    - framework capability update
  - `koiki_ref_app`
    - backend starter wiring / sample domain / auth integration update
  - `frontend/`
    - UI/BFF starter update
  - downstream は必要な単位だけ選択的に取り込む
- patch / minor / breaking の扱いを次のように定義した
  - patch
    - bugfix
    - security fix
    - doc correction
    - template default の小改善
    - downstream では原則取り込み推奨
  - minor
    - backward-compatible な starter 機能追加
    - optional integration 追加
    - reference UI / sample domain の拡張
    - downstream では案件都合に応じて選択取り込み
  - breaking
    - package path 変更
    - startup path 変更
    - config schema 変更
    - migration / auth / API contract の互換破壊
    - downstream では migration guide を確認した上で計画的に取り込む
- downstream update の期待値も次のように整理した
  - patch
    - 定期的に取り込む標準更新
  - minor
    - 必要性と差分コストを評価してから取り込む
  - breaking
    - 別タスクとして計画し、検証環境で確認後に取り込む
- upstream へ戻す変更の流れも定義した
  - 2案件以上で再利用価値が見える変更は upstream 候補
  - framework generic な改善は `libkoiki`
  - starter default として有効な改善は `koiki_ref_app` または root `frontend/`
  - customer 固有 branding / workflow / private integration は upstream へ戻さない
- downstream に閉じる変更の判断も明文化した
  - customer 名、契約条件、tenant 条件に依存する変更
  - 特定運用環境だけで必要な deployment composition
  - 特定案件でしか使わない BFF route、UI flow、業務 API
  - upstream の default template を複雑化させるだけの条件分岐
- update 時に upstream が出すべき成果物も整理した
  - release note
  - change summary
  - patch / minor / breaking の区分
  - breaking の場合は migration guide
  - 必要に応じて diff 観点
    - `libkoiki`
    - `koiki_ref_app`
    - `frontend/`
- downstream 側の標準 update 手順も次のように整理した
  1. upstream release note を確認する
  2. 対象が patch / minor / breaking のどれか判定する
  3. 取り込む単位を決める
     - `libkoiki`
     - `koiki_ref_app`
     - `frontend/`
  4. downstream `apps/` との競合有無を確認する
  5. template 側変更を手動で取り込む
  6. backend / frontend / migration / auth を検証する
- copy-first 運用で避けるべきことも整理した
  - upstream と downstream の live 共有前提で説明すること
  - customer 固有変更を template default へ安易に戻すこと
  - patch / minor / breaking の区別なしに一括更新を推奨すること
  - template の update を無期限に undocumented のまま流すこと
- Stage 4 時点のテンプレート更新戦略を次の一文で説明できるようにした
  - upstream は `libkoiki` / `koiki_ref_app` / `frontend/` の改善をバージョンと文書で公開し、downstream は必要な更新だけを copy-first 前提で選択的に取り込む

未解決事項:

- release note の置き場を `docs/`、GitHub Releases、CHANGELOG のどれに寄せるかは Stage 5 以降で決めてよい
- downstream update 支援のために差分テンプレートやチェックリストを追加するかは後続判断でよい
- `apps/` を含む実案件で patch / minor / breaking の具体例を補強するのは実案件出現後でよい

検証結果:

- downstream へのテンプレート配布単位と update 判断基準を説明できる状態になった
- patch / minor / breaking の扱いが明確になり、copy-first 運用が「複製しっぱなし」ではなく選択的更新モデルであると整理できた
- Task 4-5 で `koiki_ref_app` / `frontend/` / `apps/` をまとめて検証する前提が揃った

次タスクへ渡す事項:

- Task 4-5 では Stage 4 全体として、template strategy が Stage 5 の実移動前に十分固まっているかを検証する
- Stage 5 では `components/` / `apps/` の実導入時に、この copy-first 運用を前提に README / docs の責務説明を追随させる
- Skills の段階再編は、実構造確定後に template / consumer への説明責務として再接続する

## 次タスク

- [Task 4-5](./task-4-5.md)
