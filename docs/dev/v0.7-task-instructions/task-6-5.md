# Task 6-5: docs / instructions / local ops path 更新

## 目的

新しい `components/` / `apps/` 構造に合わせて、開発・運用 docs と `.github/instructions` の旧 path 前提を解消する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-6-4.md`
- `README.md`
- `docs/dev/local_setup.md`
- `docs/testing/認証系APIテストガイド.md`
- `ops/README.md`
- `.github/instructions/*.instructions.md`

## 事前条件

- [Task 6-4](./task-6-4.md) が完了している

## 確認観点

- `components/libkoiki` / `components/koiki_ref_app` の path へ追随しているか
- root `app/` を互換 wrapper として説明できているか
- test path / coverage / branch trigger が docs と一致しているか
- `.github/instructions` の `applyTo` が新構造へ追随しているか

## 実施手順

1. `README.md` のディレクトリ構造、CI ブランチ、テスト実行例を新構造へ更新する
2. `docs/dev/local_setup.md` の component path と現行 Poetry ベース手順を更新する
3. `docs/testing/認証系APIテストガイド.md` の test path / coverage path を新構造へ更新する
4. `ops/README.md` に新しい backend 正本配置の注記を追加する
5. `.github/instructions` の `applyTo` と本文中の旧 `libkoiki/` / `app/` 前提を新構造へ更新する

## 成果物

- 更新済み `README.md`
- 更新済み local setup / test guide / ops docs
- 更新済み `.github/instructions`

## 検証

- docs と instructions に旧 `libkoiki/` / root `alembic/` 前提が残っていない
- docs 上の test path / branch 名が実構成と一致している

## 完了条件

- docs / instructions / ops 手順が Stage 5 の構造変更へ追随している
- Task 6-6 で Stage 6 横断検証へ進める

## 実施結果

Task:

- Task 6-5: docs / instructions / local ops path 更新

変更内容:

- `README.md` を新構造へ追随させた
  - `components/libkoiki` / `components/koiki_ref_app` / `apps/` / `frontend/` を含むディレクトリ構造へ更新
  - coverage 付き test 実行例を `koiki_ref_app` と component test path へ更新
  - CI branch trigger を `main` / `dev/v0.7` / `support/0.6` / `topic/*` / `feature/*` に更新
  - root `app/` を互換 wrapper として明記
- `docs/dev/local_setup.md` を更新した
  - `components/libkoiki` / `components/koiki_ref_app` 前提の説明へ更新
  - `uv` は計画済み、現時点の実運用は Poetry ベースであると明記
  - `cd components/libkoiki` で package build する手順へ更新
- `docs/testing/認証系APIテストガイド.md` を更新した
  - `components/libkoiki/tests/...` / `components/koiki_ref_app/tests/...` を使う test path に更新
  - coverage target を `koiki_ref_app` / `libkoiki` に更新
  - app 側サンプルコードの import を `koiki_ref_app` ベースへ更新
- `ops/README.md` に新しい backend 正本配置の注記を追加した
- `.github/instructions` を更新した
  - `architecture.instructions.md`
  - `libkoiki.instructions.md`
  - `app.instructions.md`
  - `auth-security.instructions.md`
  - `testing.instructions.md`
  の `applyTo` と本文を新構造へ追随させた

未解決事項:

- root `README.md` は Stage 6 時点で最小限の追随に留めており、`uv` 実移行後に再度整理余地がある
- `ops/README.md` の実行コマンド自体はまだ `docker-compose` 表記を含むため、将来 `docker compose` へ統一する余地がある

検証結果:

- docs / instructions 上の主要な旧 path 前提は `components/` / `apps/` 構造へ更新された
- branch 名、coverage target、test path は現行構成と整合する状態になった
- `.github/instructions` の `applyTo` も component 配下の実パスへ追随した

次タスクへ渡す事項:

- Task 6-6 で Alembic / CI / Docker / docs の横断整合を確認する
- Stage 6 終了時点で docs と実構成の差分が残る箇所を最終洗い出しする

## 次タスク

- [Task 6-6](./task-6-6.md)
