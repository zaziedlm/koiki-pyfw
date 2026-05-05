# Task 0-3: v0.6 安定基準点の固定

## 目的

`v0.7` 再編の最中でも `v0.6.x` 保守を継続できるよう、保守基準点を固定する。

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)

## 事前条件

- [Task 0-2](./task-0-2.md) が完了している
- 現在の `v0.6` 開発突端が `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` であることを確認済みである

## 確認対象

- `v0.6` の安定基準とするコミット
- 付与するタグ名
- `support/0.6` の切り出し起点
- `main` の切り出し基点
- `dev/v0.7` の切り出し基点
- 基準ブランチ名

## 実施手順

1. `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` の `HEAD` を確認する
2. その `HEAD`、または直近の安定コミットを `v0.6` 保守基準として妥当か判断する
3. タグ名を決める
4. `support/0.6` をどのコミットから切るか記録する
5. `main` と `dev/v0.7` も同じ基点、またはその確定コミットから切り出す前提を記録する
6. `main`、`dev/v0.7`、`support/0.6` の分岐点として参照できるよう記録を残す

## 成果物

- 基準ブランチ名
- 安定基準コミット SHA
- タグ名
- `support/0.6` 切り出し基点メモ
- `main` 切り出し基点メモ
- `dev/v0.7` 切り出し基点メモ

## 検証

- `git log` とタグ一覧で基準点を特定できる
- `support/0.6` をその基点から再現できる
- `main` と `dev/v0.7` の切り出し元がどのブランチで、どのコミットかを一意に説明できる

## 完了条件

- `v0.7` 再編と `v0.6.x` 保守を並走できる基準点が固定されている
- `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` を正式基点とする扱いが記録されている

## 実施結果

Task:

- Task 0-3: v0.6 安定基準点の固定

変更内容:

- `samlauth-api-docker-multicontainer-oidcpyjwt-userT-Skills-logSecurity` の `HEAD` を基準確認対象とし、現在の基点コミットを `523cb79fcc541643d9809e539b2abadee982d8bd` に固定した
- 同コミットに、基準タグ `v0.6-next-base` を作成した
- 同コミットに、ローカルブランチ `main` を作成した
- 同コミットに、ローカルブランチ `support/0.6` を作成した
- `dev/v0.7` も同じ `523cb79` を基点に切る方針を確定した
- これにより、`main`、`dev/v0.7`、`support/0.6`、`v0.6-next-base` が同一基点 `523cb79` を共有する運用方針を確定した

未解決事項:

- `main` と `support/0.6` はローカル参照として作成済みだが、remote への push と default branch 切替は未実施
- `dev/v0.7` は長命ブランチモデルに追加したため、ローカル参照作成と remote push は別途実施が必要
- `v0.6-next-base` は基準タグとして作成したが、最終的な公開版タグ名を `v0.6.2` などへ置き換えるかは別判断
- branch protection 設定は GitHub 側で別途実施が必要

検証結果:

- `v0.6-next-base` が `523cb79fcc541643d9809e539b2abadee982d8bd` を指していることを確認した
- `main` が `523cb79fcc541643d9809e539b2abadee982d8bd` を指していることを確認した
- `support/0.6` が `523cb79fcc541643d9809e539b2abadee982d8bd` を指していることを確認した
- `dev/v0.7` も同一コミットを基点に切る前提で記録されていることを確認した
- `git branch --list` と `git tag --list` で、参照名がローカル Git 上に存在することを確認した

次タスクへ渡す事項:

- Stage 1 以降の作業ブランチは、`main` を `v0.7` 公開本線、`dev/v0.7` を `v0.7` 開発統合線、`support/0.6` を `v0.6.x` 保守線として扱う
- remote default branch はまだ `master` のため、GitHub 側の切替は別操作として扱う
- Stage 1 の `topic/metadata-cleanup` は `dev/v0.7` を基準に切る

## 次タスク

- [Task 1-1](./task-1-1.md)
