# KOIKI Frontend 実装精査レポートと Next.js 15 開発ガイド（ドラフト）

最終更新: 2025-08-30

## 目的
- 現行 frontend 実装（Next.js 15 / React 19）の健全性を評価し、改善点を提示
- 今後同様機能を追加する際に参照可能な、開発標準と実装パターンを提供

---

## 1. 調査サマリ

### 1.1 技術スタック/設定
- Next.js 15.4 / React 19 / App Router / Tailwind v4 構成は妥当
- Turbopack 対応、Docker 向け `output: 'standalone'` は適切
- 懸念:
  - `next.config.ts` にて `eslint.ignoreDuringBuilds` と `typescript.ignoreBuildErrors` が true（本番無効化は非推奨）
  - `rewrites` で `/api/backend/:path*` を用意しているが、axios/fetch が直接 `http://localhost:8000` を参照する箇所があり不統一

### 1.2 App Router/レイアウト
- `src/app/layout.tsx` で Providers 集約、`metadata` 設定も妥当
- ページが `use client` 前提の箇所が散見（必要最小限へ）

### 1.3 認証/middleware
- middleware: Cookie の `koiki_access_token` を参照しガード
- フロント: localStorage にトークン保存（`tokenStorage`）
- 上記不一致により、保護ルート判定が不安定/脆弱になり得る
- 推奨: 認証を httpOnly Cookie に統一し、Route Handlers 経由で発行/更新/破棄

### 1.4 API クライアント/データ取得
- axios + React Query 構成は妥当
- 懸念:
  - `src/lib/api-client.ts` の interceptor 引数 `config` が import 変数 `config` と衝突（`config.api.baseUrl` 参照で不具合の恐れ）
  - React Query の retry 判定で `unknown` な error に `error?.response` を参照（型的に不正）
  - baseURL がリライト不使用（CORS/環境差分吸収の観点で `/api/backend` 統一推奨）
  - React Query Devtools が常時描画（production では非表示推奨）

### 1.5 状態管理
- サーバ同期データ（todos/users）を React Query と Zustand の両方で保持し二重管理傾向
- 推奨: サーバ同期は React Query に集約、Zustand は UI/短命ローカル state のみに限定

### 1.6 スタイル
- Tailwind v4 の inline theme は妥当
- テーマ切替は `next-themes` を使うと実装が簡潔（任意）

---

## 2. 主要改善提案（優先順）

### P1: 型/静的解析を本番で有効化
- `next.config.ts`:
  - `eslint.ignoreDuringBuilds: false`
  - `typescript.ignoreBuildErrors: false`
- CI で `next lint` / `tsc --noEmit` を必須化

### P1: 認証を Cookie ベースに統一（httpOnly/Secure/SameSite）
- ログイン/リフレッシュ/ログアウトを Next の Route Handlers で backend へプロキシ
- backend の発行トークンを httpOnly Cookie としてクライアントへ付与
- フロントの localStorage 保存は撤廃
- middleware は Cookie の存在/有効性でリダイレクト制御
- CSRF 対策: SameSite=Lax/Strict + ダブルサブミットトークン等

### P1: axios クライアントのバグ修正・標準化
- 変数衝突回避（import 側を `appConfig` などへリネーム）
- refresh リクエストは `appConfig.api.baseUrl` を参照
- `withCredentials: true`（Cookie 認証時）
- baseURL は `/api/backend/api/v1` へ統一（rewrites を活用）

例（抜粋・概念コード）:
```ts
// TypeScript
// src/lib/api-client.ts
import axios, { isAxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { config as appConfig } from './config';

const client: AxiosInstance = axios.create({
  baseURL: '/api/backend/api/v1',
  timeout: 10000,
  withCredentials: true, // Cookie 認証時は必須
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((reqConfig) => {
  // Cookie モードでは Authorization ヘッダは不要（必要なら付与）
  return reqConfig;
});

let refreshPromise: Promise<void> | null = null;
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (isAxiosError(error) && error.response?.status === 401 && !original._retry) {
      original._retry = true;
      refreshPromise ??= axios
        .post(`${appConfig.api.baseUrl}/auth/refresh`, {}, { withCredentials: true })
        .then(() => { /* Cookie 更新 */ })
        .finally(() => { refreshPromise = null; });

      await refreshPromise;
      return client(original);
    }
    throw error;
  }
);
```

