import { NextRequest, NextResponse } from 'next/server';
import { getBackendApiUrl } from '@/lib/cookie-utils';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = new URL(`${getBackendApiUrl()}/auth/sso/authorization`);
    const redirectUri = request.nextUrl.searchParams.get('redirect_uri');
    if (redirectUri) {
      backendUrl.searchParams.set('redirect_uri', redirectUri);
    }

    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        cookie: request.headers.get('cookie') ?? '',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      return NextResponse.json(payload, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('[SSO][authorization] proxy error', error);
    return NextResponse.json(
      { detail: 'Failed to initialize SSO authorization' },
      { status: 500 }
    );
  }
}

