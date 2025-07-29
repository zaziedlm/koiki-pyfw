import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { securityApi } from '@/lib/api-client';

// Query keys
export const securityKeys = {
  all: ['security'] as const,
  metrics: () => [...securityKeys.all, 'metrics'] as const,
  authMetrics: () => [...securityKeys.all, 'auth-metrics'] as const,
  summary: () => [...securityKeys.all, 'summary'] as const,
  health: () => [...securityKeys.all, 'health'] as const,
} as const;

// Get security metrics
export function useSecurityMetrics() {
  return useQuery({
    queryKey: securityKeys.metrics(),
    queryFn: () => securityApi.getMetrics().then(res => res.data),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

// Get authentication metrics
export function useAuthMetrics() {
  return useQuery({
    queryKey: securityKeys.authMetrics(),
    queryFn: () => securityApi.getAuthMetrics().then(res => res.data),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

// Get security summary
export function useSecuritySummary() {
  return useQuery({
    queryKey: securityKeys.summary(),
    queryFn: () => securityApi.getSummary().then(res => res.data),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 2 * 60 * 1000, // Refetch every 2 minutes
  });
}

// Get security health
export function useSecurityHealth() {
  return useQuery({
    queryKey: securityKeys.health(),
    queryFn: () => securityApi.getHealth().then(res => res.data),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    retry: false, // Don't retry health checks
  });
}

// Reset security metrics mutation
export function useResetSecurityMetrics() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => securityApi.resetMetrics().then(res => res.data),
    onSuccess: () => {
      // Invalidate all security-related queries
      queryClient.invalidateQueries({ queryKey: securityKeys.all });
    },
  });
}

// Refresh all security data
export function useRefreshSecurityData() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      // Force refetch all security queries
      await Promise.all([
        queryClient.refetchQueries({ queryKey: securityKeys.metrics() }),
        queryClient.refetchQueries({ queryKey: securityKeys.authMetrics() }),
        queryClient.refetchQueries({ queryKey: securityKeys.summary() }),
        queryClient.refetchQueries({ queryKey: securityKeys.health() }),
      ]);
    },
  });
}