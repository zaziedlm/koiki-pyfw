# Task 2-3: dashboard and navigation data cleanup

## 目的

固定値の dashboard と未実装 route 導線を整理し、業務 UI 基盤として誤解を生まない状態にする。

## 事前条件

- Task 2-1 が完了していることが望ましい
- Task 2-2 が完了していることが望ましい

## 対象

- `frontend/src/app/dashboard/page.tsx` または移動後の dashboard route
- `frontend/src/components/layout/dashboard-layout.tsx`
- task / user API hooks
- navigation 定義

## 実施手順

1. dashboard の固定値が demo として必要か、実データ化するかを判断する
2. demo として残す場合は mock data を明示的に隔離し、業務実装の前例にしない
3. 実データ化する場合は backend API の有無を確認し、ない場合は frontend 側で無理に作らない
4. `/dashboard/profile`, `/dashboard/users`, `/dashboard/security`, `/dashboard/settings` の導線は UI として残すか判断する
5. 未実装 route の導線を残す場合は、404 / root redirect になる現状を許容した意図を記録する
6. task stats は task query から導出するか、専用 endpoint が必要かを判断する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm run build`
- dashboard navigation の未実装 route 導線を残す/消す判断が明確である

## 完了条件

- 実データと mock data の境界が明確である
- navigation に存在する未実装 route の扱いが明確である
- dashboard が業務実装の不正確な前例になっていない

## 実施結果

完了。

- dashboard の固定 task stats / recent task mock data は削除し、`useCookieTodos()` の task query から `total`, `completed`, `pending`, `completionRate`, recently updated tasks を導出する形にした。
- 専用 dashboard stats / users / team API は現状ないため、frontend 側で架空の API や mock data は追加しない判断にした。
- `/dashboard/profile`, `/dashboard/users`, `/dashboard/security`, `/dashboard/settings` の UI 導線は、未実装 route であっても残す方針とした。
- dashboard action も `Create new task`, `View all tasks`, `Team overview` を残し、`Team overview` は従来通り未実装の `/dashboard/users` へ向ける。

検証:

- `npm run check-types`
- `npm run lint`
- `npm run build`

補足:

- sandbox 通常権限の `npm run build` は esbuild 起動時の `spawn EPERM` で失敗した。
- 同じ build を昇格実行し、成功を確認した。
