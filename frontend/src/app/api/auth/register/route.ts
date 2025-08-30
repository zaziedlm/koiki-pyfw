import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    console.log('=== Register Route Handler ===');
    console.log('Request headers:', Object.fromEntries(request.headers.entries()));
    console.log('Request cookies:', request.cookies.getAll());
    
    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      console.log('CSRF token validation failed');
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
    console.log('Backend response data:', data);
    
    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Registration successful',
      user: data.user,
    });

    // 登録成功時にもトークンが返される場合はCookieに設定
    if (data.access_token) {
      console.log('Setting access token cookie');
      setAccessTokenCookie(nextResponse, data.access_token);
    }

    if (data.refresh_token) {
      console.log('Setting refresh token cookie');
      setRefreshTokenCookie(nextResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを生成・設定
    const newCSRFToken = generateCSRFToken();
    console.log('Setting new CSRF token');
    setCSRFTokenCookie(nextResponse, newCSRFToken);

    console.log('Register route handler completed successfully');
    return nextResponse;
  } catch (error) {
    console.error('Register proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Registration failed' },
      { status: 500 }
    );
  }
}
