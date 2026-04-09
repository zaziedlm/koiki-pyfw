# LOG-11 E2E 起点のログセキュリティ短期対応計画

最終更新: 2026-04-09 完了

## 1. 目的

本書は、Docker `prod` profile 上で実施した SAML / OIDC の E2E 検証により顕在化した
ログセキュリティ残課題を、短期対応で解消するための計画である。

今回の `LOG-11` は、以下 3 点を対象とする。

- Uvicorn access log 経由の query string 漏えい停止
- SAML フロー関連の nonce / ticket 断片ログ除去
- normal log に混入している `request.http.client` / `request.http.user_agent` の制御

本計画は完了済みであり、今回の第 1 弾ログセキュリティ対応は E2E 観点まで含めて完了扱いとする。

## 2. 背景

unit / component test の回帰セットは `LOG-10` までで成立しているが、
Docker `prod` profile 上の実起動・ブラウザ操作では、以下の経路が追加で確認された。

- Uvicorn 標準 access log
- request context が付与された通常ログ
- SAML フロー永続化に伴う repository/service ログ

このため、unit test ベースでは見落としやすい `実運用ログ経路` を対象に、
追加の是正を行う必要がある。

## 3. E2E で確認された問題

### 3.1 SAML / OIDC 共通

#### 3.1.1 Uvicorn access log に query string が残る

現象:

- `/api/v1/auth/saml/authorization?redirect_uri=...`
- `/api/v1/auth/sso/authorization?redirect_uri=...`

上記が Uvicorn access log にそのまま残る。

影響:

- redirect URI の生値が stdout 経由で外部ログ基盤へ流れる
- middleware 側で query を落としても、別経路のため防げない

主な対象:

- [`Dockerfile.unified`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/Dockerfile.unified)
- [`docker-compose.unified.yml`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docker-compose.unified.yml)

#### 3.1.2 normal log に `request.http.client` / `request.http.user_agent` が混在する

現象:

- normal log に `request.http.client`
- normal log に `request.http.user_agent`

が生値で残る。

影響:

- 通常ログの `IP は部分マスク / UA は原則除去` というポリシーと不整合
- `request.http` が付いたあらゆる通常ログで個人情報最小化が崩れる

主な対象:

- [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py)
- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)

### 3.2 SAML 固有

#### 3.2.1 `relay_nonce` / `ticket_id` / `request_id` 断片ログが残る

現象:

- `relay_nonce: "Fv0wmTX2..."`
- `ticket_id: "L-CiLM3fRE5y..."`
- SAML request id 相当値

が通常ログに残る。

影響:

- token 本体だけでなく token 断片も出さない方針に反する
- フロー再現材料として悪用される余地を残す

主な対象:

- [`app/services/saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)
- [`app/repositories/saml_auth_flow_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/saml_auth_flow_repository.py)

## 4. 今回の対象範囲

### 4.1 対象

- `prod` profile の実行経路で出る stdout / structlog ベースの通常ログ
- SAML / OIDC の authorization, login, ACS 周辺ログ
- request context を含む通常ログ
- E2E で再発確認できる回帰テストと確認手順

### 4.2 対象外

今回の計画では、以下は対象外とする。

- `audit log` / `security log` の保存先分離
- `JWT_SECRET` の本番値是正
- `passlib/bcrypt` 依存ライブラリ由来 traceback の完全解消
- CI 組み込み
- warning 解消

## 5. 対応方針

### 5.1 Uvicorn access log は停止し、structlog 側へ寄せる

方針:

- Uvicorn 標準 access log は `--no-access-log` で停止する
- request 監査 / access 情報は [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py) の audit / access log を正とする

理由:

- query string 漏えいを一括で止められる
- ログポリシーを structlog sanitizer 配下へ統一できる
- E2E 環境とコンテナ運用での再現性が高い

### 5.2 SAML の nonce / ticket は断片でも通常ログへ出さない

方針:

- `relay_nonce[:8] + "..."` や `ticket_id[:12] + "..."` を削除する
- 代替識別子は `flow_id`、`user_id`、`status`、`used_at` を使う
- `request_id` についても、SAML request id など外部フロー識別子は通常ログへ出さない

