import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/config';
import { validateCSRFToken, createCSRFErrorResponse } from '@/lib/csrf-utils';

type Role = { name?: string | null };
type MeUser = { is_superuser?: boolean; roles?: Role[] | null } | null;

// export const runtime = 'nodejs';

function getAccessToken(req: NextRequest): string | null {
    return req.cookies.get('koiki_access_token')?.value ?? null;
}

async function fetchCurrentUser(accessToken: string): Promise<MeUser> {
    const meUrl = `${config.api.baseUrl}/auth/me`;
    const res = await fetch(meUrl, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        cache: 'no-store',
    });
    if (!res.ok) return null;
    try { return await res.json(); } catch { return null; }
}

function isAdmin(user: MeUser): boolean {
    if (!user) return false;
    if (user.is_superuser) return true;
    const roles = user.roles ?? [];
    return Array.isArray(roles) && roles.some(r => ((r?.name ?? '').toLowerCase() === 'admin'));
}

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const token = getAccessToken(request);
    if (!token) {
        return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
    }

    const { id } = await params;

    // Admin only for viewing arbitrary user detail
    const user = await fetchCurrentUser(token);
    if (!isAdmin(user)) {
        return NextResponse.json({ detail: 'Forbidden' }, { status: 403 });
    }

    const url = `${config.api.baseUrl}/users/${id}`;
    const res = await fetch(url, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });

    if (!res.ok) {
        const text = await res.text();
        return NextResponse.json({ detail: text || 'Backend error' }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    if (!validateCSRFToken(request)) {
        return createCSRFErrorResponse();
    }

    const token = getAccessToken(request);
    if (!token) {
        return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
    }

    const { id } = await params;
    const user = await fetchCurrentUser(token);
    if (!isAdmin(user)) {
        return NextResponse.json({ detail: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json().catch(() => ({}));
    const url = `${config.api.baseUrl}/users/${id}`;
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

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    if (!validateCSRFToken(request)) {
        return createCSRFErrorResponse();
    }

    const token = getAccessToken(request);
    if (!token) {
        return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
    }

    const { id } = await params;
    const user = await fetchCurrentUser(token);
    if (!isAdmin(user)) {
        return NextResponse.json({ detail: 'Forbidden' }, { status: 403 });
    }

    const url = `${config.api.baseUrl}/users/${id}`;
    const res = await fetch(url, {
        method: 'DELETE',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });

    if (!res.ok) {
        const text = await res.text();
        return NextResponse.json({ detail: text || 'Backend error' }, { status: res.status });
    }
    return NextResponse.json({ message: 'User deleted' });
}
