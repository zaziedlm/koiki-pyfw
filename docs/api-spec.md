# API Specification

KOIKI-FW v0.7.0 の API ownership と実装配置は `docs/design_kkfw_0.7.0.md` を参照してください。

現行の API 実装場所:

- framework API: `components/libkoiki/src/libkoiki/api/`
- reference app API: `components/koiki_ref_app/src/koiki_ref_app/api/`
- downstream customer-specific API: `apps/`

FastAPI の OpenAPI schema は development 環境で `koiki_ref_app.asgi:app` を起動したうえで `/openapi.json` から確認します。Production では docs / redoc / openapi endpoint は無効化されます。

Todo API は `components/libkoiki/` の framework sample / starter capability として維持されています。新規 business API を `components/libkoiki/` に置く前例として扱わないでください。
