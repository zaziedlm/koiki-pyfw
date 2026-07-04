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
2. login response body から token value を返すかどうかを Task 0-2 の contract に合わせる
3. 既存 rate limit、LoginSecurityService、security logging、security metrics を維持する
4. register 成功時の Cookie 発行要否を contract に合わせる
5. refresh token を request body から読むか Cookie から読むかを contract に合わせる
6. refresh 成功時に token rotation と Cookie 更新を行う
7. refresh response body から token value を返すかどうかを Task 0-2 の contract に合わせる
8. refresh 失敗時に auth Cookie を clear する
9. logout 時に backend token 失効と Cookie clear を行う
   - この挙動は現状 parity ではなく強化であるため、失効範囲を contract に合わせる
10. `me` が Cookie 認証で current user を返せるようにする
11. CSRF bootstrap endpoint を追加または既存 endpoint と統合する
12. Users API authorization parity が必要な場合、backend 側 endpoint / dependency に反映する

## 検証

- login 成功時に auth Cookie が設定される
- refresh 成功時に Cookie が更新される
- refresh 失敗時に Cookie が clear される
- logout 後に `me` が 401 になる
- token value を SPA 向け response body に返さない contract の場合、そのことがテストで確認できる
- 既存 Bearer client 向け contract を維持する場合、その互換性がテストで確認できる
- login security / rate limit / security logging が維持されている
- Users API の権限が BFF 削除で緩んでいない

## 完了条件

- password auth flow が Next.js route handler なしで成立する
- refresh / logout / register の新規挙動と parity 挙動が区別されている

## 実施結果

未実施。
