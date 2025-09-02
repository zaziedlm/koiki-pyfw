# macOS (Darwin) システムコマンド

## 基本ファイル操作
- `ls -la`: ファイル・ディレクトリ一覧（詳細表示）
- `cd <directory>`: ディレクトリ移動
- `pwd`: 現在のディレクトリパス表示
- `mkdir -p <directory>`: ディレクトリ作成（親ディレクトリも作成）
- `cp -r <source> <destination>`: ファイル・ディレクトリコピー
- `mv <source> <destination>`: ファイル・ディレクトリ移動/リネーム
- `rm -rf <file_or_directory>`: ファイル・ディレクトリ削除

## 検索・テキスト処理
- `find <path> -name "<pattern>"`: ファイル検索
- `grep -r "<pattern>" <directory>`: テキスト検索（再帰）
- `grep -i "<pattern>" <file>`: 大文字小文字を無視して検索
- `cat <file>`: ファイル内容表示
- `head -n <number> <file>`: ファイル先頭行表示
- `tail -f <file>`: ファイル末尾をリアルタイム表示

## プロセス・システム情報
- `ps aux | grep <process>`: プロセス検索
- `top`: システムリソース使用状況
- `kill -9 <pid>`: プロセス強制終了
- `lsof -i :<port>`: ポート使用状況確認
- `df -h`: ディスク使用量確認
- `free -h`: メモリ使用量確認（Linux。macOSでは`vm_stat`）

## ネットワーク
- `curl -X GET <url>`: HTTP リクエスト送信
- `ping <host>`: ネットワーク接続確認
- `netstat -an | grep <port>`: ネットワーク接続状況

## Git操作
- `git status`: リポジトリ状態確認
- `git diff`: 変更差分表示
- `git log --oneline -n 10`: コミット履歴（簡潔版）
- `git branch`: ブランチ一覧
- `git checkout -b <branch_name>`: 新ブランチ作成・切替

## Docker関連（macOS Docker Desktop）
- `docker ps`: 実行中コンテナ一覧
- `docker logs -f <container>`: コンテナログリアルタイム表示
- `docker-compose up -d`: バックグラウンドでサービス起動
- `docker-compose down`: サービス停止・削除
- `docker system prune`: 不要リソース削除

## macOS固有
- `brew install <package>`: Homebrewパッケージインストール
- `open <file_or_directory>`: Finderで開く
- `pbcopy < <file>`: ファイル内容をクリップボードにコピー
- `pbpaste`: クリップボード内容を貼り付け