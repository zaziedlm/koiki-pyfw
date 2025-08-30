import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie, clearAuthCookies, COOKIE_CONFIG } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    console.log('=== Refresh Route Handler ===');
    console.log('Request headers:', Object.fromEntries(request.headers.entries()));
    console.log('Request cookies:', request.cookies.getAll());
    
    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      console.log('CSRF token validation failed');
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
      const errorData = await response.json();
      
      // リフレッシュ失敗時はCookieをクリア
      const nextResponse = NextResponse.json(errorData, { status: response.status });
      clearAuthCookies(nextResponse);
      
      return nextResponse;
    }

    const data = await response.json();
    console.log('Backend response data:', data);
    
    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Token refreshed',
      access_token: data.access_token, // フロントエンドが必要とする場合のため
    });

    // 新しいトークンでCookieを更新
    if (data.access_token) {
      console.log('Setting new access token cookie');
      setAccessTokenCookie(nextResponse, data.access_token);
    }

    if (data.refresh_token) {
      console.log('Setting new refresh token cookie');
      setRefreshTokenCookie(nextResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを生成・設定
    const newCSRFToken = generateCSRFToken();
    console.log('Setting new CSRF token');
    setCSRFTokenCookie(nextResponse, newCSRFToken);

    console.log('Refresh route handler completed successfully');
    return nextResponse;
  } catch (error) {
    console.error('Refresh proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Token refresh failed' },
      { status: 500 }
    );
  }
}
