import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie, clearAuthCookies, COOKIE_CONFIG } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    if (process.env.NODE_ENV === 'development') {
      console.log('[AUTH][refresh] start');
    }

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[AUTH][refresh] CSRF validation failed');
      }
      return createCSRFErrorResponse();
    }

    const refreshToken = request.cookies.get(COOKIE_CONFIG.REFRESH_TOKEN.name)?.value;

    if (!refreshToken) {
      return NextResponse.json(
        { message: 'Refresh token not found', detail: 'Please login again' },
        { status: 401 }
      );
    }

    // バックエンドAPIへプロキシ
    const response = await fetch(`${getBackendApiUrl()}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      let payload: unknown;
      try { payload = await response.json(); } catch { payload = { message: 'Refresh failed' } as const; }
      // リフレッシュ失敗時はCookieをクリア
      const nextResponse = NextResponse.json(payload as Record<string, unknown>, { status: response.status });
      clearAuthCookies(nextResponse);

      return nextResponse;
    }

    const data = await response.json();

    // レスポンスを作成
    const nextResponse = NextResponse.json({ message: 'Token refreshed' });

    // 新しいトークンでCookieを更新
    if (data.access_token) {
      setAccessTokenCookie(nextResponse, data.access_token);
    }

    if (data.refresh_token) {
      setRefreshTokenCookie(nextResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを生成・設定
    const newCSRFToken = generateCSRFToken();
    setCSRFTokenCookie(nextResponse, newCSRFToken);

    return nextResponse;
  } catch {
    console.error('[AUTH][refresh] error');
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Token refresh failed' },
      { status: 500 }
    );
  }
}
