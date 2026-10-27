# ランタイムTLSの確認

`verify_runtime_tls.py` は、更新したアプリ環境で次を実測する診断プログラムです。

- 正規のローカル証明書の受理、未信頼CA・異なるホスト名の拒否
- OS CAとcertifiから問題の `emSign ECC Root CA - G3` が除去されていること
- PyPIへの検証有効なHTTPS接続
- JWT期限切れ拒否、PyJWTの呼び出し元optionsが書き換わらないこと

```sh
uv run --locked python ops/security/verify_runtime_tls.py
```

Debian系の `/etc/ssl/certs/ca-certificates.crt` を参照します。管理ネットワークでは、正規提供された結合CAバンドルを `SSL_CERT_FILE` に指定します。外部IdPの資格情報は不要です。ローカルに一時CAと鍵を生成し、終了時に削除します。`system` の確認はイメージ内のOSバンドルを明示参照し、外部通信の一時CAと区別します。

これは管理された実IdPのSSO/JWKS/SAML検証や、侵害された中間CA鍵の実物を使う検証を代替しません。Python標準sslの侵害鍵拒否は公式3.13.18配布物の版・digest・保守元の収録根拠と併せて判断します。

更新前後の監査、コンテナビルド、既存テストの記録と再現方法は `docs/security/implementation/2026-10-27/README.ja.md` を参照してください。
