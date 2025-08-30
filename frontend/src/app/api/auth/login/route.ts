import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse, setCSRFTokenCookie, generateCSRFToken } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    console.log('=== Login Route Handler ===');
    console.log('Request headers:', Object.fromEntries(request.headers.entries()));
    console.log('Request cookies:', request.cookies.getAll());
    
    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      console.log('CSRF token validation failed');
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
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    console.log('Backend response data:', data);
    
    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Login successful',
      user: data.user,
    });

    // httpOnly Cookieとしてトークンを設定
    if (data.access_token) {
      console.log('Setting access token cookie');
      setAccessTokenCookie(nextResponse, data.access_token);
    } else {
      console.log('No access token in response');
    }

    if (data.refresh_token) {
      console.log('Setting refresh token cookie');
      setRefreshTokenCookie(nextResponse, data.refresh_token);
    } else {
      console.log('No refresh token in response');
    }

    // 新しいCSRFトークンを生成・設定
    const newCSRFToken = generateCSRFToken();
    console.log('Setting new CSRF token');
    setCSRFTokenCookie(nextResponse, newCSRFToken);

    console.log('Login route handler completed successfully');
    
    // JSONレスポンスでリダイレクト情報を含める（fetchエラー回避）
    const finalResponse = NextResponse.json({
      message: 'Login successful',
      redirected: true,
      location: '/dashboard',
      user: data.user,
      access_token: data.access_token,
      new_cookie_set: true, // Cookie設定完了フラグ
      backend_response: {
        access_token_length: data.access_token?.length || 0,
        user_id: data.user?.id,
        timestamp: new Date().toISOString()
      }
    });
    
    // finalResponseにCookieを設定（詳細ログ付き）
    if (data.access_token) {
      console.log('=== Setting Access Token Cookie ===');
      console.log('Token length:', data.access_token.length);
      console.log('Token preview:', data.access_token.substring(0, 20) + '...');
      console.log('Cookie name: koiki_access_token');
      console.log('Cookie options:', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 30 * 60,
        path: '/'
      });
      
      setAccessTokenCookie(finalResponse, data.access_token);
      console.log('Access token cookie set successfully');
    } else {
      console.error('No access token received from backend');
    }

    if (data.refresh_token) {
      console.log('Setting refresh token cookie');
      setRefreshTokenCookie(finalResponse, data.refresh_token);
    }

    // 新しいCSRFトークンを設定
    const finalCSRFToken = generateCSRFToken();
    setCSRFTokenCookie(finalResponse, finalCSRFToken);
    
    console.log('=== Final Response Headers ===');
    finalResponse.headers.forEach((value, key) => {
      if (key.toLowerCase().includes('cookie') || key.toLowerCase().includes('set-cookie')) {
        console.log(`Header ${key}:`, value);
      }
    });
    
    return finalResponse;
  } catch (error) {
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Login proxy failed' },
      { status: 500 }
    );
  }
}
