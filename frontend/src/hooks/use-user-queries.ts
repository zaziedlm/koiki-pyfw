import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/lib/api-client';
import { UserCreate, UserUpdate, UserListParams } from '@/types';

// Query keys
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (params: UserListParams) => [...userKeys.lists(), params] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: number) => [...userKeys.details(), id] as const,
  me: () => [...userKeys.all, 'me'] as const,
} as const;

// Get current user (different from auth/me)
export function useCurrentUser() {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: () => userApi.getMe().then(res => res.data),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Get users list (admin only)
export function useUsers(params: UserListParams = {}) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => userApi.getAll(params).then(res => res.data),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get single user (admin only)
export function useUser(id: number) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => userApi.getById(id).then(res => res.data),
    enabled: !!id,
  });
}

// Create user mutation (admin only)
export function useCreateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: UserCreate) => userApi.create(data).then(res => res.data),
    onSuccess: () => {
      // Invalidate all user lists
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

// Update user mutation (admin only)
export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdate }) => 
      userApi.update(id, data).then(res => res.data),
    onSuccess: (data, variables) => {
      // Update the specific user in cache
      queryClient.setQueryData(userKeys.detail(variables.id), data);
      // Invalidate all user lists
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

// Update current user profile
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: UserUpdate) => userApi.updateMe(data).then(res => res.data),
    onSuccess: (data) => {
      // Update current user data in cache
      queryClient.setQueryData(userKeys.me(), data);
      // Also invalidate auth/me if it exists
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });
}

// Delete user mutation (admin only)
export function useDeleteUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => userApi.delete(id),
    onSuccess: (_, id) => {
      // Remove the user from cache
      queryClient.removeQueries({ queryKey: userKeys.detail(id) });
      // Invalidate all user lists
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}