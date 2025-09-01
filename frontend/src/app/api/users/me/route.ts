import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

// export const runtime = 'nodejs';

function getAccessToken(req: NextRequest): string | null {
    return req.cookies.get('koiki_access_token')?.value ?? null;
}

export async function GET(request: NextRequest) {
    const token = getAccessToken(request);
    if (!token) {
        return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
    }

    const url = `${config.api.baseUrl}/users/me`;
    const res = await fetch(url, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        cache: 'no-store',
    });

    if (!res.ok) {
        const text = await res.text();
        return NextResponse.json({ detail: text || 'Backend error' }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
}

export async function PUT(request: NextRequest) {
    if (!validateCSRFToken(request)) {
        return createCSRFErrorResponse();
    }

    const token = getAccessToken(request);
    if (!token) {
        return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
    }

    const body = await request.json().catch(() => ({}));
    const url = `${config.api.baseUrl}/users/me`;
    const res = await fetch(url, {
        method: 'PUT',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const text = await res.text();
        return NextResponse.json({ detail: text || 'Backend error' }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
}
