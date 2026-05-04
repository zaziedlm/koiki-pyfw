# DM-14 API ownership / sample feature boundary policy

作成日: 2026-05-04

対象タスク:

- `docs/dev/deferred-maintenance-tasks.ja.md` の `DM-14`

## 1. 目的

v0.7 以降の API 実装で、`components/libkoiki/`、`components/koiki_ref_app/`、`apps/` のどこに何を置くかを場当たりにしない。

特に Todo タスク管理 API のように、サンプルとして有用だが業務 API にも見える機能について、framework 層に置く条件と reference app 層に置く条件を明確にする。

この PR では、コード移動や router 構成変更は行わない。
まず所有境界と判断基準を文書化し、Todo API の現在位置づけと後続判断を明確にする。

## 2. 現行確認

Todo タスク管理 API は、現状では主に `components/libkoiki/` 側に実装されている。

代表的な配置:

- `components/libkoiki/src/libkoiki/models/todo.py`
- `components/libkoiki/src/libkoiki/schemas/todo.py`
- `components/libkoiki/src/libkoiki/repositories/todo_repository.py`
- `components/libkoiki/src/libkoiki/services/todo_service.py`
- `components/libkoiki/src/libkoiki/api/v1/endpoints/todos.py`
- `components/libkoiki/src/libkoiki/api/v1/router.py`

`components/koiki_ref_app/` 側では、reference app の `app_factory.py` が `libkoiki` の API router を include することで Todo API を利用している。

また、`components/koiki_ref_app/src/koiki_ref_app/models/__init__.py` では `TodoModel` を re-export している。

このため、Todo は現在「reference app 固有の業務機能」ではなく、「libkoiki に含まれる framework sample / starter capability」として動作している。

## 3. リスク

現行構成のままでも動作上の問題はないが、次の混乱リスクがある。

- Todo が `libkoiki` にあるため、業務 API も framework 側へ置いてよいように見える
- `libkoiki.api.v1.router` が `/todos` を標準 include しており、framework 利用アプリへ sample API が常時入る構造に見える
- `koiki_ref_app` 側には Todo の業務実装がほぼないため、reference app feature なのか framework sample なのか境界が曖昧
- 今後 `apps/` や案件固有 API を足す際、配置判断がぶれやすい

## 4. API ownership policy

### 4.1 `components/libkoiki/` に置く API

`components/libkoiki/` に置ける API は、複数アプリで再利用する framework capability に限る。

該当例:

- authentication / token / password / user / RBAC
- security monitoring / audit / rate limit
- common persistence / schema / repository / service patterns
- starter application が共通で持ってよい最小 sample API

判断条件:

- 特定業務ドメインに依存しない
- 複数アプリで同じ contract として再利用できる
- application-specific な workflow や外部 integration 判断を含まない
- framework 利用者に exposed API として説明できる

### 4.2 `components/koiki_ref_app/` に置く API

`components/koiki_ref_app/` に置く API は、reference app の business behavior または application-level composition である。

該当例:

- SSO / SAML の reference app integration
- business clock など current reference app 固有の workflow
- framework capability を組み合わせた app-level API
- reference app の UI / frontend contract に強く結びつく API

判断条件:

- 現在の reference app 固有の業務判断を含む
- integration や deployment 前提が current project に依存する
- 他アプリへそのまま再利用するには抽象化が足りない
- framework 側へ置くと project-specific assumption が混ざる

### 4.3 `apps/` に置く API

`apps/` は downstream 案件固有 backend API 実装の予約領域である。

該当例:

- 特定顧客・案件・業務に閉じた API
- reusable framework に戻す前の業務拡張
- reference app の標準機能として一般化しない API

判断条件:

- framework / reference app の正本へすぐ戻すべきではない
- 案件固有の table、workflow、外部 integration を含む
- starter として全利用者へ提供するには narrow すぎる

## 5. Todo API の暫定方針

Todo API は、当面 `libkoiki` の `framework sample / starter capability` として維持する。

理由:

- v0.6 系から Todo sample として存在し、認証済みユーザーと owner scoped CRUD の最小例として機能している
- frontend のタスク管理 sample と結びつき、v0.7 の動作確認にも利用されている
- いきなり `koiki_ref_app` 側へ移すと router、model relation、tests、frontend contract、migration の確認範囲が広がる

ただし、今後の新規業務 API を Todo と同じ理由で `libkoiki` に置いてよいわけではない。

Todo は `sample / starter capability` であり、business-specific API の配置先例ではない。

## 6. 後続判断候補

Todo API の最終形は、v0.7.0 後に次のいずれかで判断する。

### Option A: `libkoiki` の sample router として明示維持

- `libkoiki` 側に残す
- `ToDos Sample` として明確に説明する
- framework 利用者が sample router を include / exclude できる構成を検討する

### Option B: `koiki_ref_app` 側へ移す

- Todo を reference app の sample feature として扱う
- model / schema / repository / service / endpoint を `koiki_ref_app` 側へ移す
- `libkoiki` には generic CRUD / ownership pattern だけを残すか判断する

### Option C: `libkoiki` に generic base capability を残し、Todo concrete を app 側へ置く

- reusable ownership / CRUD pattern を `libkoiki` に残す
- Todo concrete model / endpoint は `koiki_ref_app` に置く
- 最も整理された形だが、抽象化が増えるため v0.7.0 前には行わない

## 7. 完了条件

- API ownership policy が文書化されている
- Todo API の現状位置づけが `framework sample / starter capability` として説明されている
- 新規 business API を安易に `libkoiki` へ置かない方針が明記されている
- Todo のコード移動や router 変更をこの PR で行わないことが明記されている
- 後続判断候補が整理されている

## 8. 確認コマンド

```powershell
rg -n "todo|todos|Todo" components/libkoiki/src components/koiki_ref_app/src components/libkoiki/tests components/koiki_ref_app/tests docs/agent README.md -S
rg --files components/libkoiki/src components/koiki_ref_app/src | rg "todo|router|dependencies|app_factory|asgi"
```

## 9. 結論

DM-14 では、Todo API の配置をすぐ変更しない。

まず、v0.7 以降の API ownership policy を明文化し、Todo を `libkoiki` の sample / starter capability として暫定維持する。

実際の Todo 移動、optional router 化、または generic base capability 化は、v0.7.0 release preparation 後の別 PR で扱う。

## 10. 次タスク

DM-14 の次は `DM-15: Agent guidance / Skills consistency review` とする。

理由:

- `DM-14` で整理した API ownership policy は、人間の開発者だけでなく AI agent の作業判断にも影響する
- Codex、Claude Code、GitHub Copilot が `components/libkoiki/`、`components/koiki_ref_app/`、`apps/` の境界を同じように判断できる必要がある
- v0.7.0 release preparation の前に agent-facing guidance の一貫性を確認しておくと、README / release note / agent docs の説明がぶれにくい

推奨順:

1. `DM-14`: API ownership / sample feature boundary policy
2. `DM-15`: Agent guidance / Skills consistency review
3. `DM-13`: v0.7.0 release preparation
4. `DM-12-C`: `app.main:app` 互換終了判断

DM-15 では、`AGENTS.md`、`docs/agent/`、`docs/agent/skills/`、`.github/copilot-instructions.md`、`.github/instructions/*.instructions.md`、Claude Code 向け guidance を横断確認する。
大きな Skill 実体変更やファイル移動が必要な場合は、DM-15 内でさらに後続 PR へ分ける。
