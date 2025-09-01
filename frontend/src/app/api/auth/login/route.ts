import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    if (process.env.NODE_ENV === 'development') {
      console.log('[AUTH][login] start');
    }

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[AUTH][login] CSRF validation failed');
      }
      return createCSRFErrorResponse();
    }

    const body = await request.json();

    // バックエンドAPIへプロキシ
    const response = await fetch(`${getBackendApiUrl()}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `username=${encodeURIComponent(body.email || body.username)}&password=${encodeURIComponent(body.password)}`,
    });

    if (!response.ok) {
      let payload: unknown;
      try { payload = await response.json(); } catch { payload = { message: 'Login failed' } as const; }
      return NextResponse.json(payload as Record<string, unknown>, { status: response.status });
    }

    const data = await response.json();

    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Login successful',
      user: data.user,
    });

    // httpOnly Cookieとしてトークンを設定
    if (data.access_token) {
      setAccessTokenCookie(nextResponse, data.access_token);
    }

    if (data.refresh_token) {
      setRefreshTokenCookie(nextResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを生成・設定
    const newCSRFToken = generateCSRFToken();
    setCSRFTokenCookie(nextResponse, newCSRFToken);

    console.log('Login route handler completed successfully');

    // JSONレスポンスでリダイレクト情報を含める（fetchエラー回避）
    const finalResponse = NextResponse.json({
      message: 'Login successful',
      redirected: true,
      location: '/dashboard',
      user: data.user,
      new_cookie_set: true,
    });

    // finalResponseにCookieを設定（詳細ログ付き）
    if (data.access_token) {
      setAccessTokenCookie(finalResponse, data.access_token);
    }

    if (data.refresh_token) {
      setRefreshTokenCookie(finalResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを設定
    const finalCSRFToken = generateCSRFToken();
    setCSRFTokenCookie(finalResponse, finalCSRFToken);

    return finalResponse;
  } catch {
    console.error('[AUTH][login] error');
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Login proxy failed' },
      { status: 500 }
    );
  }
}
