'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores';
import { useCookieAuth } from '@/hooks/use-cookie-auth-queries';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requiredRoles?: string[];
  fallback?: React.ReactNode;
}

export function AuthGuard({ 
  children, 
  requireAuth = true, 
  requiredRoles = [],
  fallback
}: AuthGuardProps) {
  const [isChecking, setIsChecking] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  
  // 認証方式の設定 - 環境変数またはconfig設定で切り替え
  const useLocalStorageAuth = process.env.NEXT_PUBLIC_USE_LOCALSTORAGE_AUTH === 'true';
  
  // LocalStorage認証の場合
  const { isAuthenticated: localAuthState, user: localUser, isLoading: localLoading, refreshUser, checkTokenValidity } = useAuthStore();
  
  // Cookie認証の場合
  const { user: cookieUser, isAuthenticated: cookieAuthState, isLoading: cookieLoading, error: cookieError } = useCookieAuth();
  
  // 認証方式に応じて状態を選択
  const isAuthenticated = useLocalStorageAuth ? localAuthState : cookieAuthState;
  const user = useLocalStorageAuth ? localUser : cookieUser;
  const isLoading = useLocalStorageAuth ? localLoading : cookieLoading;

  useEffect(() => {
    const checkAuth = async () => {
      console.log('🔐 AuthGuard checkAuth - Start:', { 
        useLocalStorageAuth, 
        isAuthenticated, 
        isLoading, 
        user: !!user,
        cookieError 
      });
      
      // If auth is loading, wait for it to complete
      if (isLoading) {
        console.log('🔐 AuthGuard - Still loading auth state');
        return;
      }

      try {
        if (useLocalStorageAuth) {
          // LocalStorage認証の場合のチェック
          checkTokenValidity();
          
          // Try to refresh user data if we think we're authenticated but don't have user data
          if (isAuthenticated && !user) {
            await refreshUser();
          }
        } else {
          // Cookie認証の場合は、useCookieAuth hookが自動的に認証状態を管理
          console.log('🔐 Cookie Auth State:', { 
            isAuthenticated, 
            hasUser: !!user, 
            error: cookieError ? String(cookieError) : null
          });
        }
      } catch (error) {
        console.error('Auth refresh failed:', error);
      } finally {
        console.log('🔐 AuthGuard checkAuth - Complete:', { isAuthenticated, hasUser: !!user });
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [isAuthenticated, user, isLoading, useLocalStorageAuth, cookieError, refreshUser, checkTokenValidity]);

  // トークンの定期チェック（LocalStorage認証のみ）
  useEffect(() => {
    if (useLocalStorageAuth && requireAuth && isAuthenticated) {
      const interval = setInterval(() => {
        checkTokenValidity();
      }, 5 * 60 * 1000); // 5分ごと

      return () => clearInterval(interval);
    }
  }, [useLocalStorageAuth, requireAuth, isAuthenticated, checkTokenValidity]);

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
    const userRoles = user?.roles?.map((role: any) => role.name) || [];
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
  
  // 認証方式の設定
  const useLocalStorageAuth = process.env.NEXT_PUBLIC_USE_LOCALSTORAGE_AUTH === 'true';
  
  // LocalStorage認証の場合
  const { isAuthenticated: localAuthState, isLoading: localLoading } = useAuthStore();
  
  // Cookie認証の場合
  const { isAuthenticated: cookieAuthState, isLoading: cookieLoading } = useCookieAuth();
  
  // 認証方式に応じて状態を選択
  const isAuthenticated = useLocalStorageAuth ? localAuthState : cookieAuthState;
  const isLoading = useLocalStorageAuth ? localLoading : cookieLoading;

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