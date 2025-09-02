import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      return NextResponse.json(
        { message: 'Access token not found', detail: 'Please login' },
        { status: 401 }
      );
    }

    // バックエンドAPIへプロキシ
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiPrefix = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';
    
    const response = await fetch(`${backendUrl}${apiPrefix}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Me proxy error:', error);
    return NextResponse.json(
      { message: 'Internal server error', detail: 'Failed to fetch user info' },
      { status: 500 }
    );
  }
}