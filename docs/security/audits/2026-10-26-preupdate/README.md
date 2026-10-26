# 更新前OSS脆弱性監査（2026-10-26）

## 対象と結論

作業ブランチ `security/backend-python-emsign-brotli`、検査元コミット `9d8a173c4c5b56cfb1eb55c6cf56e0eff40d7d2e`。Python本体更新を待つ間に現状を監査した。依存・ロック・ソース・Docker設定・稼働コンテナを変更せず、自動修正、依存同期、イメージ再ビルドを行っていない。監査は既存更新ブランチの基準記録として同ブランチに保持する。

これは監査ツールの検出結果であり、各利用経路で攻撃が成立することを確認した結果ではない。バージョン更新の採用判断は別工程で行う。

## 検査範囲と結果

| 検査 | 結果 | 注意 |
| --- | --- | --- |
| pip-audit／既存仮想環境 | 10パッケージ、受信指摘51件 | workspace2パッケージはPyPI未掲載としてスキップ |
| pip-audit／uv.lock全体 | registry由来82パッケージ、同じ10パッケージ・51件 | 環境で未導入のcoloramaも対象。再解決なし |
| Python指摘の整理 | パッケージ別37件 | 同じID・aliasが重なる指摘を統合。全体で異なるCVE37個という意味ではない |
| Bandit | 指摘0件、解析エラー0件 | app、apps、libkoiki/src、koiki_ref_app/srcを対象。ルール既定値で実行 |
| npm／ルート | 1パッケージ High | 間接依存zod。開発ツール用 |
| npm／frontend | 18パッケージ | Critical 1、High 12、Moderate 5。依存親への波及を含むパッケージ数 |
| Trivy | 4イメージ完了、Keycloak未完了 | ベース素材と既存PostgreSQL。アプリ完成イメージの監査とは異なる |

pip-auditとnpmの終了コード1は今回のJSONでは指摘検出を示す。Keycloakの終了コード1は取得エラーであり区別する。Trivyは今回の設定で検出しても終了コード0となる。

## Python指摘一覧

raw / uniqueは受信指摘数／同一パッケージ内でID・aliasを統合した件数。runtime分類はrootの実行時依存から、PyJWT[crypto]などの有効extraを含めた依存到達で判定した。dev/security分類は現在の宣言上の分類であり、本番イメージに存在しない保証ではない。通常Dockerfileは開発・監査依存を含めてコピーするため、完成イメージでも確認する。

| パッケージ | 現行版 | 依存範囲 | raw / unique | ツールが提示した修正版（未採用） |
| --- | --- | --- | --- | --- |
| anyio | 4.13.0 | runtime | 2 / 2 | 4.14.2 |
| certifi | 2026.4.22 | runtime | 1 / 1 | 2026.10.19 |
| cryptography | 47.0.0 | runtime | 7 / 4 | 48.0.1, 49.0.0, 50.0.0 |
| filelock | 3.29.0 | dev/security | 3 / 3 | 4.2.1 |
| msgpack | 1.1.2 | dev/security | 2 / 1 | 1.2.1 |
| pip | 26.1.1 | dev/security | 4 / 2 | 26.1.2, 26.2, 26.2.0 |
| pyjwt | 2.12.1 | runtime | 19 / 16 | 2.13.0, 2.14.0, 2.15.0 |
| python-multipart | 0.0.29 | runtime | 6 / 3 | 0.0.30, 0.0.31 |
| starlette | 1.1.0 | runtime | 4 / 2 | 1.3.0, 1.3.1 |
| urllib3 | 2.7.0 | dev/security | 3 / 3 | 2.8.0 |

[全ID・alias・概要・修正版](python-findings.json) を参照する。修正版一覧は異なる脆弱性の候補の集合であり、どれか一つを入れれば全指摘が消えるという意味ではない。PyJWTのPYSEC-2026-4146には修正版が提示されておらず、公式勧告・利用条件の追加確認が必要。

