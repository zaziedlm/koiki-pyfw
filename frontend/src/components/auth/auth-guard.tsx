'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useCookieAuth } from '@/hooks/use-cookie-auth-queries';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requiredRoles?: string[];
  fallback?: React.ReactNode;
}

const isDev = process.env.NODE_ENV !== 'production';
const devLog = (...args: unknown[]) => {
  if (isDev) {
    console.log('[auth-guard]', ...args);
  }
};

export function AuthGuard({
  children,
  requireAuth = true,
  requiredRoles = [],
  fallback,
}: AuthGuardProps) {
  const [isChecking, setIsChecking] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const { user, isAuthenticated, isLoading, error: cookieError } = useCookieAuth();

  useEffect(() => {
    const checkAuth = async () => {
      devLog('checkAuth:start', { isAuthenticated, isLoading, hasUser: !!user });

      // If auth is loading, wait for it to complete
      if (isLoading) {
        devLog('checkAuth:loading');
        return;
      }

      try {
        // Cookie認証の状態確認（本番ではログ非表示）
        devLog('state', {
          isAuthenticated,
          hasUser: !!user,
          error: cookieError ? String(cookieError) : null,
        });
      } catch (error) {
        if (isDev) {
          console.error('Auth check failed:', error instanceof Error ? error.message : error);
        }
      } finally {
        devLog('checkAuth:complete', { isAuthenticated, hasUser: !!user });
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [isAuthenticated, user, isLoading, cookieError]);

  // Handle authentication redirect in useEffect to avoid rendering during render
  useEffect(() => {
    if (!isLoading && !isChecking && requireAuth && !isAuthenticated) {
      router.push(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [requireAuth, isAuthenticated, isLoading, isChecking, router, pathname]);

  // Still checking authentication state
  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Require authentication but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // Check role-based access
  if (requireAuth && isAuthenticated && requiredRoles.length > 0) {
    const userRoles = user?.roles?.map((role: { name: string }) => role.name) || [];
    const hasRequiredRole = requiredRoles.some((role: string) =>
      userRoles.includes(role) || user?.is_superuser
    );

    if (!hasRequiredRole) {
      if (fallback) {
        return <>{fallback}</>;
      }

      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <div className="text-6xl">🔒</div>
            <h1 className="text-2xl font-bold">Access Denied</h1>
            <p className="text-muted-foreground">
              You don&apos;t have permission to access this page.
            </p>
            <button
              onClick={() => router.back()}
              className="text-primary hover:underline"
            >
              Go back
            </button>
          </div>
        </div>
      );
    }
  }

  // User is authenticated or authentication is not required
  return <>{children}</>;
}

// Convenience wrapper for admin-only pages
export function AdminGuard({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <AuthGuard requireAuth={true} requiredRoles={['admin']} fallback={fallback}>
      {children}
    </AuthGuard>
  );
}

// Convenience wrapper for authenticated pages
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard requireAuth={true}>
      {children}
    </AuthGuard>
  );
}

// Wrapper for public pages that should redirect authenticated users
export function PublicRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const { isAuthenticated, isLoading } = useCookieAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Redirecting...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
