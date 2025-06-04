# 開発環境セットアップガイド

## ローカル開発環境のセットアップ

このプロジェクトでは、`libkoiki` フレームワークと `app` アプリケーションを同時に開発できる構造になっています。
推奨 Python バージョンは **3.11.7** です。以下の手順でセットアップしてください。

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
# poetryのインストール（初回のみ）
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# poetryを使った仮想環境の作成と依存関係のインストール
poetry env use python
poetry install

# 仮想環境の有効化
poetry shell
```

### 2. libkoikiを開発モードでインストール

#### 従来の方法（pip）（非推奨）

```powershell
# 注意: このプロジェクトではpoetryへの完全移行が行われており、この方法は推奨されません
pip install -e ./libkoiki
```

#### poetry を使用する方法（推奨）

```powershell
poetry add --editable ./libkoiki
```

### 3. アプリケーション依存関係のインストール

#### 従来の方法（pip）（非推奨）

```powershell
# 注意: このプロジェクトではpoetryへの完全移行が行われており、この方法は推奨されません
pip install -r requirements.txt
```

#### poetry を使用する方法（推奨）

```powershell
poetry install
```

### 4. アプリケーションの実行

```powershell
# 直接実行
poetry run uvicorn app.main:app --reload

# または、仮想環境内で実行
poetry shell
uvicorn app.main:app --reload
```

## パッケージング

`libkoiki` を別のプロジェクトで使用する場合は、以下のようにビルドします：

```
cd libkoiki
python -m build
```

作成したパッケージは `dist` ディレクトリに出力されます。
