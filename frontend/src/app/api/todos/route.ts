import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

// Environment-based logging utility
const isDevelopment = process.env.NODE_ENV === 'development';

function devLog(message: string, data?: unknown) {
  if (isDevelopment) {
    console.log(`[TODOS-API] ${message}`, data || '');
  }
}

export async function GET(request: NextRequest) {
  try {
    devLog('GET request started');
    
    // Get search params
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
    
    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      // Keep security-related logs for audit purposes
      console.warn('Todo GET: Authentication failed - No access token');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    devLog('Making backend request');

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos${queryString}`;
    devLog('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    devLog('Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.text();
      // Keep error logs for troubleshooting
      console.error('Todo GET: Backend request failed', { 
        status: response.status, 
        url: backendUrl,
        error: errorData 
      });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('Success, returning todos count:', data?.length || 0);

    return NextResponse.json(data);
  } catch (error) {
    // Always keep error logs for monitoring
    console.error('Todo GET route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    devLog('POST request started');
    
    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      devLog('CSRF token validation failed');
      return createCSRFErrorResponse();
    }
    
    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      // Keep security-related logs for audit purposes
      console.warn('Todo POST: Authentication failed - No access token');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();
    devLog('Request received with body keys:', Object.keys(body));

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos`;
    devLog('Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    devLog('Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.text();
      // Keep error logs for troubleshooting
      console.error('Todo POST: Backend request failed', { 
        status: response.status, 
        url: backendUrl,
        error: errorData 
      });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('Success, created todo with ID:', data.id);

    return NextResponse.json(data);
  } catch (error) {
    // Always keep error logs for monitoring
    console.error('Todo POST route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
