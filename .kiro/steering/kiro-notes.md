# Kiro環境特有の注意点

## このステアリングファイルについて

このファイルはKiro（AI開発環境）およびCodex（サンドボックス実行環境）で作業する際の特有の問題と回避策をまとめています。

**通常のローカル開発では、これらの問題は発生しません。**

---

## 環境変数の問題

### DEBUG変数の衝突

**問題:**
Codexセッションでは、プロセス環境に `DEBUG=release` が継承されることがあります。これはKOIKI-FWの設定ではなく、エージェント実行環境由来の値です。

KOIKI-FWの `Settings.DEBUG` はブール値を期待しますが、Pydanticは `release` を有効なブール値として解釈できません。

**Codex検証時の回避策:**
```bash
# アプリケーション設定をインポートするコマンド実行時は、明示的にDEBUGを設定
DEBUG=True uv run --locked pytest
DEBUG=False uv run --locked uvicorn koiki_ref_app.asgi:app
```

**やってはいけないこと:**
- ❌ アプリケーションコードを変更して `release` を受け入れる
- ❌ `DEBUG=release` をプロジェクト設定として文書化する
- ❌ `.env` ファイルに `DEBUG=release` を追加する

**通常のローカル開発:**
```bash
# .envファイルまたは明示的なブール値を使用
uv sync
uv run --locked pytest
```

---

## uvキャッシュの問題

### サンドボックス環境でのキャッシュアクセス

**問題:**
Codexのサンドボックスコマンドは、ユーザーのデフォルトuvキャッシュ（`AppData\Local\uv\cache`）にアクセスできない場合があります。

これはエージェントサンドボックスの権限問題であり、プロジェクトの依存関係管理の要件ではありません。

**Codex検証時の回避策:**
```bash
# ワークスペースローカルのキャッシュディレクトリを使用
UV_CACHE_DIR=.uv-cache-codex uv sync --locked
```

または、適切な承認を得て同じコマンドを再実行します。

**やってはいけないこと:**
- ❌ `UV_CACHE_DIR=.uv-cache-codex` を通常の開発ワークフローの一部にする
- ❌ `.env` ファイルに `UV_CACHE_DIR` を追加する
- ❌ プロジェクトドキュメントに必須設定として記載する

**通常のローカル開発:**
```bash
# 特別な設定は不要
uv sync
```

---

## 長時間実行コマンドの制限

### 開発サーバーやウォッチャー

**問題:**
Kiroのシェルコマンド実行は、長時間実行されるプロセス（開発サーバー、ビルドウォッチャー、インタラクティブコマンド）には適していません。

**回避策:**
```bash
# ❌ Kiroのシェルで実行しない
uv run --locked uvicorn koiki_ref_app.asgi:app --reload

# ✅ 代わりに、ユーザーに手動実行を推奨
# または、control_pwsh_process ツールを使用してバックグラウンドプロセスとして起動
```

**長時間実行コマンドの例:**
- `uvicorn ... --reload`
- `npm run dev`
- `webpack --watch`
- `jest --watch`
- テキストエディタ（vim, nano）

**対処方法:**
- 単発実行フラグを使用（例: `vitest --run`）
- ユーザーに別ターミナルでの手動実行を推奨
- バックグラウンドプロセスツールを使用

---

## Windows環境でのコマンド

### シェルの違い

**Kiroが動作するシェル:**
- Windows: PowerShell または CMD
- コマンド区切り文字: `;` (PowerShell) または `&` (CMD)

**注意点:**
```bash
# ❌ Bashスタイル（Windowsでは動作しない）
cd frontend && npm run dev

# ✅ PowerShellスタイル
cd frontend; npm run dev

# または、cwdパラメータを使用
# cwd: frontend, command: npm run dev
```

---

## パス区切り文字

### Windows vs Unix

**Windowsでのパス:**
```
c:\Users\kataoka\Desktop\KOIKI-v07\koiki-v07
```

**コマンド内でのパス指定:**
```bash
# ✅ 相対パスを使用（推奨）
uv run --locked pytest tests/test_auth.py

# ✅ スラッシュも使用可能
uv run --locked pytest tests/test_auth.py

# ⚠️ バックスラッシュはエスケープが必要な場合がある
```

---

## テスト実行時の注意

### プロパティベーステスト

**問題:**
プロパティベーステスト（Hypothesis等）は、多数のランダムケースを生成するため、実行時間が長くなる可能性があります。

**対処方法:**
```bash
# タイムアウトを設定
uv run --locked pytest --timeout=300

# または、特定のテストを除外
uv run --locked pytest -m "not slow"
```

---

## データベース接続

### Docker環境での接続

**問題:**
Dockerコンテナ内とホスト環境では、データベース接続文字列が異なります。

**Docker内:**
```bash
DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@db:5432/koiki_todo_db
```

**ホスト環境:**
```bash
DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db
```

**対処方法:**
- `.env` ファイルで環境に応じた設定を使用
- `.env.docker` と `.env.local` を分ける

---

## ファイル監視の制限

### ホットリロードの動作

**問題:**
一部の環境では、ファイル変更の監視が正常に動作しない場合があります。

**対処方法:**
```bash
# ポーリングモードを使用
uv run --locked uvicorn koiki_ref_app.asgi:app --reload --reload-delay 2

# または、手動で再起動
```

---

## まとめ

### Kiro/Codex環境での作業原則

1. **環境変数は明示的に設定** - 特にDEBUG変数
2. **キャッシュ問題は一時的回避策** - UV_CACHE_DIRは最終手段
3. **長時間実行コマンドは避ける** - 単発実行またはバックグラウンドプロセス
4. **Windowsシェルを意識** - コマンド区切り文字とパス
5. **通常のローカル開発とは区別** - これらは環境固有の問題

---

## Skills との協調

環境問題のトラブルシューティングには以下のSkillsが役立ちます：

- **koiki-testing**: テスト実行の詳細ガイダンス
- **koiki-project-overview**: プロジェクト全体の理解

---

## 参照先

詳細な情報は以下を参照してください：

- **docs/agent/environment.md**: 環境問題の詳細な説明
- **commands.md**: 基本的なコマンド集
- **AGENTS.md**: エージェント向けエントリーポイント
