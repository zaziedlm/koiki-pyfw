# Task 4-1: `koiki_ref_app` のテンプレート責務定義

## 目的

参照実装とテンプレートの境界を明確にし、`koiki_ref_app` に残すもの、`libkoiki` に上げるもの、`apps/` に行くべきものを定義する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-3-2.md`
- `docs/dev/v0.7-task-instructions/task-3-4.md`
- `docs/dev/v0.7-task-instructions/task-3-6.md`

## 事前条件

- [Task 3-6](./task-3-6.md) が完了している

## 確認観点

- `koiki_ref_app` に残すもの
- `libkoiki` に上げるもの
- `apps/` に行くべきもの
- copy-first テンプレートとしての最小構成

## 実施手順

1. Stage 3 までに確定した境界をテンプレート観点で再分類する
2. `koiki_ref_app` の責務を backend starter として定義する
3. `libkoiki` に昇格すべき reusable 領域を定義する
4. `apps/` に置くべき案件固有 code を定義する
5. downstream 採用時の最小導入単位を記録する

## 成果物

- `koiki_ref_app` 責務定義メモ
- `libkoiki` / `koiki_ref_app` / `apps/` 分担表

## 検証

- downstream 採用時の境界が明確である
- `koiki_ref_app` が framework 本体や案件固有アプリ本体と混線していない

## 完了条件

- Task 4-2 で `frontend/` のテンプレート責務を接続できる

## 実施結果

Task:

- Task 4-1: `koiki_ref_app` のテンプレート責務定義

変更内容:

- Stage 3 までの前提をテンプレート観点で再整理し、`koiki_ref_app` の位置づけを次のように定義した
  - `koiki_ref_app` は「現行 app の移設先」ではなく
  - `libkoiki` を土台にした backend starter / reference app / template package
  - downstream プロジェクトが copy-first で取り込むための出発点
- `koiki_ref_app` に残す責務を次のように定義した
  - backend starter としての composition root
    - `create_app()`
    - lifecycle / bootstrap wiring
    - `app.main:app` から移る最終的な ASGI entrypoint
  - app-specific bootstrap
    - SSO / SAML bootstrap
    - app 固有 background task
    - app 固有 degraded startup policy
  - reference / starter domain
    - `todo` 系一式
    - business_clock 等の reference business feature
  - app-level configuration / ops ownership
    - Alembic
    - app 固有 env / settings glue
    - app-level tests
  - template として downstream が読みやすい bootstrap / wiring のサンプル
- `koiki_ref_app` に残さないものも明文化した
  - reusable framework middleware / auth / persistence / schema infrastructure
  - app をまたいで使える generic helper
  - customer 固有の業務 code
- `libkoiki` に上げるものを次のように定義した
  - reusable framework capability
    - auth
    - config
    - logging
    - middleware
    - persistence
    - exception handling
    - monitoring helper
    - Redis / limiter bootstrap helper
  - app factory を支える reusable helper
    - common FastAPI app settings helper
    - common middleware registration helper
    - common exception handler registration helper
    - common lifecycle helper
  - downstream 複数案件で再利用される extension point
  - ドメイン非依存の generic service / repository / schema
- `apps/` に行くべきものも次のように定義した
  - customer / tenant 固有の業務 code
  - 案件専用の backend
  - 案件専用の frontend
  - upstream へ戻さない前提のカスタマイズ
  - 個別納品用の composition
- `koiki_ref_app` と `apps/` の違いも明確にした
  - `koiki_ref_app`
    - upstream が保守する starter template
    - 複数案件の共通出発点
  - `apps/`
    - downstream / 個別案件が保守する実アプリ
    - 共通スターターから分岐した納品物 / 運用物
- Stage 3 の `todo` 判断も取り込み、`koiki_ref_app` の starter domain 方針を次のように固定した
  - `todo` は `libkoiki` 本体ではなく `koiki_ref_app` の sample/reference domain
  - したがって `koiki_ref_app` は「空の wiring だけの箱」ではなく、最小限の starter domain を持つ
- `koiki_ref_app` の最小構成も整理した
  - app factory / ASGI entry
  - app bootstrap modules
  - app-specific router
  - starter domain (`todo`, business clock, auth integration sample)
  - migration / tests
  - template README / bootstrap guidance
- downstream 採用時の最小導入単位も定義した
  - backend のみ採用する場合
    - `libkoiki`
    - `koiki_ref_app`
  - 標準 UI / BFF も採用する場合
    - `libkoiki`
    - `koiki_ref_app`
    - root `frontend/`
  - customer 固有実装へ進む段階で
    - `apps/` へ案件 code を置く
- copy-first 前提での境界も整理した
  - downstream は `koiki_ref_app` を複製して開始する
  - upstream へ戻す価値がある reusable 変更は `libkoiki` か `koiki_ref_app` に還流する
  - customer 固有変更は `apps/` へ閉じる
- `koiki_ref_app` が「なってはいけないもの」も明文化した
  - framework 本体の dumping ground
  - customer 固有 code の蓄積場所
  - `frontend/` を含む monolithic product package
  - upstream と downstream の責務が混ざった巨大アプリ
- 分担表として次の3分割を確定した
  - `libkoiki`
    - reusable framework
  - `koiki_ref_app`
    - reusable backend starter / reference app
  - `apps/`
    - downstream project-specific code

未解決事項:

- `business_clock` を `koiki_ref_app` の starter domain として維持するか、より汎用的な sample へ置き換えるかは後続判断が必要
- `koiki_ref_app` に残す reference domain を `todo` だけに絞るか、SSO/SAML sample をどこまで含めるかは Stage 4 後半でさらに詰める余地がある
- `koiki_ref_app` README の実内容は Task 4-5 以降または Stage 5 実装時に具体化が必要

検証結果:

- downstream 採用時に `libkoiki` / `koiki_ref_app` / `apps/` の境界を説明できる状態になった
- `koiki_ref_app` が framework 本体でも customer 固有アプリでもない、中間の starter template だと明確になった
- Task 4-2 で `frontend/` の責務を接続するための backend 側テンプレート定義が揃った

次タスクへ渡す事項:

- Task 4-2 では、root `frontend/` を `koiki_ref_app` と組になる starter frontend として定義する
- Task 4-3 では、案件固有 code を `apps/` へ出す判定基準と naming rule をこの境界へ対応づける
- Task 4-4 では、copy-first 更新戦略を `koiki_ref_app` / `frontend/` / `apps/` の3層前提で整理する

## 次タスク

- [Task 4-2](./task-4-2.md)