PyJWT <2.13、Starlette <1.2などの現在の制約では、一部の修正候補へ更新できない。Pythonのパッチ版更新だけでは、これらのロック済み依存の指摘は自動解消されない。

## npm指摘一覧

frontendの直接依存ではreact-router、vite、vitest、zodに指摘。間接依存は@humanfs/node、@vitest/mocker、ajv、baseline-browser-mapping、brace-expansion、browserslist、flatted、js-yaml、minimatch、nanoid、postcss、source-map-js、tar、undici。Criticalのtarは間接依存であり、到達経路と開発・ビルド用途を確認する。フロントエンド本番はNginx静的配信なので、Nodeプロセスへの影響とブラウザに配布されるコードへの影響を分ける。

rootとfrontendは別ロックで監査し、zod等の重複を全体のユニーク脆弱性数として合算していない。各npm JSONにvia、影響範囲、nodes、fixAvailableを保存した。fixAvailable=trueでも自動修正は実行していない。

## コンテナ結果

severity件数の列は Critical / High / Medium / Low / Unknown の順。総数はパッケージ・配置ごとの指摘件数で、同じCVEを複数パッケージに数える。修正版なし・未到達の可能性も含み、全件を無条件に修正対象とは扱わない。

| 対象 | 指摘件数 | 異なる脆弱性ID数 | severity件数 |
| --- | --- | --- | --- |
| python-base | 328 | 174 | 7 / 74 / 128 / 112 / 7 |
| node-base | 251 | 121 | 1 / 67 / 97 / 84 / 2 |
| nginx | 167 | 96 | 0 / 42 / 50 / 71 / 4 |
| postgres | 418 | 194 | 2 / 90 / 170 / 147 / 9 |

対象:

- python-base: `python:3.13.13-slim-bookworm` の公開ベース。
- node-base: `node:22-slim` の監査時点の公開タグ。過去にビルド・配備したイメージの同定には使わない。
- nginx: `nginxinc/nginx-unprivileged:1.30.3-alpine` の公開イメージ。
- postgres: ローカルに存在する `postgres:15`、image ID `afdbd967cf65`。実行中コンテナは変更していない。
- keycloak: `quay.io/keycloak/keycloak:26.3.5` はレイヤー取得エラーで未検査。

検査したdigestとOS・パッケージ情報は各JSONに保存した。これらは完成アプリイメージの代替検査ではない。NginxのDB警告、ネットワーク制約、未検査対象は [limitations.md](limitations.md) に記録する。

## 保存した証拠

- [manifest.json](manifest.json): 検査元コミット、ツール版、Trivy DB日時、対象ファイルSHA-256、終了コード、レポートのSHA-256。
- [installed-packages.json](installed-packages.json): 仮想環境の導入名・版。ホストの環境変数や資格情報は収集しない。
- [locked-requirements.txt](locked-requirements.txt): uv.lockから再解決せず抽出した82パッケージ。
- `python-environment.json.gz`、`python-lock.json.gz`、`bandit.json.gz`、`npm-root.json.gz`、`npm-frontend.json.gz`: 生のJSONをgzip圧縮して保持。
- `image-python-base.json.gz`、`image-node-base.json.gz`、`image-nginx.json.gz`、`image-postgres.json.gz`: Trivyの生JSONを保持。

展開例: `gzip -dc python-lock.json.gz > /tmp/python-lock.json`。元データと圧縮後のハッシュはmanifestで検証する。アーカイブに実行バイナリ、DBキャッシュ、コンテナレイヤー、トークン、アプリ設定の秘密値を含めない。

## 後続の仕分けタスク

