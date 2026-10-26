# 検査の制約・失敗と回復

- Trivyの既定DBミラーmirror.gcr.ioへの接続はForbiddenだった。公式GHCRの `ghcr.io/aquasecurity/trivy-db:2` から取得して回復した。
- Docker Hubの探索用index.docker.ioへの接続はForbiddenだった。許可された公式registry-1.docker.ioを明示し、対象3イメージを検査した。
- 共有キャッシュの競合は `--cache-backend memory` により回復した。
- Keycloak `quay.io/keycloak/keycloak:26.3.5` は初回・再試行ともレイヤー展開中にunexpected EOFとなり、レポートを生成できなかった。取得エラーであり脆弱性0件とは扱わない。正常に取得できる環境で再検査する。
- Nginxは終了コード0で結果を生成したが、CVE-2026-107891の詳細がDBにない旨の警告が2件あった。全件詳細が揃った保証はない。
- アプリ完成イメージとDev Containerはローカルに存在せず、再ビルドも実施していない。追加APT部品、独自CA、アプリwheel内のネイティブ部品は完成イメージで再確認する。
- イメージ検査はLinux amd64のみ。arm64等の配備物は未検査。
- Python本体、pip／uv等の内蔵コピー、証明書内容、GitHub Actions、サプライチェーン上の悪意あるコードの不存在はこれらの検査だけでは保証できない。
