# Task 4-3: 案件固有 code の `apps/` 配置ルール定義

## 目的

`components/` と `apps/` の境界を運用可能にし、案件固有 code をどの時点で `apps/` に出すか、どのような名前で管理するかを定義する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-4-1.md`
- `docs/dev/v0.7-task-instructions/task-4-2.md`

## 事前条件

- [Task 4-2](./task-4-2.md) が完了している

## 確認観点

- どの時点で `apps/` を使うか
- `components/` に残すべきものとの境界
- `apps/` 配下の naming rule
- downstream project-specific code を upstream 側へ混入させない運用

## 実施手順

1. `libkoiki` / `koiki_ref_app` / `frontend/` の責務整理を前提に、案件固有 code の判定基準を整理する
2. `apps/` を使い始めるタイミングを定義する
3. `apps/` 配下の標準レイアウトと naming rule を定義する
4. customer 固有 code を `components/` に入れないルールを明文化する
5. reusable 変更を upstream へ戻す判断基準を整理する

## 成果物

- `apps/` 配置ルール定義メモ
- `components/` / `apps/` 判定基準

## 検証

- downstream 実案件の置き場に迷いがない
- customer 固有 code を `components/` に入れない判断基準が説明できる

## 完了条件

- Task 4-4 で copy-first 更新戦略を `apps/` 前提で整理できる

## 実施結果

Task:

- Task 4-3: 案件固有 code の `apps/` 配置ルール定義

変更内容:

- `apps/` の役割を次のように定義した
  - downstream / customer-specific application code の配置先
  - upstream が保守する reusable component や starter template の配置先ではない
  - copy-first で複製した後に案件固有化した backend / frontend / composition を閉じ込める領域
- `apps/` を使い始めるタイミングを次のように定義した
  - `koiki_ref_app` / root `frontend/` をそのまま template として評価している段階では使わない
  - 次のいずれかが始まった時点で `apps/` へ出す
    - customer 固有 workflow の追加
    - customer 固有 branding / UI の追加
    - 特定 tenant / deployment 専用の API や integration の追加
    - upstream へ戻さない private domain model / schema / settings の追加
    - 納品物として独立した backend / frontend を持つ必要が出た時
- `components/` に残すべきものも再確認し、判定基準を次のように整理した
  - `components/` に残すもの
    - 複数案件で再利用する前提の framework capability
    - starter template の標準 bootstrap
    - default sample / reference domain
    - upstream が継続保守する共通改善
  - `apps/` に置くもの
    - customer 固有 domain
    - customer 固有 UI / BFF
    - customer 固有 external integration
    - 特定案件でしか使わない settings / deployment composition
    - upstream へ戻さない前提の quick customization
- `apps/` 配下の naming rule も次のように定義した
  - 第1階層は project slug とし、lowercase kebab-case を使う
    - 例: `apps/acme-portal/`
    - 例: `apps/city-ops/`
  - project slug 配下は役割単位で分ける
    - `apps/<project-slug>/backend/`
    - `apps/<project-slug>/frontend/`
    - 必要なら `apps/<project-slug>/shared/`
    - 必要なら `apps/<project-slug>/ops/`
  - backend / frontend の両方がない案件では、必要なものだけ作る
  - `components/` と同じ package 名を `apps/` で再利用しない
- backend / frontend の配置ルールも具体化した
  - root `frontend/` は upstream starter のまま維持する
  - customer 固有 frontend は `apps/<project-slug>/frontend/` に置く
  - `koiki_ref_app` は upstream starter backend のまま維持する
  - customer 固有 backend は `apps/<project-slug>/backend/` に置く
- `components/` と `apps/` の依存方向も整理した
  - `apps/` は `components/` を参照できる
  - `components/` は `apps/` を参照しない
  - reusable 化したい変更は `apps/` で直接複製するのではなく、`components/` へ昇格させる
- customer 固有 code を `components/` に入れないルールを次のように明文化した
  - customer 名、tenant 名、個別契約、個別運用条件に依存する code は `components/` に入れない
  - upstream の default behavior を壊す条件分岐は `components/` ではなく `apps/` で吸収する
  - reusable かどうか迷う変更は、少なくとも 2 案件以上で共通化価値が見えるまでは `apps/` 側に置く
- upstream へ戻す判断基準も定義した
  - reusable / generic / template default に昇格できるものは `components/libkoiki` または `components/koiki_ref_app` に戻す
  - customer 固有判断、branding、private integration は `apps/` に閉じる
  - `frontend/` に戻すのは、複数案件で有効な starter 改善に限る
- downstream 採用時の標準像も整理した
  - upstream template 評価段階
    - `components/libkoiki`
    - `components/koiki_ref_app`
    - root `frontend/`
  - downstream 実案件段階
    - `apps/<project-slug>/backend`
    - `apps/<project-slug>/frontend`
    - 必要に応じて `shared` / `ops`
- `apps/` が「なってはいけないもの」も明文化した
  - upstream template の正式な保管場所
  - reusable 改善の放置場所
  - 命名規則のない雑多な sandbox
  - `components/` を迂回した framework fork 集積場所

未解決事項:

- `apps/<project-slug>/backend` を Python package としてどう切るかは Stage 5 以降の実装時に具体化が必要
- `shared/` を project 配下の標準ディレクトリにするか、案件ごとに optional 扱いにするかは後続判断でよい
- 複数 backend service を持つ案件で `backend/` の下をさらに分ける naming rule は、実案件の出現後に補足してよい

検証結果:

- downstream 実案件の backend / frontend をどこへ置くか説明できる状態になった
- `components/` と `apps/` の依存方向が明確になり、customer 固有 code を upstream 側に混ぜない判断基準が定まった
- Task 4-4 で copy-first 更新戦略を downstream 実案件構成まで含めて整理できる前提が揃った

次タスクへ渡す事項:

- Task 4-4 では、`koiki_ref_app` / root `frontend/` を複製して `apps/` へ展開した後の update 方針を整理する
- Stage 5 では `apps/` を予約領域として導入し、まずは構造と説明責務を整える
- Skills の段階再編は、実リポ構成が固まった後に `components/` / `apps/` 境界へ接続する

## 次タスク

- [Task 4-4](./task-4-4.md)
