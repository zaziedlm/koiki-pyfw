# Task 1-5: libkoiki dependency 境界の整理

## 目的

`libkoiki` に残すべき framework dependency と、参照アプリ側へ寄せるべき依存を切り分ける。

## 参照ファイル

- `libkoiki/pyproject.toml`
- `app/pyproject.toml`
- `docs/agent/boundaries.md`

## 事前条件

- [Task 1-1](./task-1-1.md) が完了している

## 確認観点

- `libkoiki` が再利用フレームワークとして必要とする依存
- app 固有の認証・SSO・SAML 依存
- migration や DB 運用依存の帰属

## 実施手順

1. `libkoiki` の依存を 1 つずつ責務で評価する
2. `app` 寄り依存を抽出する
3. `alembic` の帰属を判断する
4. `python3-saml`、`xmlsec` などの app 寄り依存の扱いを決める
5. `libkoiki` に残す依存の理由を記録する

## 成果物

- `libkoiki` dependency 分類メモ
- 残す依存と移す依存の一覧

## 検証

- 各依存について「別アプリでも必要か」を説明できる
- app 固有依存が framework package に混ざったままになっていない

## 完了条件

- `libkoiki` の再利用責務に沿った依存境界が定義されている

## 実施結果

Task:

- Task 1-5: `libkoiki` dependency 境界の整理

変更内容:

- `libkoiki/pyproject.toml`、root `pyproject.toml`、`docs/agent/boundaries.md`、実装上の import 実態を照合し、依存を次の4群に分類した
  - `libkoiki` の core runtime として残す依存
  - `libkoiki` の optional extra へ寄せるのが妥当な依存
  - 参照アプリ `app` / 将来の `koiki_ref_app` 側へ寄せる依存
  - workspace / 運用側へ寄せる依存
- `libkoiki` に残すべき core runtime dependency を次のように整理した
  - `fastapi`
  - `uvicorn`
  - `sqlalchemy[asyncio]`
  - `asyncpg`
  - `pydantic`
  - `pydantic-settings`
  - `PyJWT[crypto]`
  - `passlib[bcrypt]`
  - `httpx`
  - `structlog`
  - `redis`
  - `slowapi`
  - `tzdata`
- 上記を残す理由も整理した
  - `fastapi` / `uvicorn`: `libkoiki.api.*` と endpoint 群、ASGI 実行に直接必要
  - `sqlalchemy[asyncio]` / `asyncpg`: `libkoiki.db.session` と config が `postgresql+asyncpg` を前提としている
  - `pydantic` / `pydantic-settings`: schema と settings の基盤
  - `PyJWT[crypto]` / `passlib[bcrypt]`: `libkoiki.core.security` と auth service が直接利用
  - `httpx`: 共通 HTTP client として framework 側で使用
  - `structlog`: logging / monitoring 実装の共通基盤
  - `redis`: dependency, event publisher/handler, rate limit 周辺で framework 側が直接利用
  - `slowapi`: `libkoiki.core.rate_limiter`、dependencies、endpoint decorator で直接利用
  - `tzdata`: Windows / container 環境の timezone 補完として framework 共通で有効
- `libkoiki` に残すが、将来的には optional extra 化を検討すべき依存を整理した
  - `prometheus-fastapi-instrumentator`
  - `prometheus-client`
  - `python-multipart`
  - `email-validator`
- この4つについての判断理由も整理した
  - `prometheus-fastapi-instrumentator` / `prometheus-client`
    - `libkoiki.core.monitoring` が直接利用しており reusable capability ではある
    - ただし全採用先で必須ではないため、core runtime より monitoring extra の方が妥当
  - `python-multipart`
    - `libkoiki.api.v1.endpoints.auth_basic` の `OAuth2PasswordRequestForm` で必要
    - auth endpoint を framework 標準同梱するなら必要だが、auth extra 化も検討余地がある
  - `email-validator`
    - `libkoiki.schemas.user` の `EmailStr` に必要で reusable
    - ただし schema extra として切り出す余地はある
- `libkoiki` から外し、参照アプリ `app` / 将来の `koiki_ref_app` 側へ寄せる依存を次のように整理した
  - `python3-saml`
  - `xmlsec`
- 上記を app 側へ寄せる理由も整理した
  - 実際の利用箇所が `app/services/saml_service.py`、`app/core/saml_config.py`、`app/api/v1/endpoints/saml_auth.py` に閉じている
  - `docs/agent/boundaries.md` の「SSO / SAML は app 側」という境界ルールに一致する
  - 別アプリで SAML を使わない場合、framework package に強制すべきではない
- `alembic` の帰属を見直し、`libkoiki` の core runtime からは外す方針が妥当と整理した
  - migration は current app / reference app の schema composition に依存する
  - すべての採用先が `alembic` を使うとは限らず、framework package の常時 runtime 依存としては重い
  - 将来的には workspace もしくは `koiki_ref_app` 側の運用依存へ寄せるのがよい
- DB 運用寄り依存の扱いも整理した
  - `psycopg2-binary`: sync migration / admin tooling 寄りなので workspace / 参照アプリ運用依存
  - `aiosqlite`: dev/test 用であり framework core runtime ではない
- root `pyproject.toml` から見えていた依存重複と不足も記録した
  - root に残っていた `python3-saml`、`xmlsec`、`psycopg2-binary`、`aiosqlite` は `libkoiki` の core runtime ではない
  - 一方で `libkoiki.core.monitoring` と `libkoiki.schemas.user` の実装からは `prometheus-*` と `email-validator` の責務が見えるため、将来は `libkoiki` 側 package 定義へ明示する必要がある

未解決事項:

- monitoring を `libkoiki` core runtime に残すか、optional extra (`monitoring`) にするかは Stage 2 以降で package 定義として確定する必要がある
- `python-multipart` と `email-validator` を core runtime と見るか optional extra と見るかは、`libkoiki` 標準機能の最終範囲次第で微調整が必要
- `asyncpg` を driver abstraction なしで固定し続けるかは将来の multi-backend 方針に依存する
- `alembic` を workspace へ置くのか、`koiki_ref_app` 側へ置くのかは Task 1-6 と Stage 2 で最終決定が必要

検証結果:

- 各依存について「別アプリでも framework として必要か」を説明できる状態になった
- SAML 関連依存は app / `koiki_ref_app` 側へ寄せるべきという境界が明確になった
- migration / DB 運用依存は framework core runtime ではなく、参照アプリまたは workspace 運用責務として扱う方針が定まった
- `libkoiki` の package 定義で不足している optional dependency 候補も把握できた

次タスクへ渡す事項:

- Task 1-6 では Stage 1 の総括として、root / `libkoiki` / `app` の責務分離が Task 2 以降へ渡せるかを検証する
- Stage 2 の package / `uv` 設計では、`alembic`、`psycopg2-binary`、`aiosqlite` を workspace または `koiki_ref_app` 側へ寄せる前提で進める
- `libkoiki` の今後の package 設計では、monitoring、auth/form、schema validation の optional extra 設計を検討対象に含める

## 次タスク

- [Task 1-6](./task-1-6.md)
