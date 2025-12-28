import { NextRequest, NextResponse } from 'next/server';
import { randomBytes } from 'node:crypto';
import { config } from './config';

// CSRF トークン設定
export const CSRF_CONFIG = {
  COOKIE_NAME: 'koiki_csrf_token',
  HEADER_NAME: 'x-csrf-token',
  TOKEN_LENGTH: 32,
  MAX_AGE: 24 * 60 * 60, // 24時間
} as const;

/**
 * CSRF トークンを生成（Node.js ランタイム／Math.randomは不使用）
 */
export function generateCSRFToken(): string {
  // Web Crypto API（Node 18+）を優先。未対応の場合は node:crypto.randomBytes を使用
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(CSRF_CONFIG.TOKEN_LENGTH);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  }

  // Node.js フォールバック（ESM import 済み）
  return randomBytes(CSRF_CONFIG.TOKEN_LENGTH).toString('hex');
}

// CSRF トークンを検証
export function validateCSRFToken(request: NextRequest): boolean {
  // GETリクエストはCSRF検証をスキップ
  if (request.method === 'GET') {
    return true;
  }

  const cookieToken = request.cookies.get(CSRF_CONFIG.COOKIE_NAME)?.value;
  const headerToken = request.headers.get(CSRF_CONFIG.HEADER_NAME);

  // デバッグ用ログ (開発環境またはエラー時)
  const isValid = !!(cookieToken && headerToken && cookieToken === headerToken);

  if (!isValid && process.env.NODE_ENV !== 'production') {
    console.warn('[CSRF Validation Failed]', {
      url: request.url,
      method: request.method,
      hasCookie: !!cookieToken,
      hasHeader: !!headerToken,
      match: cookieToken === headerToken,
      cookieSample: cookieToken ? `${cookieToken.substring(0, 4)}...` : 'null',
      headerSample: headerToken ? `${headerToken.substring(0, 4)}...` : 'null'
    });
  }

  // 両方のトークンが存在し、一致することを確認
  return isValid;
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
// 注意: この関数は Node.js runtime でのみ使用してください。
export function setCSRFTokenCookie(response: NextResponse, token: string) {
  response.cookies.set(CSRF_CONFIG.COOKIE_NAME, token, {
    httpOnly: false, // JavaScriptから読み取り可能にする
    secure: config.auth.cookieAuth.secure,
    sameSite: config.auth.cookieAuth.sameSite,
    maxAge: CSRF_CONFIG.MAX_AGE,
    path: '/',
  });
}
