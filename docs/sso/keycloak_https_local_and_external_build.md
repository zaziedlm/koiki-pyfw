# Keycloak HTTPS ローカル構成と AWS 向け build の整理

## 目的

このドキュメントは、以下を切り分けて整理するための手順書です。

- ローカル `Keycloak` コンテナを `HTTPS` で動かし、`OIDC` / `SAML` ログインを通す
- 社内ネットワーク配下でも `Python` / `Node.js` の依存取得を含む Docker build を通す
- `.\start-docker.ps1 unified-prod-external-build` で作る AWS 向けイメージには、ローカル Keycloak 用の `mkcert` CA を含めない

## 前提と profile の役割

- `.\start-docker.ps1 unified-prod-build`
  - ローカル `Postgres` + ローカル `Keycloak` を使う
  - ローカル `Keycloak` の HTTPS 証明書を app / frontend が信頼する必要がある

- `.\start-docker.ps1 unified-prod-external-build`
  - AWS 向けイメージの build を想定
  - `Keycloak` コンテナは使わない
  - 外部 IdP は `HENNGE` を想定
  - ローカル `Keycloak` 用の `mkcert` CA は不要

## 証明書 / CA の役割

### 1. `nscacert.pem`

- 配置:
  - `docker/certs/nscacert.pem`
  - `frontend/docker/certs/nscacert.pem`
- 用途:
  - 社内ネットワーク環境で Docker build 中の `pip` / `npm` / `curl` が外部へ HTTPS 接続するための CA
- 注意:
  - これはローカル Keycloak 用ではありません
  - 現在の Dockerfile では build 環境事情を優先して参照対象に残しています

### 2. `mkcert` ルート CA

- 取得元:
  - `mkcert -CAROOT` で確認できるローカル PC 上の `rootCA.pem`
- リポジトリ内の配置:
  - `docker/certs/mkcert-rootCA.pem`
  - `frontend/docker/certs/mkcert-rootCA.pem`
- 用途:
  - `mkcert` で発行した `server.crt` を app / frontend コンテナが信頼できるようにする
- 注意:
  - ローカル Keycloak HTTPS 専用
  - AWS 向け `unified-prod-external-build` ではイメージに取り込まない

### 3. Keycloak サーバー証明書

- 配置:
  - `docker/keycloak/certs/server.crt`
  - `docker/keycloak/certs/server.key`
- 用途:
  - ローカル Keycloak コンテナ自身の HTTPS 終端

## PC 側の CA 設定

ローカルブラウザで `https://localhost:8443` を警告なしで開くには、`mkcert` のローカル CA が PC 側の trust store に入っている必要があります。

### 確認 / 初期化

```powershell
mkcert -CAROOT
mkcert -install
```

- `mkcert -install`
  - Windows のローカル trust store に `mkcert` のローカル CA を登録します
- これにより、ブラウザが `mkcert` 署名証明書を信頼できるようになります

## ローカル Keycloak HTTPS 証明書の作成

### 1. SAN を含む証明書を再発行

以下のホスト名で使えるようにします。

- `localhost`
- `127.0.0.1`
- `keycloak`
- `host.docker.internal`

```powershell
mkcert `
  -cert-file docker/keycloak/certs/server.crt `
  -key-file docker/keycloak/certs/server.key `
  localhost 127.0.0.1 keycloak host.docker.internal
```

### 2. `mkcert` のルート CA をリポジトリへコピー

```powershell
Copy-Item "$env:LOCALAPPDATA\mkcert\rootCA.pem" "docker/certs/mkcert-rootCA.pem" -Force
Copy-Item "$env:LOCALAPPDATA\mkcert\rootCA.pem" "frontend/docker/certs/mkcert-rootCA.pem" -Force
```

意味:

- app build 用に `docker/certs/mkcert-rootCA.pem`
- frontend build 用に `frontend/docker/certs/mkcert-rootCA.pem`

を置き、ローカル profile の build 時だけ trust store に入れます。

## Keycloak コンテナへの証明書配置

`docker-compose.unified.yml` で以下を Keycloak に mount しています。

```yaml
- ./docker/keycloak/certs/server.crt:/opt/keycloak/conf/server.crt:ro
- ./docker/keycloak/certs/server.key:/opt/keycloak/conf/server.key:ro
```

また、Keycloak 側では以下を設定しています。

```yaml
KC_HTTP_ENABLED: "false"
KC_HOSTNAME: https://localhost:8443
KC_HTTPS_CERTIFICATE_FILE: /opt/keycloak/conf/server.crt
KC_HTTPS_CERTIFICATE_KEY_FILE: /opt/keycloak/conf/server.key
```

意味:

- `8443` の HTTPS のみを有効化する
- 非標準 HTTPS ポートのため、`KC_HOSTNAME` に `https://localhost:8443` を明示する

## `.env.production` のローカル Keycloak HTTPS 設定

主な変更点:

```env
SSO_ISSUER_URL=https://localhost:8443/realms/koiki
SSO_AUTHORIZATION_ENDPOINT=https://localhost:8443/realms/koiki/protocol/openid-connect/auth
SSO_TOKEN_ENDPOINT=https://keycloak:8443/realms/koiki/protocol/openid-connect/token
SSO_JWKS_URI=https://keycloak:8443/realms/koiki/protocol/openid-connect/certs
SSO_SKIP_SSL_VERIFY=false

SAML_IDP_ENTITY_ID=https://localhost:8443/realms/koiki-saml
SAML_IDP_SSO_URL=https://localhost:8443/realms/koiki-saml/protocol/saml
SAML_IDP_SLS_URL=https://localhost:8443/realms/koiki-saml/protocol/saml
SAML_IDP_METADATA_URL=https://keycloak:8443/realms/koiki-saml/protocol/saml/descriptor
SAML_SKIP_SSL_VERIFY=false
```

