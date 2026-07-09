import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { isApiError } from '@/shared/api';
import type { LoginCredentials, RegisterData } from '@/types';
import { cookieAuthApi } from './api';

const devLog = (...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.log('[cookie-auth]', ...args);
  }
};

export const cookieAuthKeys = {
  all: ['cookie-auth'] as const,
  me: () => [...cookieAuthKeys.all, 'me'] as const,
} as const;

export function useCookieMe() {
  return useQuery({
    queryKey: cookieAuthKeys.me(),
    queryFn: async () => {
      try {
        return await cookieAuthApi.getMe();
      } catch (error) {
        if (isApiError(error) && error.status === 401) {
          return null;
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useCookieLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      devLog('login: start');

      const result = await cookieAuthApi.login({
        email: credentials.email,
        password: credentials.password,
      });

      devLog('login: response');

      return result;
    },
    onSuccess: async (data) => {
      devLog('login: success');

      try {
        if (data.user) {
          devLog('login: cache user');
          queryClient.setQueryData(cookieAuthKeys.me(), data.user);
        }

        devLog('login: invalidate queries');
        await queryClient.invalidateQueries({ queryKey: cookieAuthKeys.all });
        devLog('login: invalidation done');
      } catch {
        devLog('login: onSuccess error');
        throw new Error('Login post-success handling failed');
      }
    },
    onError: () => {
      devLog('login: error');
    },
  });
}

export function useCookieLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      return cookieAuthApi.logout();
    },
    onSuccess: () => {
      queryClient.clear();
      queryClient.removeQueries({ queryKey: cookieAuthKeys.all });
    },
    onError: () => {
      queryClient.clear();
    },
  });
}

export function useCookieRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData: RegisterData) => {
      return cookieAuthApi.register(userData);
    },
    onSuccess: (data) => {
      if (data.user) {
        queryClient.setQueryData(cookieAuthKeys.me(), data.user);
      }

      queryClient.invalidateQueries({ queryKey: cookieAuthKeys.all });
    },
  });
}

export function useCookieRefreshToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      return cookieAuthApi.refreshToken();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookieAuthKeys.me() });
    },
    onError: () => {
      queryClient.removeQueries({ queryKey: cookieAuthKeys.all });
    },
  });
}

export function useCookieAuth() {
  const { data: user, isLoading, error } = useCookieMe();

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
  };
}
