'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores';
import { tokenStorage } from '@/lib/api-client';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const { refreshUser, setLoading } = useAuthStore();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setLoading(true);
        
        // Check if we have a token in localStorage
        const token = tokenStorage.get('koiki_access_token');
        
        if (token) {
          // Try to refresh user data with the existing token
          try {
            await refreshUser();
          } catch (error) {
            // If refresh fails, clear tokens
            console.warn('Token refresh failed during initialization:', error);
            tokenStorage.clear();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [refreshUser, setLoading]);

  // Don't render children until auth is initialized
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return <>{children}</>;
}