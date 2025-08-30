import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // バックエンドAPIへプロキシ
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';
    
    const response = await fetch(`${backendUrl}${apiPrefix}/auth/register`, {
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
    console.error('Register proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Registration failed' },
      { status: 500 }
    );
  }
}