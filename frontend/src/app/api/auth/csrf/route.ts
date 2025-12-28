import { NextResponse } from 'next/server';
import { generateCSRFToken, setCSRFTokenCookie } from '@/lib/csrf-utils';

// Node.js runtime を使用してセキュアな CSRF トークンを生成
export const runtime = 'nodejs';

export async function GET() {
  const token = generateCSRFToken();
  const response = NextResponse.json({
    message: 'CSRF token generated',
    csrf_token: token,
  });

  setCSRFTokenCookie(response, token);
  return response;
}