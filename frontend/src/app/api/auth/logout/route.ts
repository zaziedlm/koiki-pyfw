import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, clearAuthCookies, COOKIE_CONFIG } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    if (process.env.NODE_ENV === 'development') {
      console.log('[AUTH][logout] start');
    }

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[AUTH][logout] CSRF validation failed');
      }
      return createCSRFErrorResponse();
    }

    const accessToken = request.cookies.get(COOKIE_CONFIG.ACCESS_TOKEN.name)?.value;

    // バックエンドAPIへプロキシ（トークンがある場合）
    if (accessToken) {
      try {
        await fetch(`${getBackendApiUrl()}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });
      } catch {
        // swallow backend error; proceed to clear cookies
        // バックエンドエラーでもCookieは削除する
      }
    }

    // レスポンスを作成
    const response = NextResponse.json({ message: 'Logout successful' });

    // Cookieを削除
    clearAuthCookies(response);

    return response;
  } catch {

    // エラーでもCookieは削除
    const response = NextResponse.json(
      { message: 'Logout completed', detail: 'Some errors occurred but cookies cleared' },
      { status: 200 }
    );

    clearAuthCookies(response);

    return response;
  }
}
