import { NextResponse } from 'next/server';

// Cookie設定の定数
export const COOKIE_CONFIG = {
  ACCESS_TOKEN: {
    name: process.env.NEXT_PUBLIC_ACCESS_TOKEN_NAME || 'koiki_access_token',
    maxAge: 30 * 60, // 30分
  },
  REFRESH_TOKEN: {
    name: process.env.NEXT_PUBLIC_REFRESH_TOKEN_NAME || 'koiki_refresh_token',
    maxAge: 7 * 24 * 60 * 60, // 7日
  },
} as const;

// 共通のCookie設定オプション
export const getSecureCookieOptions = (maxAge: number) => ({
  httpOnly: true,
  secure: process.env.NEXT_PUBLIC_COOKIE_SECURE === 'true' || process.env.NODE_ENV === 'production',
  sameSite: (process.env.NEXT_PUBLIC_COOKIE_SAMESITE as 'lax' | 'strict' | 'none') || 'lax',
  maxAge,
  path: '/',
});

// アクセストークンをCookieに設定
export function setAccessTokenCookie(response: NextResponse, token: string) {
  response.cookies.set(
    COOKIE_CONFIG.ACCESS_TOKEN.name,
    token,
    getSecureCookieOptions(COOKIE_CONFIG.ACCESS_TOKEN.maxAge)
  );
}

// リフレッシュトークンをCookieに設定
export function setRefreshTokenCookie(response: NextResponse, token: string) {
  response.cookies.set(
    COOKIE_CONFIG.REFRESH_TOKEN.name,
    token,
    getSecureCookieOptions(COOKIE_CONFIG.REFRESH_TOKEN.maxAge)
  );
}

// 認証Cookieをクリア
export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(COOKIE_CONFIG.ACCESS_TOKEN.name, '', {
    ...getSecureCookieOptions(0),
    maxAge: 0,
  });
  
  response.cookies.set(COOKIE_CONFIG.REFRESH_TOKEN.name, '', {
    ...getSecureCookieOptions(0),
    maxAge: 0,
  });
}

// バックエンドAPI URLを取得
export function getBackendApiUrl(): string {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';
  return `${backendUrl}${apiPrefix}`;
}
