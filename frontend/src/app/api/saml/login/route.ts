import { NextRequest, NextResponse } from 'next/server';

const rawBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL
  || `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`;
const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { login_ticket } = body;

    if (!login_ticket) {
      return NextResponse.json(
        { detail: 'login_ticket is required' },
        { status: 400 }
      );
    }

    // Forward request to backend SAML login endpoint
    const backendUrl = `${API_BASE_URL}/auth/saml/login`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward cookies if any
        ...(request.headers.get('cookie') ? { Cookie: request.headers.get('cookie')! } : {}),
      },
      body: JSON.stringify({ login_ticket }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'SAML login failed' }));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();

    // Create response with success data
    const nextResponse = NextResponse.json({
      ...data,
      location: '/dashboard', // Redirect to dashboard after successful login
    });

    // Set authentication cookies (similar to OIDC flow)
    if (data.access_token) {
      nextResponse.cookies.set('koiki_access_token', data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: data.expires_in || 3600, // Use expires_in from response or default 1 hour
        path: '/',
      });
    }

    if (data.refresh_token) {
      nextResponse.cookies.set('koiki_refresh_token', data.refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      });
    }

    // Forward any Set-Cookie headers from backend
    const setCookieHeaders = response.headers.get('set-cookie');
    if (setCookieHeaders) {
      nextResponse.headers.append('set-cookie', setCookieHeaders);
    }

    return nextResponse;
  } catch (error) {
    console.error('[SAML Login] Error:', error);
    return NextResponse.json(
      { detail: 'Internal server error during SAML login' },
      { status: 500 }
    );
  }
}
