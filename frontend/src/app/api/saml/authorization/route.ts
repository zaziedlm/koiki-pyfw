import { NextRequest, NextResponse } from 'next/server';

const rawBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL
  || `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`;
const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const redirectUri = searchParams.get('redirect_uri');

    if (!redirectUri) {
      return NextResponse.json(
        { detail: 'redirect_uri parameter is required' },
        { status: 400 }
      );
    }

    // Forward request to backend SAML authorization endpoint
    const backendUrl = `${API_BASE_URL}/auth/saml/authorization?redirect_uri=${encodeURIComponent(redirectUri)}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward cookies if any
        ...(request.headers.get('cookie') ? { Cookie: request.headers.get('cookie')! } : {}),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'SAML authorization failed' }));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('[SAML Authorization] Error:', error);
    return NextResponse.json(
      { detail: 'Internal server error during SAML authorization' },
      { status: 500 }
    );
  }
}
