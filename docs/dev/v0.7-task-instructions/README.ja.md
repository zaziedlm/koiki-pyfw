# KOIKI-FW v0.7 個別タスク指示書

本ディレクトリは、[v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md) の個別実行指示書を収録するものです。
現時点では、初期タスクに加えて Stage 2 継続実装タスク `Task 2-6` から `Task 2-10` も含みます。

Stage 2 の `uv` 実移行後に残る Poetry 関連 follow-up は、次の文書で管理します。

- [v0.7-stage2-uv-follow-up-plan.ja.md](../v0.7-stage2-uv-follow-up-plan.ja.md)

## 使い方

- 実作業は、原則として番号順に進める
- 各タスクは、対応する指示書に従って実施する
- タスク完了後は、元のタスク分解書にある実行記録テンプレート形式で結果を残す
- 前提が崩れた場合は、後続に進まず、計画書とタスク分解書を更新する
- 個別タスク指示書を変更した場合は、計画書とタスク分解書の記述も必要に応じて同期させる
- 計画書に変更が入る場合は、日本語版と英語版の両方を確認し、必要に応じて同期更新する

## 収録タスク

1. [Task 0-1](./task-0-1.md)
2. [Task 0-2](./task-0-2.md)
3. [Task 0-3](./task-0-3.md)
4. [Task 1-1](./task-1-1.md)
5. [Task 1-2](./task-1-2.md)
6. [Task 1-3](./task-1-3.md)
7. [Task 1-4](./task-1-4.md)
8. [Task 1-5](./task-1-5.md)
9. [Task 1-6](./task-1-6.md)
10. [Task 2-1](./task-2-1.md)
11. [Task 2-2](./task-2-2.md)
12. [Task 2-3](./task-2-3.md)
13. [Task 2-4](./task-2-4.md)
14. [Task 2-5](./task-2-5.md)
15. [Task 2-6](./task-2-6.md)
16. [Task 2-7](./task-2-7.md)
17. [Task 2-8](./task-2-8.md)
18. [Task 2-9](./task-2-9.md)
19. [Task 2-10](./task-2-10.md)

## 推奨進行順

- まず Stage 0 を完了する
- 次に Stage 1 を通しで完了する
- その後に Stage 2 へ入る
- Stage 2 の方針タスク `Task 2-1` から `Task 2-5` 完了後は、継続実装タスク `Task 2-6` から `Task 2-10` を branch 単位で進める
- `Task 2-10` 完了後は、`v0.7-stage2-uv-follow-up-plan.ja.md` の FU-1 から順に Poetry 残存整理を進める

この順序を守ることで、`uv` 移行や構造移動の前提を崩さずに進められます。
