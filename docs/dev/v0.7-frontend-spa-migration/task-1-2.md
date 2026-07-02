# Task 1-2: password auth Cookie endpoints

## 目的

password login、registration、refresh、logout、me を SPA 向け Cookie 認証 contract に対応させる。

## 事前条件

- Task 1-1 が完了している

## 対象

- login
- register
- refresh
- logout
- me
- csrf bootstrap

## 実施手順

1. login 成功時に access / refresh Cookie を発行する
2. register 成功時の Cookie 発行要否を contract に合わせる
3. refresh 成功時に token rotation と Cookie 更新を行う
4. refresh 失敗時に auth Cookie を clear する
5. logout 時に backend token 失効と Cookie clear を行う
6. `me` が Cookie 認証で current user を返せるようにする
7. CSRF bootstrap endpoint を追加または既存 endpoint と統合する

## 検証

- login 成功時に auth Cookie が設定される
- refresh 成功時に Cookie が更新される
- refresh 失敗時に Cookie が clear される
- logout 後に `me` が 401 になる

## 完了条件

- password auth flow が Next.js route handler なしで成立する

## 実施結果

未実施。
