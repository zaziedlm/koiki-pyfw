import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl, setAccessTokenCookie, setRefreshTokenCookie } from '@/lib/cookie-utils';
import {
  validateCSRFToken,
  createCSRFErrorResponse,
  generateCSRFToken,
  setCSRFTokenCookie,
} from '@/lib/csrf-utils';

export async function POST(request: NextRequest) {
  try {
    if (!validateCSRFToken(request)) {
      return createCSRFErrorResponse();
    }

    const payload = await request.json();

    const backendResponse = await fetch(`${getBackendApiUrl()}/auth/sso/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!backendResponse.ok) {
      const errorPayload = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(errorPayload, { status: backendResponse.status });
    }

    const tokenData: {
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
    } = await backendResponse.json();

    let user: unknown = null;

    try {
      const meResponse = await fetch(`${getBackendApiUrl()}/auth/me`, {
        headers: {
          Authorization: `Bearer ${tokenData.access_token}`,
        },
      });
      if (meResponse.ok) {
        user = await meResponse.json();
      }
    } catch (error) {
      console.error('[SSO][login] failed to fetch user profile', error);
    }

    const body = {
      message: 'SSO login successful',
      redirected: true,
      location: '/dashboard',
      user,
      new_cookie_set: true,
    };

    const nextResponse = NextResponse.json(body);

    if (tokenData.access_token) {
      setAccessTokenCookie(nextResponse, tokenData.access_token);
    }

    if (tokenData.refresh_token) {
      setRefreshTokenCookie(nextResponse, tokenData.refresh_token);
    }

    const newCsrfToken = generateCSRFToken();
    setCSRFTokenCookie(nextResponse, newCsrfToken);

    return nextResponse;
  } catch (error) {
    console.error('[SSO][login] proxy error', error);
    return NextResponse.json(
      { detail: 'Failed to complete SSO login' },
      { status: 500 }
    );
  }
}

