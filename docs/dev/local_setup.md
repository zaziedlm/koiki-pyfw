# 開発環境セットアップガイド

## ローカル開発環境のセットアップ

このプロジェクトでは、`components/libkoiki` フレームワークと `components/koiki_ref_app` 参照アプリを同時に開発できる構造になっています。
推奨 Python バージョンは **3.11.7** です。以下の手順でセットアップしてください。

**注意**: `uv` への移行は計画済みですが、現時点の実運用手順はまだ Poetry ベースです。

### 0. Python 3.11.7 のインストール (pyenv 使用)

```powershell
# Windowsの場合（PowerShell）
pyenv install 3.11.7
pyenv local 3.11.7
```

### 1. 仮想環境の作成

#### 従来の方法（venv）（非推奨）

```powershell
# 注意: このプロジェクトではpoetryへの完全移行が行われており、この方法は推奨されません
python -m venv venv
venv\Scripts\activate  # Windowsの場合
```

#### poetry を使用する方法（推奨）

```powershell
# Poetry 2.x のインストール（初回のみ）
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Poetry 2.x 設定の最適化
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
poetry config installer.parallel true
poetry config installer.max-workers 10

# 依存関係の検証とインストール（Poetry 2.x）
poetry check --lock
poetry install

# Poetry 2.x: dependency groups の活用
poetry install --with dev

# 仮想環境の有効化
poetry shell
```

### 2. ローカル component の取り込み

#### 従来の方法（pip）（非推奨）

```powershell
# 注意: component は root pyproject.toml から参照されます
# 追加の pip install -e は不要です
```

#### poetry を使用する方法（推奨）

```powershell
# Poetry 2.x: libkoiki は既に root pyproject.toml で
# components/libkoiki をローカル dependency として参照します
# 追加の手順は不要です
```

### 3. アプリケーション依存関係のインストール

#### 従来の方法（pip）（非推奨）

```powershell
# 注意: このプロジェクトではpoetryへの完全移行が行われており、この方法は推奨されません
pip install -r requirements.txt
```

#### poetry を使用する方法（推奨）

```powershell
# Poetry 2.x: 依存関係グループを指定してインストール
poetry install --with dev

# または、特定のグループのみインストール
poetry install --only=main
poetry install --only=dev
```

### 4. アプリケーションの実行

```powershell
# Poetry 2.x 推奨方法: 互換 wrapper 経由で直接実行
poetry run uvicorn app.main:app --reload

# または、仮想環境内で実行
poetry shell
uvicorn app.main:app --reload

# 開発時の便利なコマンド
poetry run pytest  # テスト実行
poetry run pytest --cov  # カバレッジ付きテスト実行
```

補足:

- 実ソースの正本は `components/koiki_ref_app/src/koiki_ref_app/` にあります
- `app.main:app` は Stage 6 時点では互換導線として維持しています
- 将来的な正式 ASGI path は `koiki_ref_app.asgi:app` です

## パッケージング

`libkoiki` を別のプロジェクトで使用する場合は、Poetry 2.x のビルド機能を使用します：

```powershell
# libkoikiディレクトリに移動
cd components/libkoiki

# Poetry 2.x でビルド（推奨）
poetry build

# または、従来の方法
python -m build
```

作成したパッケージは `dist` ディレクトリに出力されます。

## Poetry 2.x の新機能

### 依存関係グループの使用

```powershell
# 開発依存関係を含めてインストール
poetry install --with dev

# 複数のグループを指定
poetry install --with dev,test

# 特定のグループのみ
poetry install --only dev

# グループを除外
poetry install --without dev
```

### パフォーマンス最適化

Poetry 2.x では以下の設定でパフォーマンスを向上できます：

```powershell
# 並列インストールの有効化
poetry config installer.parallel true

# 最大ワーカー数の設定
poetry config installer.max-workers 10

# インプロジェクト仮想環境の使用
poetry config virtualenvs.in-project true
```
