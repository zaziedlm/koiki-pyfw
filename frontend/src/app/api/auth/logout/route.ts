import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, clearAuthCookies, COOKIE_CONFIG } from '@/lib/cookie-utils';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    console.log('=== Logout Route Handler ===');
    console.log('Request headers:', Object.fromEntries(request.headers.entries()));
    console.log('Request cookies:', request.cookies.getAll());
    
    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      console.log('CSRF token validation failed');
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
      } catch (error) {
        console.error('Backend logout error:', error);
        // バックエンドエラーでもCookieは削除する
      }
    }

    // レスポンスを作成
    const response = NextResponse.json({ message: 'Logout successful' });

    // Cookieを削除
    clearAuthCookies(response);

    return response;
  } catch (error) {
    console.error('Logout proxy error:', error);
    
    // エラーでもCookieは削除
    const response = NextResponse.json(
      { message: 'Logout completed', detail: 'Some errors occurred but cookies cleared' },
      { status: 200 }
    );

    clearAuthCookies(response);

    return response;
  }
}
