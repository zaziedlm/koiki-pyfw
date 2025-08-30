import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    console.log('📋 Todo GET (single) route handler started, ID:', id);
    
    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      console.log('❌ Todo GET (single): No access token found in cookies');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
    console.log('🔗 Todo GET (single): Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    console.log('📡 Todo GET (single): Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.text();
      console.log('❌ Todo GET (single): Backend error:', errorData);
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('✅ Todo GET (single): Success, todo:', data.id);

    return NextResponse.json(data);
  } catch (error) {
    console.error('❌ Todo GET (single) route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    console.log('📋 Todo PUT route handler started, ID:', id);
    
    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      console.log('❌ Todo PUT: No access token found in cookies');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();
    console.log('📝 Todo PUT: Request body:', body);

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
    console.log('🔗 Todo PUT: Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    console.log('📡 Todo PUT: Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.text();
      console.log('❌ Todo PUT: Backend error:', errorData);
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('✅ Todo PUT: Success, updated todo:', data.id);

    return NextResponse.json(data);
  } catch (error) {
    console.error('❌ Todo PUT route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    console.log('📋 Todo DELETE route handler started, ID:', id);
    
    // Get access token from cookies
    const accessToken = request.cookies.get('koiki_access_token')?.value;
    
    if (!accessToken) {
      console.log('❌ Todo DELETE: No access token found in cookies');
      return NextResponse.json(
        { error: 'Authentication required', detail: 'Access token not found' },
        { status: 401 }
      );
    }

    // Forward request to backend with token
    const backendUrl = `${config.api.baseUrl}/todos/${id}`;
    console.log('🔗 Todo DELETE: Backend URL:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    console.log('📡 Todo DELETE: Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.text();
      console.log('❌ Todo DELETE: Backend error:', errorData);
      return NextResponse.json(
        { error: 'Backend request failed', detail: errorData },
        { status: response.status }
      );
    }

    console.log('✅ Todo DELETE: Success, deleted todo:', id);

    // Return success response (DELETE typically returns empty body or confirmation)
    return NextResponse.json({ message: 'Todo deleted successfully' });
  } catch (error) {
    console.error('❌ Todo DELETE route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', detail: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}