意味:

- ブラウザが触る URL は `https://localhost:8443`
- app コンテナが内部通信用に触る URL は `https://keycloak:8443`

## Dockerfile での CA 取り込み方針

### 現在の方針

- `nscacert.pem`
  - 常に build context に含める
  - 社内ネットワーク build に必要
- `mkcert-rootCA.pem`
  - ローカル Keycloak を使う profile のときだけ取り込む

### build arg

- `INCLUDE_LOCAL_IDP_CA=true`
  - `dev` / `optimized` / `prod`
- `INCLUDE_LOCAL_IDP_CA=false`
  - `prod-external`

### 関連ファイル

- `Dockerfile.unified`
- `frontend/Dockerfile.unified`
- `docker-compose.unified.yml`

## `unified-prod-build` と `unified-prod-external-build` の違い

### `unified-prod-build`

- `Keycloak` コンテナを使う
- `INCLUDE_LOCAL_IDP_CA=true`
- `mkcert-rootCA.pem` を app / frontend の trust store に入れる
- ローカル Keycloak HTTPS の `OIDC` / `SAML` を検証できる

### `unified-prod-external-build`

- `Keycloak` コンテナを使わない
- `INCLUDE_LOCAL_IDP_CA=false`
- `mkcert-rootCA.pem` はイメージに入らない
- `docker/keycloak/certs/server.crt` / `server.key` も runtime では使われない
- AWS 向けの外部 IdP 連携イメージとして扱う

注意:

- 現在の実装では `nscacert.pem` は残ります
- これは「社内ネットワークで build が成立すること」を優先したためです
- もし将来的に「AWS 向け final image から社内 CA も外したい」なら、build stage と runtime stage の分離を追加で行います

## 既存 Keycloak realm がある場合の注意

`Keycloak` は `--import-realm` で起動していますが、既存 realm がある場合は `IGNORE_EXISTING` で import が skip されます。

そのため、`realm-saml.json` を修正しても既存 realm には自動反映されません。

### 起きた問題

- `koiki-saml` realm の `frontendUrl` が `http://localhost:8090` のまま残っていた
- 結果として SAML ログイン時に Keycloak が `invalid_destination` を返し、ブラウザで `400 Bad Request` になった

### 対応

1. import 元ファイルを修正

```json
"attributes": {
  "frontendUrl": "https://localhost:8443"
}
```

対象:

- `docker/keycloak/realm-saml.json`

2. 既存 realm の実体も更新

app コンテナから Keycloak 管理 API を叩いて反映できます。

```powershell
docker exec koiki_app_prod_unified python -c "
import httpx
base='https://keycloak:8443'
token=httpx.post(
    base + '/realms/master/protocol/openid-connect/token',
    data={
        'grant_type':'password',
        'client_id':'admin-cli',
        'username':'admin',
        'password':'admin',
    },
    timeout=30.0,
).json()['access_token']
headers={'Authorization': f'Bearer {token}'}
client=httpx.Client(base_url=base, headers=headers, timeout=30.0)
realm=client.get('/admin/realms/koiki-saml').json()
realm.setdefault('attributes', {})['frontendUrl']='https://localhost:8443'
resp=client.put('/admin/realms/koiki-saml', json=realm)
print(resp.status_code)
"
```

別案:

- 既存 `keycloak_data` volume を消して初期化し、realm を再 import する

## ローカル検証コマンド

### 1. build / 起動

```powershell
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
```

### 2. container 状態

```powershell
docker ps --filter "name=osskk_keycloak_unified" --filter "name=koiki_app_prod_unified"
```

### 3. health 確認

```powershell
curl.exe -s http://localhost:8000/api/v1/auth/sso/health
curl.exe -s http://localhost:8000/api/v1/auth/saml/health
```

期待:

- `jwks_accessible: true`
- `status: healthy`

### 4. Keycloak metadata 確認

```powershell
docker exec koiki_app_prod_unified sh -lc "curl -sk https://keycloak:8443/realms/koiki-saml/protocol/saml/descriptor | head -c 800"
```

期待:

- `entityID="https://localhost:8443/realms/koiki-saml"` を含む

### 5. ブラウザ確認

- `OIDC` ログイン成功
- `SAML` ログイン成功

## AWS 向け build の確認

### build

```powershell
.\start-docker.ps1 unified-prod-external-build
```

### 意味

- `Keycloak` コンテナなし
- `mkcert` ルート CA なし
- 外部 `IdP` 連携向け

## 影響を受ける主なファイル

- `docker/keycloak/certs/server.crt`
- `docker/keycloak/certs/server.key`
- `docker/certs/mkcert-rootCA.pem`
- `frontend/docker/certs/mkcert-rootCA.pem`
- `docker/certs/nscacert.pem`
- `frontend/docker/certs/nscacert.pem`
- `.env.production`
- `docker-compose.unified.yml`
- `Dockerfile.unified`
- `frontend/Dockerfile.unified`
- `docker/keycloak/realm-saml.json`

## 補足

- ローカル Keycloak HTTPS 用の `server.crt` / `server.key` は開発用途です
- AWS 本番では `HENNGE` を外部 IdP として利用する前提のため、`unified-prod-external-build` 側にローカル Keycloak 用 CA を持ち込まない設計にしています
- `nscacert.pem` は「社内ネットワーク build の成立」のために残しています
