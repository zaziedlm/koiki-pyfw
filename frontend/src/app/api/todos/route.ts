import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

// Environment-based logging utility
const isDevelopment = process.env.NODE_ENV === 'development';
const devLog = (msg: string) => { if (isDevelopment) console.log(`[TODOS] ${msg}`); };

export async function GET(request: NextRequest) {
  try {
    devLog('GET start');

    // Get search params
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';

    // Get access token from cookies (no logging of values)
    const accessToken = request.cookies.get('koiki_access_token')?.value;

    if (!accessToken) {
      // Keep security-related logs for audit purposes
      if (isDevelopment) console.warn('[TODOS] GET unauthorized (no token)');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    devLog('Backend request');

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos${queryString}`;
    devLog('Backend request');

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    devLog(`Backend status ${response.status}`);

    if (!response.ok) {
      const errorData = await response.text();
      if (isDevelopment) console.error('[TODOS] GET backend error', { status: response.status });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('GET success');

    return NextResponse.json(data);
  } catch (error) {
    console.error('[TODOS] GET handler error');
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    devLog('POST start');

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      devLog('CSRF validation failed');
      return createCSRFErrorResponse();
    }

    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;

    if (!accessToken) {
      // Keep security-related logs for audit purposes
      if (isDevelopment) console.warn('[TODOS] POST unauthorized (no token)');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();
    // no body logging

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos`;
    devLog('Backend request');

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    devLog(`Backend status ${response.status}`);

    if (!response.ok) {
      const errorData = await response.text();
      if (isDevelopment) console.error('[TODOS] POST backend error', { status: response.status });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('POST success');

    return NextResponse.json(data);
  } catch (error) {
    console.error('[TODOS] POST handler error');
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
