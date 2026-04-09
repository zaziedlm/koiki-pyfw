# LOG-04 Repository/Service 入力データログ是正 作業計画

最終更新: 2026-04-09

## 1. 目的

`LOG-04` は、Repository / Service / 一部 endpoint で
入力値や ORM オブジェクト全体を通常ログへ出している箇所を是正するための作業である。

本タスクでは、以下を原則とする。

- 入力値の生値は通常ログへ出さない
- request payload や ORM `__dict__` の丸ごと出力をやめる
- logger へ渡すのは `field 名の一覧`、件数、識別子など最小限に限定する
- token / password / hashed_password などの機密項目は field 名レベルでも除外する

## 2. 対応方針

### 2.1 共通方針

- `libkoiki/core/logging.py` に、payload から安全な field 名一覧を取り出す helper を置く
- 各 call site は `data=` `payload=` `obj.__dict__` をやめ、`provided_fields=` `update_fields=` へ置き換える
- 認証系と同様に、sanitizer は最終防御とし、呼び出し側でも payload を小さくする

### 2.2 優先度

1. `BaseRepository`
2. `UserService` / `TodoService`
3. `users.py` / `todos.py`
4. `app/repositories/user_sso_repository.py`
5. `events/` `utils/email.py` `tasks/email.py`

## 3. 作業単位

### LOG-04-01 共通 helper 追加

- 目的:
  - payload から安全な field 名一覧を共通取得できるようにする
- 主対象:
  - [`logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
- 対応内容:
  - `get_log_field_names()` を追加
  - `Mapping`、Pydantic model、任意オブジェクトの `__dict__` に対応
  - private key と sensitive key を除外
- 状況:
  - 完了

### LOG-04-02 BaseRepository の入力ログ是正

- 目的:
  - `obj.__dict__` と update payload の丸出しを止める
- 主対象:
  - [`base.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/repositories/base.py)
- 対応内容:
  - `create()` を `field_names=` ログへ変更
  - `update()` を `update_fields=` ログへ変更
- 状況:
  - 完了

### LOG-04-03 User/Todo Service の入力ログ是正

- 目的:
  - Service 層が入力値や更新 payload をそのまま出さないようにする
- 主対象:
  - [`user_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/user_service.py)
  - [`todo_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/todo_service.py)
- 対応内容:
  - `provided_fields=` `update_fields=` へ置換
  - email / title / new_email など raw value を除去
  - `authenticate_user()` の email 生値ログも除去
- 状況:
  - 完了

### LOG-04-04 User/Todo Endpoint の入力ログ是正

- 目的:
  - endpoint 層の `data=` や raw title / email を除去する
- 主対象:
  - [`users.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/users.py)
  - [`todos.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/todos.py)
- 対応内容:
  - `provided_fields=` `update_fields=` へ置換
  - 成功ログから raw email / title を除去
- 状況:
  - 完了

### LOG-04-05 app repository / 周辺ユーティリティの入力ログ是正

- 目的:
  - `LOG-04` の適用を framework 外まで広げる
- 主対象:
  - [`user_sso_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/user_sso_repository.py)
  - [`handlers.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/events/handlers.py)
  - [`publisher.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/events/publisher.py)
  - [`email.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/utils/email.py)
  - [`email.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/tasks/email.py)
- 主な懸念:
  - SSO subject / event payload / email address / subject line の raw 出力
- 状況:
  - 完了

### LOG-04-06 回帰テスト整備

- 目的:
  - 今回の入力ログ是正が戻らないようにする
- 主対象:
  - [`test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
  - [`test_input_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_input_logging.py)
- 状況:
  - 第1弾完了

## 4. 2026-04-09 時点の実施結果

完了済み:

- `get_log_field_names()` を追加
- `BaseRepository.create/update` の raw payload logging を除去
- `UserService` / `TodoService` の raw input logging を除去
- `users.py` / `todos.py` の raw input logging を除去
- `user_sso_repository.py` の raw `sso_subject_id` logging を除去
- `events/handlers.py` `events/publisher.py` の raw event payload logging を除去
- `utils/email.py` `tasks/email.py` の raw email / subject logging を除去
- 代表経路の unit test を追加

未完了:

- `LOG-04` 対象の追加洗い出し
  - `events` 周辺の他モジュール
  - `tasks` / `utils` の派生処理
  - `app` 側の周辺 repository / service

## 5. テスト

現時点での確認コマンド:

```powershell
poetry run pytest tests/unit/core/test_logging_sanitizer.py tests/unit/libkoiki/test_input_logging.py
```

確認済み観点:

- helper が sensitive / private field を除外すること
- repository が `field_names` / `update_fields` を使うこと
- service が raw input value を logger に渡さないこと
- endpoint が `data=` や raw title / email を logger に渡さないこと
- event handler / publisher が raw payload を logger に渡さないこと
- email utility / email task が raw email / subject を logger に渡さないこと

## 6. 次アクション

1. `LOG-04` は現時点の対象範囲として完了扱いにできる
2. 追加の raw input logging が見つかった場合は `LOG-04` の追補として扱う
3. 次は `LOG-05` または `LOG-06` へ進む
