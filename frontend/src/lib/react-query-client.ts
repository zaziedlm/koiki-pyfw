import { QueryClient } from '@tanstack/react-query';
import { isApiError } from '@/shared/api';

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        gcTime: 10 * 60 * 1000,
        retry: (failureCount, error: unknown) => {
          if (isApiError(error)) {
            if (error.status >= 400 && error.status < 500 && error.status !== 429) {
              return false;
            }
          }
          return failureCount < 3;
        },
        refetchOnWindowFocus: false,
        refetchOnMount: true,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: (failureCount, error: unknown) => {
          if (isApiError(error)) {
            if (error.status >= 400 && error.status < 500) {
              return false;
            }
          }
          return failureCount < 2;
        },
      },
    },
  });
}