理由:

- 断片でも secret / relay state 由来値であり、ログ出力禁止方針と整合しない
- 障害解析は DB 主キーや `http.request_id` で十分代替可能

### 5.3 `request.http` は logger 種別ごとに出し分ける

方針:

- normal log:
  - `request.http.method`
  - `request.http.path`
  - `request.http.request_id`
  のみ保持
- normal log では:
  - `request.http.client` は除去または部分マスク
  - `request.http.user_agent` は除去
- security / audit では現行どおり `client` と `user_agent` を保持可

実装寄せ:

- 第一段階は [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py) の processor 側で logger category に応じて `request.http` を整形する
- 必要なら第二段階で [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py) の bind 内容を調整する

## 6. 作業単位

### LOG-11-01 Uvicorn access log 停止

- 目的:
  - query string を含む Uvicorn 標準 access log を止める
- 主対象:
  - [`Dockerfile.unified`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/Dockerfile.unified)
  - 必要に応じて [`docker-compose.unified.yml`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docker-compose.unified.yml)
- 対応内容:
  - production / optimized / 必要なら dev の `uvicorn` 起動に `--no-access-log` を追加
  - 影響範囲を確認し、request tracing は audit/access middleware で代替できる状態を確認する
- 完了条件:
  - `docker compose logs app-prod` に `GET /path?query=...` が出ない

### LOG-11-02 SAML フロー断片ログ除去

- 目的:
  - `relay_nonce`, `ticket_id`, SAML request id の断片ログを除去する
- 主対象:
  - [`app/services/saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)
  - [`app/repositories/saml_auth_flow_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/saml_auth_flow_repository.py)
- 対応内容:
  - `relay_nonce`
  - `ticket_id`
  - 外部フロー request id
  の logger 引数を削除
  - 代替として `flow_id`, `user_id`, `status` を使う
- 完了条件:
  - SAML authorization / ACS / login の通常ログに nonce / ticket 断片が残らない

### LOG-11-03 normal log の `request.http` 整形

- 目的:
  - normal log から生の IP / user agent を落とす
