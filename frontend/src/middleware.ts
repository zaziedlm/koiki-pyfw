import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Use experimental-edge runtime for Next.js 15 compatibility
export const runtime = 'experimental-edge';

// Define protected routes that require authentication
const PROTECTED_ROUTES = ['/dashboard', '/profile', '/admin', '/settings'] as const;
const AUTH_TOKEN_COOKIE = 'koiki_access_token';
const LOGIN_PATH = '/auth/login';

// Environment-based logging (Next.js 15 best practice)
const isDevelopment = process.env.NODE_ENV === 'development';

function log(message: string, data?: unknown) {
  if (isDevelopment) {
    console.log(`[MIDDLEWARE] ${message}`, data || '');
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  log(`Processing: ${pathname}`);

  // Early return for static files (Next.js 15 performance optimization)
  if (pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/') ||
    pathname.includes('.')) {
    return NextResponse.next();
  }

  // Check if route requires authentication
  const isProtectedRoute = PROTECTED_ROUTES.some(route =>
    pathname.startsWith(route)
  );

  if (!isProtectedRoute) {
    log(`Public route: ${pathname}`);
    return NextResponse.next();
  }

  // Authentication check for protected routes
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;

  if (!token) {
    log(`Redirect to login (no token): ${pathname}`);
    const loginUrl = new URL(LOGIN_PATH, request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Basic JWT format validation (Next.js 15 security best practice)
  if (!isValidJWTFormat(token)) {
    log(`Invalid token format`);
    const loginUrl = new URL(LOGIN_PATH, request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  log(`Access granted: ${pathname}`);
  return NextResponse.next();
}

// Helper function for JWT format validation
function isValidJWTFormat(token: string): boolean {
  // JWT should have 3 parts separated by dots
  const parts = token.split('.');
  return parts.length === 3 && parts.every(part => part.length > 0);
}

// Configure matcher for protected routes only (Next.js 15 best practice)
export const config = {
  matcher: [
    // Only run middleware on protected routes for better performance
    '/dashboard/:path*',
    '/profile/:path*',
    '/admin/:path*',
    '/settings/:path*',
  ],
};