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
4. `/dashboard/profile`, `/dashboard/users`, `/dashboard/security`, `/dashboard/settings` の導線を実装済み route と一致させる
5. 未実装 route は非表示にするか、正式な placeholder route を作る
6. task stats は task query から導出するか、専用 endpoint が必要かを判断する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm run build`
- dashboard navigation の全リンクが 404 / root redirect にならない

## 完了条件

- 実データと mock data の境界が明確である
- navigation に存在する route が実装と一致している
- dashboard が業務実装の不正確な前例になっていない

## 実施結果

未実施。

