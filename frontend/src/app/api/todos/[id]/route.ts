import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

const isDevelopment = process.env.NODE_ENV === 'development';
const devLog = (msg: string) => { if (isDevelopment) console.log(`[TODOS] ${msg}`); };

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    devLog('GET one start');

    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;

    if (!accessToken) {
      if (isDevelopment) console.warn('[TODOS] GET one unauthorized (no token)');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
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
      if (isDevelopment) console.error('[TODOS] GET one backend error', { status: response.status });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('GET one success');

    return NextResponse.json(data);
  } catch (error) {
    console.error('[TODOS] GET one handler error');
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    devLog('PUT start');

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      devLog('CSRF validation failed');
      return createCSRFErrorResponse();
    }

    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;

    if (!accessToken) {
      if (isDevelopment) console.warn('[TODOS] PUT unauthorized (no token)');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
    devLog('Backend request');

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    devLog(`Backend status ${response.status}`);

    if (!response.ok) {
      const errorData = await response.text();
      if (isDevelopment) console.error('[TODOS] PUT backend error', { status: response.status });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    devLog('PUT success');

    return NextResponse.json(data);
  } catch (error) {
    console.error('[TODOS] PUT handler error');
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    devLog('DELETE start');

    // CSRF トークン検証
    if (!validateCSRFToken(request)) {
      devLog('CSRF validation failed');
      return createCSRFErrorResponse();
    }

    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;

    if (!accessToken) {
      if (isDevelopment) console.warn('[TODOS] DELETE unauthorized (no token)');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
    devLog('Backend request');

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    devLog(`Backend status ${response.status}`);

    if (!response.ok) {
      const errorData = await response.text();
      if (isDevelopment) console.error('[TODOS] DELETE backend error', { status: response.status });
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    devLog('DELETE success');

    // Return success response (DELETE typically returns empty body or confirmation)
    return NextResponse.json({ message: 'Todo deleted successfully' });
  } catch (err) {
    console.error('[TODOS] DELETE handler error');
    return NextResponse.json(
      { error: 'Internal server error', detail: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
