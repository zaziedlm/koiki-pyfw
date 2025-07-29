import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api-client';
import { useAuthStore } from '@/stores';
import { LoginCredentials, RegisterData, PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm } from '@/types';

// Query keys
export const authKeys = {
  all: ['auth'] as const,
  me: () => [...authKeys.all, 'me'] as const,
} as const;

// Get current user
export function useMe() {
  return useQuery({
    queryKey: authKeys.me(),
    queryFn: () => authApi.getMe().then(res => res.data),
    enabled: !!useAuthStore.getState().isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Login mutation
export function useLogin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (credentials: LoginCredentials) => 
      useAuthStore.getState().login(credentials),
    onSuccess: () => {
      // Invalidate and refetch user data
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
    },
  });
}

// Register mutation
export function useRegister() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: RegisterData) => 
      useAuthStore.getState().register(data),
    onSuccess: () => {
      // Invalidate and refetch user data
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
    },
  });
}

// Logout mutation
export function useLogout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => useAuthStore.getState().logout(),
    onSuccess: () => {
      // Clear all cached data
      queryClient.clear();
    },
  });
}

// Change password mutation
export function useChangePassword() {
  return useMutation({
    mutationFn: (data: PasswordChangeRequest) => 
      authApi.changePassword(data).then(res => res.data),
  });
}

// Request password reset mutation
export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (email: string) => 
      authApi.requestPasswordReset(email).then(res => res.data),
  });
}

// Confirm password reset mutation
export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: (data: PasswordResetConfirm) => 
      authApi.confirmPasswordReset(data).then(res => res.data),
  });
}

// Revoke all tokens mutation
export function useRevokeAllTokens() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => authApi.revokeAllTokens().then(res => res.data),
    onSuccess: () => {
      // Clear all cached data and logout
      queryClient.clear();
      useAuthStore.getState().logout();
    },
  });
}