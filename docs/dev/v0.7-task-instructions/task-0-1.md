# Task 0-1: v0.7 作業開始基準の確認

## 目的

`v0.7` 再編作業の前提条件を固定し、作業中に前提がぶれない状態を作る。

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)

## 事前条件

- 計画書の日本語版が最新である
- `components/`、`apps/`、`frontend/` の方向性について大きな未決定論点が残っていない

## 確認対象

- `components/` は upstream の再利用資産置き場であること
- `apps/` は案件固有アプリ置き場であること
- `frontend/` は root 維持であること
- Skills は段階再編であること
- MCP は今回スコープ外であること
- テンプレート配布は copy-first であること

## 実施手順

1. 計画書の最新版パスを確認する
2. 目標構成と責務ルールの節を読み直す
3. まだ未解決の大論点があるかを洗い出す
4. 未解決論点がなければ、「この計画書を v0.7 作業開始基準とする」と記録する
5. 論点が残る場合は、Task 0-2 へ進まずに計画書へ戻す

## 成果物

- `v0.7` の作業開始基準メモ
- 未解決論点一覧、または「未解決なし」の記録

## 検証

- 関係者が参照する計画書パスが 1 つに定まっている
- 次の文を迷わず言える
  - `components/` は upstream 再利用資産
  - `apps/` は案件固有アプリ
  - `frontend/` は root のテンプレート UI スターター

## 完了条件

- 作業開始基準が記録されている
- Stage 0 の後続タスクが、この前提で進められる

## 実施結果

Task:

- Task 0-1: v0.7 作業開始基準の確認

変更内容:

- `v0.7` 作業開始基準として、次の 2 文書を同期対象の計画書ペアとして固定した
  - `docs/dev/v0.7-directory-reorganization-plan.ja.md`
  - `docs/dev/v0.7-directory-reorganization-plan.md`
- これらの計画書を受ける実行系文書として、次を作業基準に固定した
  - `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
  - `docs/dev/v0.7-task-instructions/`
- 前提条件として、次を確認した
  - `components/` は upstream 再利用資産
  - `apps/` は案件固有アプリ
  - `frontend/` は root のテンプレート UI スターター
  - MCP は今回スコープ外
  - テンプレート配布は copy-first
- Stage 0 の前提として、現在の開発突端ブランチ `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を `main` 切り出し元候補として扱う方針と、現行計画に矛盾がないことを確認した

未解決事項:

- なし

検証結果:

- 計画書日本語版と英語版の双方に、文書同期ルールが存在することを確認した
- 計画書日本語版で `components/`、`apps/`、`frontend/`、MCP out-of-scope、copy-first が明記されていることを確認した
- 現在の checkout ブランチが `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` であることを確認した
- 現時点で、Task 0-2 へ進行を止める未解決の大論点は見当たらなかった

次タスクへ渡す事項:

- Task 0-2 では、`main` と `support/0.6` の役割確定に加え、`samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を `main` の正式候補基点として明文化する
- Task 0-3 では、上記ブランチの `HEAD` と安定コミットの関係を記録し、`support/0.6` と `main` の切り出し基点を確定する

## 次タスク

- [Task 0-2](./task-0-2.md)
