# 採用版と公式情報の再照合結果

初回確認日: 2026-10-26（日本時間）。最新確認追記: 2026-10-27。対象ブランチ: `security/backend-python-emsign-brotli`。
今回実施したのは公開メタデータ、公式勧告、配布一覧、ロック内wheelタグの読み取りのみ。Python・ツール・依存・OSパッケージのインストール、ロック更新、イメージpull／ビルドは実施していない。

## 0. 最新状況（2026-10-27追記）

Python 3.13.18の公式Dockerタグ `python:3.13.18-slim-bookworm` は公開済み（HTTP 200）。Linux amd64／arm64を確認した。index digestは `sha256:770c65dea7da9d5eeddb968968bd514ee9fdd9bb8988e03b4463eb11ad72d3ca`。amd64のconfigもPYTHON_VERSION=3.13.18を宣言する。

Actionsのmanifestにも3.13.18のLinux x64／arm64が掲載されている。T1.1／T1.4の配布確認は完了し、T2のツール／CA準備後にT3へ進める。Windows／macOSやuv管理Pythonの配布確認は今回のLinux更新の完了条件に含めない。

[最新の配布証拠・監査差分・準備状況](../../../docs/security/reviews/2026-10-27/README.md) を参照。以下の第1～6節は10月26日時点の判断・配布待ち記録として保存する。旧表の「未提供」は最新状態ではない。依存・イメージの更新適用はまだ行っていない。

## 1. 採用判断

| 対象 | 採用版／条件 | 収録・提供の確認 | 適用先・状態 |
| --- | --- | --- | --- |
| CPython | **3.13.18** | 10月25日公開。公式リリースノートがCVE-2026-115557のssl拒否処理を明記。ソース配布のみ | Docker／CI／Dev Containerの目標版確定。既存配布経路では提供待ち |
| certifi | **2026.10.23** | PyPI公開・非yank、Python >=3.7、汎用wheelあり。対策最低基準2026.10.19以降 | root／libkoikiの採用版確定。依存制約の下限も2026.10.23を採用する方針 |
| pip | **26.2.2** | 公式注意喚起の対策版。PyPI公開・非yank、Python >=3.10、汎用wheelあり | ロック内の監査依存、各仮想環境、本体／ensurepip内蔵を別確認 |
| uv | **0.13.5** | 対策版0.13.4を含む後続安定版。PyPI wheel・公式GHCRタグを確認 | Docker／CI／Dev Container／更新作業ツール。実体更新はT2以降 |
| OS | **Debian bookworm継続** | OS系列を変更せずバックポートを利用 | バックエンドとDev Container。ホストのtrixieと混同しない |
| ca-certificates | **20250419~deb12u2**（または同じbookworm系列の後続修正版） | Debianの勧告が問題のemSign ECC Root CA - G3の除外を明記 | イメージ内OS CA。独自追加CAの内容確認は残る |
| libbrotli1／同一sourceの関連部品 | **1.0.9-2+deb12u1**（または同じbookworm系列の後続修正版） | Debian Security TrackerがCVE-2026-111497修正済みと登録 | curl等のOS依存。実際の搭載・導入版確認はT5 |
| Python向けBrotli | **追加しない** | 現行依存と既存仮想環境では不在 | Pythonの非搭載とOS部品の修正状況を別管理 |

certifiは対策最低版2026.10.19に留めず、確認時点の公開安定版2026.10.23を採用する。Python要件は現在のパッケージ利用範囲と両立する。pipは本件の修正を含む26.2.2へ限定し、無関係なアプリOSSの一括更新はしない。HTTPX／FastAPI等の更新は今回の採用対象に追加しない。

OSの「後続修正版」はDebianの版比較と当該系列の勧告で判定する。版の文字列比較や上流1.2.1との単純比較を使わない。実装時はAPT candidateと実導入版を記録し、対象版が配布元に存在しない場合は未適用とする。

## 2. Pythonの収録確認と配布物の制約

