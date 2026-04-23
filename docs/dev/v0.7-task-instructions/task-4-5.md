# Task 4-5: Stage 4 結果検証

## 目的

component move 前に、`koiki_ref_app`、`frontend/`、`apps/`、copy-first 更新モデルを含むテンプレート戦略が十分固まっているかを確認する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-4-1.md`
- `docs/dev/v0.7-task-instructions/task-4-2.md`
- `docs/dev/v0.7-task-instructions/task-4-3.md`
- `docs/dev/v0.7-task-instructions/task-4-4.md`

## 事前条件

- [Task 4-4](./task-4-4.md) が完了している

## 確認観点

- `koiki_ref_app` の template 境界
- root `frontend/` の starter 境界
- `apps/` の project-specific 境界
- copy-first update モデルの実務妥当性

## 実施手順

1. Task 4-1 から 4-4 の結論を横断確認する
2. `koiki_ref_app` / `frontend/` / `apps/` の責務が重複していないか確認する
3. downstream 採用時の最小導入単位と update 単位が説明可能か確認する
4. Stage 5 の `components/` / `apps/` 実移動に対して不足論点がないか確認する
5. Stage 4 完了可否を判定する

## 成果物

- Stage 4 検証メモ
- Stage 5 への申し送り

## 検証

- Stage 5 で構造を動かしても後戻りしない程度にテンプレート定義が固まっている
- downstream 採用モデルを一貫した言葉で説明できる

## 完了条件

- Stage 5 に着手可能と判断できる

## 実施結果

Task:

- Task 4-5: Stage 4 結果検証

変更内容:

- Task 4-1 から 4-4 の結論を横断確認し、Stage 4 のテンプレート戦略を次の4層で説明できる状態に整理した
  - `components/libkoiki`
    - reusable framework
  - `components/koiki_ref_app`
    - backend starter / reference app
  - root `frontend/`
    - frontend starter / BFF template
  - `apps/`
    - downstream project-specific code
- `koiki_ref_app` / `frontend/` / `apps/` の責務重複も点検し、次のように整理した
  - `koiki_ref_app`
    - backend 側 starter の composition root
    - sample / reference domain
    - app-specific bootstrap
  - `frontend/`
    - UI / BFF starter
    - 認証 UI / route protection / API proxy の starter
  - `apps/`
    - customer 固有 backend / frontend / composition
  - この3つは責務が重なっていない
- downstream 採用時の導入単位も一貫して説明できる状態になった
  - backend のみ
    - `libkoiki`
    - `koiki_ref_app`
  - backend + UI/BFF
    - `libkoiki`
    - `koiki_ref_app`
    - root `frontend/`
  - customer 固有化後
    - `apps/<project-slug>/backend`
    - `apps/<project-slug>/frontend`
- copy-first update モデルも、責務境界を壊さず説明できることを確認した
  - update 単位は `libkoiki` / `koiki_ref_app` / `frontend/`
  - downstream 側は patch / minor / breaking を見て選択取り込みする
  - customer 固有変更は `apps/` に閉じる
  - reusable 改善だけ upstream に還流する
- Stage 5 の実移動前提も点検し、次の前提が揃っていることを確認した
  - `components/` は upstream managed assets
  - `apps/` は downstream managed assets
  - `frontend/` は root 維持
  - `koiki_ref_app` は `app/` の単純 rename ではなく starter backend package
  - `todo` は `koiki_ref_app` 側へ寄せる方針
- Stage 5 へ渡す実務上の申し送りも明示した
  - path 移動時に README / docs の責務説明を追随する
  - `apps/` はまず予約領域として導入し、案件実コードは後続で置けるようにする
  - `frontend/` は root 維持前提のまま、backend path 変更に追随する説明だけ更新する
  - Skills 再編は実構造ができてから接続する

未解決事項:

- `koiki_ref_app` README、root `frontend/README`、template release note の具体フォーマットは Stage 5 以降で具体化が必要
- `business_clock` や starter domain の最終構成は、実移動時に最小 starter を意識して微調整の余地がある
- `apps/` の実案件レイアウト例は、最初の案件またはサンプル追加時に補強してよい

検証結果:

- `koiki_ref_app` / `frontend/` / `apps/` / copy-first 更新戦略の間に重大な矛盾は見つからなかった
- Stage 5 の `components/` / `apps/` 実移動に必要な責務定義は揃っている
- Stage 4 は完了、Stage 5 着手可と判断した

次タスクへ渡す事項:

- Stage 5 では責務定義を崩さず、まず path / package / import / docs の整合を取る
- `components/libkoiki` と `components/koiki_ref_app` の移設は、Stage 3 までに定義した app factory / ORM bootstrap / compatibility path を前提に進める
- `apps/` は実案件のための予約領域として先に導入し、構造上の責務を明確化する

## 次タスク

- Stage 5 / Task 5-1
