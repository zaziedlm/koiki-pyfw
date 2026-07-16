# Task 1-1: notification and production log cleanup

## 目的

ユーザー操作の成功・失敗が表示されない通知不具合を解消し、本番コードに残っている不要な console 出力を整理する。

## 事前条件

- Task 0-1 の責務境界が確定している

## 対象

- `frontend/src/components/ui/sonner.tsx`
- `frontend/src/stores/ui-store.ts`
- `frontend/src/components/auth/*.tsx`
- `frontend/src/components/tasks/*.tsx`
- `frontend/src/components/layout/dashboard-layout.tsx`
- その他 `addNotification` / `console.log` 使用箇所

## 実施手順

1. `rg "addNotification|toast\\(|console\\.log|console\\.error" frontend/src` で現状を確認する
2. 通知方針を次のどちらかに決める
   - `sonner` の `toast()` に一本化し、Zustand の `notifications` を削除する
   - `addNotification()` を通知 facade とし、内部で `toast()` を呼ぶ
3. login / register / task create / edit / delete / toggle の通知が表示されるように修正する
4. 本番に出す必要がない console 出力を削除するか `import.meta.env.DEV` ガードへ寄せる
5. 通知の文言が画面言語として不自然でないか確認する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm run build`
- 手動またはテストで login 失敗、task 作成成功、task 更新失敗の通知を確認する

## 完了条件

- `addNotification` 呼び出しが表示に接続されている、または `toast()` へ置換されている
- 本番向けでない logout debug log が残っていない
- 通知実装の責務が UI store と sonner の間で曖昧になっていない

## 実施結果

完了。

- 通知方針は、既存の `addNotification()` を通知 facade として維持し、内部で `sonner` の `toast.success/error/warning/info()` を呼ぶ形にした。
- `frontend/src/stores/ui-store.ts` で通知履歴を既存どおり保持しつつ、同じ `id` / `duration` で toast 表示へ接続した。
- login / register / task create / edit / delete / toggle の既存 `addNotification()` 呼び出しは、呼び出し側を変えずに表示へ接続される。
- `frontend/src/components/layout/dashboard-layout.tsx` の logout debug `console.log` / `console.error` を削除した。logout API が失敗した場合も既存方針どおり login 画面へ遷移する。

検証結果:

- `rg "addNotification|toast\\(|console\\.log|console\\.error" frontend/src` で `dashboard-layout.tsx` の logout debug log 削除を確認した。残存 console は dev guard 付きログ、storage / callback 失敗ログ、または後続タスク対象の API client dev log。
- `npm run check-types`: 成功
- `npm run lint`: 成功。ただし Task 3-1 前なので ESLint は実効ルール未整備
- `npm run build`: 通常権限で成功。initial JS chunk size warning は継続し、Task 2-2 の lazy loading で扱う

後続確認:

- backend / frontend コンテナ起動後の UI 操作で toast 表示を確認済み。
