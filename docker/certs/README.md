# コンテナのCA

通常の公開ネットワークでは追加ファイルは不要です。OSの更新済みCAバンドルでTLSを検証します。

組織で管理するCAが必要な場合は、正規の管理者から提供された `nscacert.pem` をこのディレクトリに置きます。Dockerfileはファイルがある場合だけ、BuildKitの読み取り専用マウントから信頼ストアへ導入します。PEMはGit管理対象外です。組織CAの信頼追加はその環境の管理判断で行います。

セッション固有の通信プロキシCAはこのディレクトリへ置かず、結合CAバンドルを一時的に渡します。例：

```sh
docker build --secret id=proxy_ca,src=/path/to/approved-combined-ca-bundle.pem .
```

`proxy_ca` はuv/npmが通信するRUNの間だけマウントされ、イメージのレイヤーへ保存されません。TLS検証は有効のままです。実行時に独自CAが必要なら、承認された結合バンドルを読み取り専用マウントし、Pythonの `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`、Nodeの `NODE_EXTRA_CA_CERTS` を該当パスへ設定します。ビルド時の一時CAだけでは実行時CAを変更しません。

フロントエンドの本番Nginxは静的資源だけを配信し、Nodeビルド段階のCAや依存をコピーしません。実施結果は `docs/security/implementation/2026-10-27/README.ja.md` を参照してください。