[Python 3.13.18公式リリース](https://www.python.org/downloads/release/python-31318/) はCVE-2026-115557を明記する。したがって、前段の「修正版番号が未確認」は解消した。一方、3.13.18はソースのみで、公式Windows／macOSインストーラーはない。

同時点の提供確認は以下のとおり。

| 経路 | 観測結果 | 判断 |
| --- | --- | --- |
| Docker Registry `python:3.13.18-slim-bookworm` | HTTP 404、MANIFEST_UNKNOWN | 未提供。存在しないタグへDockerfileを書き換えない |
| Docker Registry `python:3.13.17-slim-bookworm` | HTTP 200。amd64／arm64等あり | 同梱pip対策版として存在するが、ssl対策済みの代替にはしない |
| docker-library/python のslim-bookworm定義 | PYTHON_VERSIONは3.13.17 | Docker Registryの観測と整合 |
| actions/python-versions のmanifest | 3.13.17は掲載、3.13.18は未掲載 | 既存setup-python経路での3.13.18提供を確認できず |
| uv 0.13.5公式リリース説明 | 管理Pythonの更新先として3.13.17を記載 | uv本体の更新はPython3.13.18の提供証拠ではない。uv管理の3.13.18配布は未確認 |

Dockerの既存タグのindex digestは `sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530`。これは提供状況比較の証拠であり、3.13.17の採用を指示するpinではない。

確認したGitHubファイルblob SHA:

- docker-library/python `3.13/slim-bookworm/Dockerfile`: `6bbeaea525287b1a2fddf67401553688be652b4e`
- actions/python-versions `versions-manifest.json`: `bff7d7859bd37f83c6fbb8b9b16d7f69c8ed4c75`

[Docker公式イメージ定義](https://github.com/docker-library/python/blob/master/3.13/slim-bookworm/Dockerfile)、[Docker公式タグ一覧の正本](https://github.com/docker-library/official-images/blob/master/library/python)、[Actionsの配布manifest](https://github.com/actions/python-versions/blob/main/versions-manifest.json)を照合した。公開Registryのmanifestを認証付き読み取りで確認したが、トークンは記録していない。

## 3. ツールの配布物確認

PyPI公式JSONの `requires_python`、`yanked`、wheelファイルとSHA-256を確認した。以下は将来の取得時の照合値であり、取得後の実行検証はT2で行う。

| 配布物 | SHA-256 |
| --- | --- |
| certifi-2026.10.23-py3-none-any.whl | e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 |
| pip-26.2.2-py3-none-any.whl | fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70 |
| uv-0.13.5-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | fa8d26e08e34c29c0c4e820cf3181757086d547240b4f4d31ff1d8bd810ca946 |
| uv-0.13.5-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.musllinux_1_1_aarch64.whl | 2386c2dc9b59fc1d39b1c500e4319d71d3268232eb3b38e29cd6775d6269e8d4 |

uvのPyPI Python要件は>=3.8。GHCR `ghcr.io/astral-sh/uv:0.13.5` はHTTP 200、Linux amd64／arm64を確認した。index digestは `sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff`。導入時にはタグ／digestと実体を再確認する。

公式JSON: [certifi](https://pypi.org/pypi/certifi/2026.10.23/json)、[pip](https://pypi.org/pypi/pip/26.2.2/json)、[uv](https://pypi.org/pypi/uv/0.13.5/json)。

## 4. 現行アプリ依存のwheel互換性

現行uv.lockのregistry由来82パッケージについて、標準GIL版CPython 3.13とDebian bookwormのglibc 2.36を前提にwheelタグを照合した。Linux x86_64／aarch64の両方で互換タグを持つロック済みwheelを確認し、該当wheelなしは0件だった。

これは配布メタデータによる判定であり、wheelのダウンロード成功、実行時リンク、xmlsec／lxml等の動作、実際の利用CPU全種の保証ではない。3.13.18を使うT3でlocked同期と基準328成功・1スキップの回帰比較を実施する。Windows／macOSやfreethreaded版を新規サポート対象に追加する判断はしていない。

## 5. 実施状態（2026-10-27更新）

T1.1〜T1.4は公式3.13.18の配布確認で完了。T2の隔離ツール/ハッシュ/CA準備とT3の旧lock回帰比較を実施し、T4以降のアプリ依存更新へ進んだ。実体3.13.18で旧lock・更新lockとも328成功/1スキップを確認した。certifi/pipに加え、監査で指摘されたPyJWT/cryptography/Starlette/AnyIO/python-multipart等、完成イメージで見つかったMakoも対象指定で更新した。

実施結果と残件は `docs/security/implementation/2026-10-27/README.ja.md`。OS・内蔵コピー・実IdP・CI/配備CPUの未確認を残し、全体完了とはしない。Keycloakはテスト用IdP代替でモジュール更新とは別。PRは発行しない。

## 6. セキュリティ判断の一次情報

- [Python公式注意喚起](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576/1)
- [Python 3.13.17（同梱pip対策）](https://www.python.org/downloads/release/python-31317/)
- [Python 3.13.18（ssl対策）](https://www.python.org/downloads/release/python-31318/)
- [certifi 2026.10.23公式リリース](https://github.com/certifi/python-certifi/releases/tag/2026.10.23)
- [pip 26.2.2変更履歴](https://pip.pypa.io/en/stable/news/#v26-2-2)
- [uv 0.13.5公式リリース](https://github.com/astral-sh/uv/releases/tag/0.13.5)
- [Debian bookworm CAパッケージ](https://packages.debian.org/bookworm/ca-certificates)
- [Debianの問題CA除外の更新記録](https://tracker.debian.org/news/1813406/accepted-ca-certificates-20250419deb12u2-source-into-oldstable-security/)
- [Debian Brotli修正判定](https://security-tracker.debian.org/tracker/CVE-2026-111497)
- [Debian bookworm libbrotli1](https://packages.debian.org/bookworm/libbrotli1)
