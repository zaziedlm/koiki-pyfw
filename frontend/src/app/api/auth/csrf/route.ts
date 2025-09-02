import { NextResponse } from 'next/server';
import { randomBytes } from 'crypto';

// Node.js runtime を使用してセキュアな CSRF トークンを生成
export const runtime = 'nodejs';

// CSRF トークン設定
const CSRF_CONFIG = {
  COOKIE_NAME: 'koiki_csrf_token',
  TOKEN_LENGTH: 32,
  MAX_AGE: 24 * 60 * 60, // 24時間
} as const;

// セキュアな CSRF トークン生成（Node.js crypto 使用）
function generateSecureCSRFToken(): string {
  return randomBytes(CSRF_CONFIG.TOKEN_LENGTH).toString('hex');
}

// CSRF トークンをCookieに設定
function setCSRFTokenCookie(response: NextResponse, token: string) {
  response.cookies.set(CSRF_CONFIG.COOKIE_NAME, token, {
    httpOnly: false, // JavaScriptから読み取り可能にする
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: CSRF_CONFIG.MAX_AGE,
    path: '/',
  });
}

export async function GET() {
  const token = generateSecureCSRFToken();
  const response = NextResponse.json({
    message: 'CSRF token generated',
    csrf_token: token,
  });

  setCSRFTokenCookie(response, token);
  return response;
}