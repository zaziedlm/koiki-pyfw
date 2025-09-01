import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    if (process.env.NODE_ENV === 'development') {
      console.log('[AUTH][register] start');
    }

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[AUTH][register] CSRF validation failed');
      }
      return createCSRFErrorResponse();
    }

    const body = await request.json();

    // バックエンドAPIへプロキシ
    const response = await fetch(`${getBackendApiUrl()}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();

    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Registration successful',
      user: data.user,
    });

    // 登録成功時にもトークンが返される場合はCookieに設定
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
    console.error('[AUTH][register] error');
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Registration failed' },
      { status: 500 }
    );
  }
}
