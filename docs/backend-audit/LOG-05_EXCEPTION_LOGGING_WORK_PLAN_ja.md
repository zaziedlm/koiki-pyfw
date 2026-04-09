# LOG-05 例外・DB エラーログ是正 作業計画

最終更新: 2026-04-09

## 1. 目的

`LOG-05` は、例外処理と DB セッション管理まわりで、
内部詳細や入力値が通常ログへ過剰に出る状態を是正するための作業である。

本タスクでは、以下を原則とする。

- ユーザー向け `detail` と、内部ログ情報は分離する
- 通常ログでは SQL 文、入力値、header 全量、request body を出さない
- 例外ログは `error_type`、`status_code`、`path`、`method` など最小限に限定する
- validation error は `field 名` と `理由` に留める

## 2. 対応方針

### 2.1 優先対象

1. [`error_handlers.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/error_handlers.py)
2. [`session.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/db/session.py)

### 2.2 基本方針

- `HTTPException` のログから `detail` と `headers` の生値を外す
- `BaseAppException` は `error_code` と `status_code` 中心で記録する
- `RequestValidationError` は `loc` `msg` `type` のみを残し、`input` を落とす
- `SQLAlchemyError` は `db_exception_type` と driver 側例外型だけを残し、`str(exc)` を出さない
- DB セッション層は `error_type` と rollback 成否のみを記録し、元メッセージ全文は出さない

## 3. 作業単位

### LOG-05-01 error_handlers 是正

- 目的:
  - API 例外ログから過剰な detail を除く
- 主対象:
  - [`error_handlers.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/error_handlers.py)
- 対応内容:
  - `http_exception_handler` から `detail` / `headers` を除去
  - `base_app_exception_handler` から `detail` を除去
  - `validation_exception_handler` の出力を `loc` `msg` `type` 中心に縮小
  - `db_exception_handler` から `str(exc)` を除去し、例外型のみを残す
- 状況:
  - 完了

### LOG-05-02 db/session 是正

- 目的:
  - DB セッション層の error logging から raw exception 文字列を除く
- 主対象:
  - [`session.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/db/session.py)
- 対応内容:
  - `error=str(...)` をやめ、`error_type` へ置換
  - rollback 失敗時も `original_error_type` のみ記録
  - connection failure / init failure も raw message を出さない
- 状況:
  - 完了

### LOG-05-03 回帰テスト追加

- 目的:
  - 例外 detail、headers、validation input、DB 例外文字列の再流出を防ぐ
- 主対象:
  - [`test_error_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py)
- 状況:
  - 完了

### LOG-05-04 周辺例外ログの横展開

- 目的:
  - service / decorator / middleware で同種の raw error logging が残っていないか整理する
- 主対象候補:
  - [`auth_decorators.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/auth_decorators.py)
  - [`transaction.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/transaction.py)
  - [`sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/sso_service.py)
  - [`saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)
- 対応内容:
  - decorator / transaction / SSO / SAML service の通常ログから raw exception 文字列を除去
  - 共通 helper `get_error_type_name()` を使い、`error_type` / `original_error_type` へ統一
  - user-facing の `HTTPException.detail` は維持しつつ、内部ログとは分離する
- 状況:
  - 完了

## 4. 2026-04-09 時点の実施結果

完了済み:

- `HTTPException` ログから `detail` / `headers` を除去
- `BaseAppException` ログから `detail` を除去
- validation error ログから `input` を除去
- DB 例外ログから `str(exc)` を除去
- DB セッションログを `error_type` / `original_error_type` 中心へ変更
- `LOG-05` 第1弾の unit test を追加
- `auth_decorators.py` の validation / authentication / unexpected error logging を `error_type` へ統一
- `transaction.py` の commit / rollback / transaction failure logging を `error_type` 系へ統一
- `sso_service.py` の token verification / JWKS / internal token pair まわりの error logging を `error_type` へ統一
- `saml_service.py` の AuthnRequest / verification / logout / internal token pair まわりの error logging を `error_type` へ統一
- `LOG-05-04` 横展開の回帰テストを追加

未完了:

- `security_logger` 側のイベント粒度整理
- middleware / audit logging と連動した例外記録ポリシーの整理

## 5. テスト

現時点での確認コマンド:

```powershell
poetry run pytest tests/unit/libkoiki/test_error_logging.py
poetry run pytest tests/unit/app/services/test_sso_service.py
poetry run pytest tests/unit/app/services/test_saml_service.py
poetry run pytest tests/unit/core/test_logging_sanitizer.py tests/unit/libkoiki/test_error_logging.py tests/unit/app/services/test_sso_service.py tests/unit/app/services/test_saml_service.py
```

確認済み観点:

- `HTTPException` で `detail` / `headers` を logger に渡さないこと
- `BaseAppException` で `detail` を logger に渡さないこと
- validation error で `input` が logger に残らないこと
- `IntegrityError` で DB 例外文字列を logger に渡さないこと
- `get_db()` と `connect_db()` が raw error 文字列ではなく `error_type` を記録すること
- `auth_decorators.py` が unexpected error を `error_type` で記録し、raw error を残さないこと
- `transaction.py` が transaction failure / rollback failure を `error_type` 系で記録すること
- `sso_service.py` が token verification / internal token pair failure で `error_type` のみを記録すること
- `saml_service.py` が token decode / internal token pair failure で `error_type` のみを記録すること

## 6. 次アクション

1. `LOG-05` は完了扱いとし、残課題は `LOG-06` / `LOG-07` 側へ引き継ぐ
2. `security_logger` のイベント粒度整理を別タスクで進める
3. その後 `LOG-06` または `LOG-07` へ進む