- 主対象:
  - [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  - 必要に応じて [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py)
- 対応内容:
  - `sanitize_event_dict()` で `request.http` を logger category ごとに再構成する
  - normal:
    - `method`
    - `path`
    - `request_id`
  のみ残す
  - security / audit:
    - `client`
    - `user_agent`
    を維持
- 完了条件:
  - normal log に `request.http.client` と `request.http.user_agent` が出ない
  - audit / security log では必要情報が維持される

### LOG-11-04 回帰確認の追加

- 目的:
  - `LOG-11-01` から `LOG-11-03` の再発防止
- 主対象:
  - [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
  - [`tests/unit/app/services/test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)
  - 必要に応じて新規 `request context` / `container logging` 観点 test
- 対応内容:
  - normal log で `request.http.client` / `user_agent` が落ちることを固定
  - SAML service / repository で nonce / ticket 断片が logger に渡らないことを固定
  - `Dockerfile.unified` の `uvicorn` 起動オプション変更を文書確認に反映
- 完了条件:
  - unit 回帰セットで `LOG-11` 観点が確認できる
  - 再ビルド後の E2E で同じ漏えいが再発しない

## 7. 推奨実施順

1. `LOG-11-01`
2. `LOG-11-02`
3. `LOG-11-03`
4. `LOG-11-04`
5. Docker 再ビルド
6. SAML / OIDC の再 E2E

理由:

- Uvicorn access log は最も広範囲で、漏えい量も大きい
- 次に SAML 固有の secret 断片を止める
- 最後に normal log の request context を整形し、全体一貫性を完成させる

## 8. 検証観点

### 8.1 Docker / stdout 確認

再ビルド後に以下を確認する。

```powershell
.\start-docker.ps1 unified-prod-down
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
$env:ENV_FILE = ".env.production"
docker compose -f docker-compose.unified.yml --profile prod logs app-prod --tail=300
```

確認ポイント:

- `INFO: ... "GET /...?... HTTP/1.1"` が出ない
- `relay_nonce`, `ticket_id` の断片が出ない
- normal log に `request.http.client` / `request.http.user_agent` が出ない

### 8.2 SAML E2E

確認フロー:

- `http://localhost:3000/auth/login`
- SAML login
- `saml-user` 等で認証
- callback 後に `/api/v1/auth/me`
- 任意の `/api/v1/todos` 操作

確認ポイント:

- token / ticket / nonce 断片が出ない
- audit log には `actor.*` と `http.request_id` が出る
- security event は維持される

### 8.3 OIDC E2E

確認フロー:

- `http://localhost:3000/auth/login`
- OIDC SSO login
- callback 後に `/api/v1/auth/me`

確認ポイント:

- authorization endpoint の query string が access log に出ない
- normal log に `request.http.client` / `user_agent` が出ない
- security event は維持される

## 9. 完了判定

`LOG-11` は、以下を満たした時点で完了とする。

- Uvicorn access log に query string が残らない
- SAML フロー関連の nonce / ticket / 外部 request id 断片が通常ログに残らない
- normal log に `request.http.client` / `request.http.user_agent` が残らない
- audit / security log の必要情報は維持される
- Docker `prod` profile の SAML / OIDC E2E で再確認済み

## 10. フォローアップ

今回の `LOG-11` 完了後も残る可能性がある論点:

- [`JWT_SECRET`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/.env.production) の本番値是正
- `passlib/bcrypt` 由来 traceback の依存関係整理
- handler / 保存先分離
- CI 組み込み

これらは本計画では追わず、別タスクで管理する。

## 11. 2026-04-09 時点の進捗

完了済み:

- [`Dockerfile.unified`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/Dockerfile.unified)
  の production / optimized 起動に `--no-access-log` を追加
- [`app/repositories/saml_auth_flow_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/saml_auth_flow_repository.py)
  から `request_id`, `relay_nonce`, `ticket_id` 断片ログを除去
- [`app/repositories/saml_auth_flow_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/saml_auth_flow_repository.py)
  の `session_index` debug を `session_index_present` へ縮小
- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  に `relay_nonce`, `ticket_id` を機密キーとして追加
- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  で normal log の `request.http` を `method`, `path`, `request_id` のみに制限
- [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
  に `request.http` の normal / audit 差分テストを追加
- [`tests/unit/app/repositories/test_saml_auth_flow_repository_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/repositories/test_saml_auth_flow_repository_logging.py)
  を追加し、SAML flow repository の断片非出力を固定

確認済みコマンド:

```powershell
poetry run pytest tests/unit/core/test_logging_sanitizer.py tests/unit/app/services/test_saml_service.py tests/unit/app/repositories/test_saml_auth_flow_repository_logging.py
poetry run pytest tests/unit/core/test_security_logger.py tests/unit/core/test_audit_middleware.py
```

結果:

- `69 passed`
- 既知 warning のみ発生

追加で完了済み:

- Docker `prod` profile を再ビルドし、[`start-docker.ps1`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/start-docker.ps1)
  の `unified-prod-build` / `unified-prod` で再起動確認
- OIDC, SAML, フレームワーク管理ログインの 3 経路でブラウザ E2E を再実施
- `docker compose logs app-prod --tail=300` で以下を確認
  - Uvicorn access log に query string が残らない
  - SAML の `relay_nonce`, `ticket_id`, 外部 request id 断片が通常ログに残らない
  - normal log に `request.http.client` / `request.http.user_agent` が残らない
  - audit / security log では必要な情報が維持される

E2E 確認結果:

- OIDC:
  - `/api/v1/auth/sso/authorization` の query string 漏えいなし
  - normal log の `request.http` は `method`, `path`, `request_id` のみ
- SAML:
  - `flow_id` ベースで追跡可能
  - `relay_nonce` / `ticket_id` 断片ログは再発なし
- フレームワーク管理ログイン:
  - normal log に IP / user agent は残らない
  - security event / audit log は維持

完了状態:

- `LOG-11` 完了

なお、以下は `LOG-11` の完了条件外であり、別課題として残る。

- [`JWT_SECRET`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/.env.production) の短さに起因する `InsecureKeyLengthWarning`
- `passlib/bcrypt` 由来 traceback
- `SAWarning`
