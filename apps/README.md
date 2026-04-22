# apps/

`apps/` は案件固有アプリケーションの配置先です。

この配下には、downstream 側で個別に保守する backend / frontend / ops などを置きます。

## 配置方針

- `components/`
  - upstream が保守する reusable framework / starter template
- `apps/`
  - downstream が保守する project-specific application

`components/` から `apps/` を参照してはいけません。
依存方向は `apps/ -> components/` のみです。

## 推奨レイアウト

```text
apps/
  <project-slug>/
    backend/
    frontend/
    shared/
    ops/
```

すべてのディレクトリが必須ではありません。
案件要件に応じて必要なものだけ作成します。

## 運用ルール

- reusable 化できる変更は `apps/` に閉じず、`components/libkoiki` または `components/koiki_ref_app` へ還元する
- customer 固有 workflow、branding、private integration は `apps/` に閉じる
- root `frontend/` は starter template として維持し、案件固有 frontend は `apps/<project-slug>/frontend` に置く
- `apps/` は root Python workspace member に含めない

