# React SPA 移行完了記録

最終更新: 2026-07-10

## 結論

参照フロントエンドの Next.js 15 / App Router / BFF 構成から、Vite + React SPA 構成への移行と、その後の refresh は完了した。

ブラウザは FastAPI の session auth contract を直接利用する。Cookie 発行、token refresh、logout、CSRF 検証、SSO token exchange、SAML ticket exchange は backend が所有し、frontend は token を browser storage に保存しない。

本書はリリース番号を定義する文書ではない。移行の完了状態、正本ドキュメント、後続の判断事項を記録する。

## 完了した範囲

- frontend を Vite + React + TypeScript SPA として構成し、React Router で browser routing を担う形へ移行した。
- Next.js runtime、Route Handler、BFF、`NEXT_PUBLIC_*` runtime contract を削除した。
- FastAPI の `/api/v1/auth/session/*` を browser session contract とし、httpOnly Cookie と署名付き・TTL 付き CSRF token を backend が管理する形へ移行した。
- SPA 用 API transport、feature API、TanStack Query の query/mutation、route-level lazy loading を整理した。
- Vitest、Testing Library、MSW による最小テスト基盤を追加した。
- Vite static build を非特権 nginx で配信し、SPA fallback、healthcheck、基本 security headers と CSP を設定した。
- frontend の Vite build-time env と backend-owned security settings の境界を整理した。
- Dev Container の frontend 参照を Vite React SPA に更新した。

## 現行の正本

| 対象 | 正本 |
|---|---|
| SPA 実装規約 | `docs/frontend-spa-implementation-guide.ja.md` |
| 認証 API と browser session contract | `docs/authentication-api-guide.md` |
| frontend / backend の環境ファイル | `docs/dev/env-files.md` |
| 実装・検証コマンド | `frontend/README.md` |
| CI 採用方針と production 配備ゲート | `docs/dev/react-spa-adoption-release-gates.ja.md` |

Next.js BFF 時代の guide と audit は、完全に廃止され参照者がいなくなったため、v0.8 で `docs/archive/frontend-nextjs-bff/` ごと削除済み。

## 代表的な検証済み事項

- `npm run check-types`
- `npm run lint`
- `npm test`（4 files / 8 tests）
- `npm run build`
- backend 起動込みの login、Todo 作成・更新・削除、logout の手動確認

検証の詳細と実行時点の制約は `docs/dev/frontend-refactor-refresh-tasks/task-4-1.md` を参照する。

## 明示的に後続へ残す事項

| 項目 | 状態 | 着手条件 |
|---|---|---|
| frontend CI の有効化 | 採用方針を定義済み | `dev/v0.8` 以降で SPA を採用対象にするとき |
| Browser E2E | 未導入 | UI flow が安定し、login → Todo CRUD → logout を継続保証するとき |
| `react-refresh/only-export-components` warning | 任意 cleanup | CI ログを warning-free にする必要があるとき |
| SSO / SAML の実 IdP happy path 再確認 | リリース／配備ゲート | IdP と production callback URI が確定したとき |
| 本番 secret・環境 metadata の確認 | リリース／配備ゲート | AWS / production deployment 前 |

セッション認証の中長期強化（access-token denylist、CSRF の session binding / `__Host-` Cookie、Redis 分散 rate limit と proxy IP 方針）は、`docs/security/session-auth-security-review-followup.ja.md` に受容条件と再検討条件を記録している。

CI 採用方針と production 配備時の確認項目は、`docs/dev/react-spa-adoption-release-gates.ja.md` を正本とする。

## 関連する履歴計画

- `docs/dev/v0.7-frontend-spa-migration/`
- `docs/dev/frontend-refactor-refresh-plan.ja.md`
- `docs/dev/frontend-refactor-refresh-tasks/`

これらは実施経緯を示す。新しい frontend 実装の判断には、本書と「現行の正本」を優先する。
