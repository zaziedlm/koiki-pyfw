import { NextRequest, NextResponse } from 'next/server';

// CSRF トークン設定
export const CSRF_CONFIG = {
  COOKIE_NAME: 'koiki_csrf_token',
  HEADER_NAME: 'x-csrf-token',
  TOKEN_LENGTH: 32,
  MAX_AGE: 24 * 60 * 60, // 24時間
} as const;

// CSRF トークンを生成（Edge Runtime 対応）
export function generateCSRFToken(): string {
  // Edge Runtime では Web Crypto API を使用
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const array = new Uint8Array(CSRF_CONFIG.TOKEN_LENGTH);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  // フォールバック: Math.random を使用（セキュリティは劣るが動作する）
  const chars = '0123456789abcdef';
  let result = '';
  for (let i = 0; i < CSRF_CONFIG.TOKEN_LENGTH * 2; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
}


// CSRF トークンを検証
export function validateCSRFToken(request: NextRequest): boolean {
  // GETリクエストはCSRF検証をスキップ
  if (request.method === 'GET') {
    return true;
  }

  const cookieToken = request.cookies.get(CSRF_CONFIG.COOKIE_NAME)?.value;
  const headerToken = request.headers.get(CSRF_CONFIG.HEADER_NAME);

  // 両方のトークンが存在し、一致することを確認
  return !!(cookieToken && headerToken && cookieToken === headerToken);
}

// CSRF エラーレスポンス
export function createCSRFErrorResponse(): NextResponse {
  return NextResponse.json(
    {
      message: 'CSRF token validation failed',
      detail: 'Invalid or missing CSRF token',
      code: 'CSRF_TOKEN_INVALID',
    },
    { status: 403 }
  );
}

// CSRF トークンをCookieに設定（API Routes用のヘルパー）
// 注意: この関数は Edge Runtime では動作しません。Node.js runtime でのみ使用してください。
export function setCSRFTokenCookie(response: NextResponse, token: string) {
  response.cookies.set(CSRF_CONFIG.COOKIE_NAME, token, {
    httpOnly: false, // JavaScriptから読み取り可能にする
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: CSRF_CONFIG.MAX_AGE,
    path: '/',
  });
}

