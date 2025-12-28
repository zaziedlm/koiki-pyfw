import { NextResponse } from 'next/server';
import { config } from './config';

// Cookie設定の定数
export const COOKIE_CONFIG = {
  ACCESS_TOKEN: {
    name: config.auth.tokenKey,
    maxAge: 30 * 60, // 30分
  },
  REFRESH_TOKEN: {
    name: config.auth.refreshTokenKey,
    maxAge: 7 * 24 * 60 * 60, // 7日
  },
} as const;

// 共通のCookie設定オプション
export const getSecureCookieOptions = (maxAge: number) => ({
  httpOnly: true,
  secure: config.auth.cookieAuth.secure,
  sameSite: config.auth.cookieAuth.sameSite,
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