| ID | 調査優先度 | 対象 | 次の確認 |
| --- | --- | --- | --- |
| U01 | 高 | PyJWT／cryptography | 許容アルゴリズム、JWK取得、暗号・証明書APIの実利用を勧告条件と照合。未提示修正版も確認 |
| U02 | 高 | Starlette／python-multipart | 認証フォーム等の入口への到達、制約変更とFastAPI互換性、上限設定・拒否動作を確認 |
| U03 | 高 | certifi／Python／pip／uv／OS CA | 既存の採用版・証明書対策タスクと統合。内蔵コピーを別途確認 |
| U04 | 中 | anyio／urllib3／filelock／msgpack | runtime／監査依存の入力元、制約、修正版を確認 |
| U05 | 高から判定 | frontendの18パッケージ | runtime／dev経路別にCritical・Highの条件を照合し、Node更新とnpm依存更新を分ける |
| U06 | 中 | rootのzod | OpenSpec経由の利用条件と親依存の更新手段を確認 |
| U07 | 高から判定 | イメージ指摘・Keycloak・完成イメージ | Critical／Highを勧告・修正版・到達経路で精査。Keycloakと完成イメージの未検査を解消 |
| U08 | 中 | 継続監査 | 文書内CI例と実CIの差、依存更新通知範囲、検査の定期化を別変更で検討 |

優先度は調査順の提案であり、CVSS評価や攻撃成立の判定ではない。U01～U08は未着手。今回は発見・保存までで、既存Python更新計画へ全指摘の一括修正を混ぜない。

## 再取得手順

[既存監査ガイド](../../SECURITY_AUDIT_COMMANDS.md) を基礎とする。次はプロジェクトルートから実行する例。保存先workを先に作成し、同じPython・導入版・ロックであることを確認する。更新前の状態を維持するため、この基準取得ではuv sync／npm install／自動fixを実行しない。

```sh
mkdir -p work/oss-audit
.venv/bin/python -m pip_audit --local -s pypi --progress-spinner off -f json -o work/oss-audit/python-environment.json
.venv/bin/python -m bandit -r app apps components/libkoiki/src components/koiki_ref_app/src -f json -o work/oss-audit/bandit.json
npm audit --package-lock-only --ignore-scripts --json > work/oss-audit/npm-root.json
npm audit --prefix frontend --package-lock-only --ignore-scripts --json > work/oss-audit/npm-frontend.json
```

ロック全体の検査は同時点のuv.lockからregistryパッケージをname==versionへ抽出し、保存したlocked-requirements.txtと一致を確認してから実行する。

```sh
.venv/bin/python -m pip_audit -r docs/security/audits/2026-10-26-preupdate/locked-requirements.txt --disable-pip --no-deps -s pypi --progress-spinner off -f json -o work/oss-audit/python-lock.json
```

保存した一覧での再監査はこの基準の版を対象とする。更新後の監査では必ず更新後ロックから再抽出する。監査DBは時間とともに変わるため、同じ依存でも将来の件数一致は保証しない。

Trivyは公式v0.76.1のLinux-64bit archiveを公式checksums.txtとSHA-256照合して作業ディレクトリだけに展開した。DBは公式GHCRから取得した。既存イメージは `--image-src docker`、公開イメージは `--image-src remote --platform linux/amd64` とし、`--scanners vuln --cache-backend memory --skip-db-update --format json` で検査した。再実行ではDB更新日時を記録し、対象をdigestで指定する。初回は公式GHCRを `--db-repository ghcr.io/aquasecurity/trivy-db:2 --download-db-only` に指定してDBを準備する。`--skip-db-update` は保存済みDBを同一実行群で使うためで、恒久的なDB更新停止ではない。

## 判定の限界

pip-auditでworkspaceのlibkoiki／koiki-ref-app自身は未掲載としてスキップされ、ソースはBanditと機能テストで別に扱う。Bandit指摘0はコード全体の安全性証明ではない。監査DBの登録遅延・誤検出・重複・修正版なしを含めて勧告を確認する。本番配備物・独自CA・外部IdPの実通信は未確認。Python3.13.18のDocker Hub公開待ちは継続する。
