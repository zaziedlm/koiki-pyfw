# Task 4-2: `frontend/` のテンプレート責務定義

## 目的

root `frontend/` をどのような starter frontend として扱うかを明文化し、`koiki_ref_app` との関係を定義する。

## 参照ファイル

- `docs/frontend-application-development-guide.md`
- `frontend/package.json`
- `docs/dev/v0.7-task-instructions/task-4-1.md`

## 事前条件

- [Task 4-1](./task-4-1.md) が完了している

## 確認観点

- backend starter との関係
- BFF、認証、UI starter の責務
- framework 本体との境界

## 実施手順

1. `frontend/` の現在の機能範囲を整理する
2. `koiki_ref_app` との結合点を整理する
3. `frontend/` に残す starter 責務を定義する
4. `libkoiki` や `apps/` に行くものとの境界を定義する
5. downstream 採用時の最小導入単位を記録する

## 成果物

- `frontend/` テンプレート責務定義メモ
- `koiki_ref_app` と `frontend/` の関係整理

## 検証

- `frontend/` が framework 本体ではなくテンプレート資産であることが明確
- backend starter との境界が明確

## 完了条件

- Task 4-3 で `apps/` 配置ルールへ接続できる

## 実施結果

Task:

- Task 4-2: `frontend/` のテンプレート責務定義

変更内容:

- `docs/frontend-application-development-guide.md` と `frontend/package.json` から、現在の `frontend/` の機能範囲を次のように整理した
  - Next.js 15 / React 19 ベースの UI 実装
  - Route Handlers を使った薄い BFF
  - Cookie ベース JWT + CSRF 認証フロー
  - Dashboard / login / task UI
  - React Query による backend 連携
  - middleware による route protection
- 上記を踏まえ、`frontend/` の位置づけを次のように定義した
  - framework 本体ではない
  - `koiki_ref_app` と組になる root-level starter frontend
  - downstream が copy-first で採用する標準 UI / BFF テンプレート
- `koiki_ref_app` との関係も次のように整理した
  - `koiki_ref_app`
    - backend starter
    - FastAPI / auth / bootstrap / reference domain
  - `frontend/`
    - frontend starter
    - Next.js / BFF / cookie auth / dashboard UI
  - この2つは組みになったテンプレート束として扱うが、同一 package にはしない
- `frontend/` に残す starter 責務を次のように定義した
  - 認証 UI / UX の starter
    - login screen
    - auth guard
    - logout flow
  - BFF / Route Handler の starter
    - `/api/auth/*`
    - `/api/todos/*`
    - backend FastAPI への proxy パターン
  - dashboard / task 管理など、starter として有用な reference UI
  - cookie / CSRF / API client の共通 frontend wiring
  - downstream が AI エージェントと一緒に拡張しやすい UI structure
- `frontend/` に残さないものも明文化した
  - `libkoiki` の framework 実装
  - backend package の内部 bootstrap
  - customer 固有 UI / branding / workflow
  - downstream 個別案件専用の BFF / UI code
- `libkoiki` / `koiki_ref_app` / `apps/` との境界も次のように整理した
  - `libkoiki`
    - backend reusable framework
  - `koiki_ref_app`
    - backend starter template
  - `frontend/`
    - frontend starter template
  - `apps/`
    - downstream project-specific frontend / backend
- `frontend/` が root 維持である理由も整理した
  - Python workspace member ではない
  - package manager も Node 系で別
  - backend template と組ではあるが、無理に `components/` へ押し込まない方が構造が読みやすい
  - AI エージェントにも「frontend starter はここ」と一目で伝わる
- downstream 採用時の最小導入単位も定義した
  - backend のみ必要
    - `libkoiki`
    - `koiki_ref_app`
  - UI / BFF も必要
    - `libkoiki`
    - `koiki_ref_app`
    - `frontend/`
  - customer 固有化へ進む段階
    - 案件専用 frontend は `apps/` 配下へ置く
- `frontend/` が「なってはいけないもの」も整理した
  - すべての案件 UI を抱え込む共有アプリ
  - framework docs なしでは理解できない opaque な BFF
  - backend template と不可分の monolith package
  - customer 固有 branding / workflow の集積場所
- copy-first 前提での運用も明文化した
  - downstream は `frontend/` を複製して出発できる
  - reusable な frontend 改善は upstream `frontend/` へ還流する
  - customer 固有変更は `apps/` 側へ閉じる

未解決事項:

- `frontend/` に含める reference UI を `task/todo` 中心で維持するか、より汎用 dashboard starter に寄せるかは後続判断が必要
- BFF をどこまで template 標準に含めるかは、将来の downstream 利用形によって微調整の余地がある
- `frontend/README.md` の template 向け再整理は Stage 4 後半または Stage 5 実装時に必要

検証結果:

- `frontend/` が framework 本体ではなく、`koiki_ref_app` と組になるテンプレート資産だと明確になった
- backend starter との境界と downstream 採用単位を説明できる状態になった
- Task 4-3 で案件固有 frontend を `apps/` へ出す運用ルールへ接続する前提が揃った

次タスクへ渡す事項:

- Task 4-3 では、案件固有 frontend / backend を `apps/` 配下へ配置する naming rule と運用境界を定義する
- Task 4-4 では、copy-first 更新戦略を backend starter と frontend starter のペア前提で整理する
- Stage 5 では `frontend/` は root 維持のまま、`components/` 移動と並行して説明責務を更新する

## 次タスク

- [Task 4-3](./task-4-3.md)