### P2: React Query のエラー型分岐と Devtools 制御
```ts
// TypeScript
// retry の型分岐
import { isAxiosError } from 'axios';

retry: (failureCount, error: unknown) => {
  if (isAxiosError(error)) {
    const s = error.response?.status;
    if (s && s >= 400 && s < 500 && s !== 429) return false;
  }
  return failureCount < 3;
}
```
```tsx
// TypeScript
// Devtools は開発時のみ
{process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
```

### P2: ルーティング/クライアント化の最小化
- ページは原則 RSC（'use client' 削減）
- 認証判定は middleware（サーバ側）を一次、クライアントは UX 補助

### P3: 状態管理の一本化
- `use-todo-queries` / `use-user-queries` を唯一のサーバ同期手段に
- `stores/todo-store.ts` / `stores/user-store.ts` の取得/同期責務は段階的に撤去
- Zustand は UI 状態（モーダル、通知、テーマ）に限定

---

## 3. 実装パターン/テンプレート

### 3.1 セキュアな取得パターン（Cookie 認証）
```ts
// TypeScript
import { useQuery } from '@tanstack/react-query';

export function useSecureResource(id: number) {
  return useQuery({
    queryKey: ['resource', 'detail', id],
    queryFn: async () => {
      const res = await fetch(`/api/backend/api/v1/resources/${id}`, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to fetch');
      return res.json();
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}
```

### 3.2 Route Handlers 経由の認証（概念）
```ts
// TypeScript
// src/app/api/auth/login/route.ts
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const body = await req.json();
  const be = await fetch(process.env.API_URL + '/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!be.ok) return NextResponse.json(await be.json(), { status: be.status });

  // backend から Set-Cookie を委譲するか、ここで Cookie を再設定（httpOnly, Secure, SameSite）
  const res = NextResponse.json({ ok: true });
  // res.cookies.set('koiki_access_token', token, { httpOnly: true, secure: true, sameSite: 'lax', path: '/' });
  return res;
}
```

### 3.3 React Query: list/detail/mutation の標準
- list: `staleTime` 30–60s、フィルタは `queryKey` に含める
- detail: 書き込み後 `setQueryData` で即時反映 + list invalidate

---

## 4. ディレクトリ/命名指針
- `app`: ルーティング（RSC デフォルト）
- `components`: 再利用 UI（副作用なしを基本）
- `hooks`: React Query hooks（サーバ同期はここに集約）
- `lib`: api-client/config/utils
- `stores`: UI ローカル状態（Zustand）。サーバ同期は持たない
- `types`: API DTO/型定義

---

## 5. 環境変数/rewrites 指針
- `.env.local` 例
```bash
# .env.local
NEXT_PUBLIC_APP_NAME=KOIKI Task Manager
NEXT_PUBLIC_APP_VERSION=1.0.0
API_URL=http://localhost:8000
```
- `next.config.ts` の rewrites を活用し、フロントからは常に `/api/backend/...` を叩く
- axios/fetch の baseURL も `/api/backend/api/v1` に統一

---

## 6. 品質/セキュリティ標準
- ESLint/TS は本番でも有効
- 依存監査（npm audit, renovate）
- Cookie 認証 + CSRF 対策
- エラーログ/監視（サーバ・クライアント）

---

## 7. 導入手順（推奨順）
1. `next.config.ts` の静的解析無効化を撤回し、Lint/TS エラー解消
2. `api-client` の変数衝突修正、`isAxiosError` 導入、Devtools 制御
3. Cookie 認証へ移行（Route Handlers、axios `withCredentials`、middleware での判定整理）
4. React Query へサーバ同期を集約（Zustand のサーバ同期責務を段階的に削除）
5. rewrites/baseURL/環境変数の統一、README/このガイドの更新

---

## 8. チェックリスト
- [ ] Lint/TS を本番有効化
- [ ] axios baseURL を `/api/backend/api/v1` に統一
- [ ] 認証を httpOnly Cookie 化
- [ ] React Query のエラー型分岐導入
- [ ] Devtools を dev のみ表示
- [ ] サーバ同期は React Query に一本化
- [ ] RSC をデフォルト（'use client' 最小化）
- [ ] .env / rewrites / README の整備

---

保存場所: `docs/dev/frontend-next15-guide.md`
