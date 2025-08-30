import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const refreshToken = request.cookies.get('koiki_refresh_token')?.value;
    
    if (!refreshToken) {
      return NextResponse.json(
        { message: 'Refresh token not found', detail: 'Please login again' },
        { status: 401 }
      );
    }

    // バックエンドAPIへプロキシ
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';
    
    const response = await fetch(`${backendUrl}${apiPrefix}/auth/refresh`, {
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
      nextResponse.cookies.set('koiki_access_token', '', { maxAge: 0, path: '/' });
      nextResponse.cookies.set('koiki_refresh_token', '', { maxAge: 0, path: '/' });
      
      return nextResponse;
    }

    const data = await response.json();
    
    // レスポンスを作成
    const nextResponse = NextResponse.json({
      message: 'Token refreshed',
      access_token: data.access_token, // フロントエンドが必要とする場合のため
    });

    // 新しいトークンでCookieを更新
    if (data.access_token) {
      nextResponse.cookies.set('koiki_access_token', data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 30 * 60, // 30分
        path: '/',
      });
    }

    if (data.refresh_token) {
      nextResponse.cookies.set('koiki_refresh_token', data.refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 7 * 24 * 60 * 60, // 7日
        path: '/',
      });
    }

    return nextResponse;
  } catch (error) {
    console.error('Refresh proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Token refresh failed' },
      { status: 500 }
    );
  }
}