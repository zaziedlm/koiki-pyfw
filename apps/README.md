# apps/

`apps/` は、このリポジトリが表すシステム固有の backend API 実装の配置先です。

この配下には、`koiki-fw` の framework / reference app 機能を利用しながら、業務アプリ固有の API、model、schema、service などを置きます。

## 配置方針

- `components/`
  - upstream が保守する reusable framework / starter template
- `apps/`
  - downstream が保守する business-specific backend implementation

`components/` から `apps/` を参照してはいけません。
依存方向は `apps/ -> components/` のみです。

業務アプリ固有 API の router 登録や ASGI composition は、`components/` ではなく `apps/` 側で所有します。

業務アプリ固有 model の Base は、既定では `koiki_ref_app.db.base.Base` を利用します。
これは `libkoiki.db.base.Base` と registry / metadata を共有しており、migration target に乗せやすい設計です。
業務固有の主キー・tenant_id・監査カラムなど独自カラム設計が必要な場合のみ、`apps/db/base.py` で独自 Base を定義します。

詳細は `docs/dev/apps-plugin-composition-plan.ja.md` を参照してください。

## 推奨レイアウト

```text
apps/
  asgi.py
  api/
    v1/
      router.py
      endpoints/
  core/
  db/
    base.py
  models/
  schemas/
  services/
  repositories/
```

すべてのディレクトリが必須ではありません。
案件要件に応じて必要なものだけ作成します。

## 運用ルール

- reusable 化できる変更は `apps/` に閉じず、`components/libkoiki` または `components/koiki_ref_app` へ還元する
- customer 固有 API、workflow、private integration は `apps/` に閉じる
- frontend 実装は引き続き root `frontend/` を標準配置とし、`apps/` は backend API 実装を中心に扱う
- `apps/` は root Python workspace member に含めない
