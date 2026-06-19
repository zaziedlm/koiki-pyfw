# Dev Container セットアップ

## 前提条件

- Docker Desktop（WSL2 バックエンド有効）
- VSCode 拡張: [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)、[Remote - WSL](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl)
- WSL2 上の Linux ディストリビューション（Ubuntu 推奨）

## セットアップ手順

### 1. リポジトリを WSL2 上にクローンする

**Windows の `C:\` 配下ではなく、WSL2 の Linux ファイルシステム上にクローンしてください。**
Windows 側にクローンするとファイルシステムの性質上、大幅な性能劣化が発生します。

```bash
# WSL2 ターミナル上で実行
cd ~
git clone <repository-url> koiki-pyfw
cd koiki-pyfw
```

### 2. 社内 CA 証明書を配置する

`docker/certs/nscacert.pem` に証明書ファイルを配置してください。

> **配置方法はプロジェクト Wiki を参照してください。**
> 証明書が配置されていない場合、イメージビルドが失敗します。

### 3. VSCode で開く

```bash
# WSL2 ターミナル上で実行
code .
```

VSCode が起動したら、右下の通知または コマンドパレット（`Ctrl+Shift+P`）から
**「Dev Containers: Reopen in Container」** を実行してください。

初回はイメージのビルドと依存関係のインストールが行われます（数分かかる場合があります）。

## 起動後の操作

コンテナ起動時に DB マイグレーションが自動実行されます。

| 操作 | VSCode タスク |
|------|--------------|
| バックエンド起動（FastAPI） | `Start Backend` |
| フロントエンド起動（Next.js） | `Start Frontend` |
| 両方同時起動 | `Start All` |
| DB マイグレーション（手動） | `DB Migration (upgrade head)` |

タスクはコマンドパレットから「Tasks: Run Task」で実行できます。

ポートは自動転送されます。

| ポート | 用途 |
|--------|------|
| 8000 | FastAPI バックエンド |
| 3000 | Next.js フロントエンド |
| 5432 | PostgreSQL |

## Keycloak（オプション）

SSO 機能が必要なプロジェクトでのみ使用します。通常起動では含まれません。

```bash
docker compose -f .devcontainer/docker-compose.devcontainer.yml --profile keycloak up
```

## Windows ネイティブでの開発（代替）

Dev Container を使わず Windows 上で直接開発することも可能です。
その場合は `.vscode/settings.json` の設定が適用されます。
ただし、パフォーマンスおよび環境の一貫性の観点から **Dev Container（WSL2）を推奨します**。
