import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { cookieTodoApi } from '@/lib/cookie-api-client';
import { TodoCreate, TodoUpdate, TodoListParams, TodoResponse } from '@/types';

// Query keys for cookie todo
export const cookieTodoKeys = {
  all: ['cookie-todos'] as const,
  lists: () => [...cookieTodoKeys.all, 'list'] as const,
  list: (params: TodoListParams) => [...cookieTodoKeys.lists(), params] as const,
  details: () => [...cookieTodoKeys.all, 'detail'] as const,
  detail: (id: number) => [...cookieTodoKeys.details(), id] as const,
} as const;

// Get todos list (Cookie認証)
export function useCookieTodos(params: TodoListParams = {}) {
  return useQuery({
    queryKey: cookieTodoKeys.list(params),
    queryFn: async () => {
      return cookieTodoApi.getAll(params);
    },
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Get single todo (Cookie認証)
export function useCookieTodo(id: number) {
  return useQuery({
    queryKey: cookieTodoKeys.detail(id),
    queryFn: async () => {
      return cookieTodoApi.getById(id);
    },
    enabled: !!id,
  });
}

// Create todo mutation (Cookie認証)
export function useCookieCreateTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: TodoCreate) => {
      return cookieTodoApi.create(data);
    },
    onSuccess: () => {
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

// Update todo mutation (Cookie認証)
export function useCookieUpdateTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: TodoUpdate }) => {
      return cookieTodoApi.update(id, data);
    },
    onSuccess: (data: TodoResponse, variables) => {
      // Update the specific todo in cache
      queryClient.setQueryData(cookieTodoKeys.detail(variables.id), data);
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

// Delete todo mutation (Cookie認証)
export function useCookieDeleteTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      return cookieTodoApi.delete(id);
    },
    onSuccess: (_, id) => {
      // Remove the todo from cache
      queryClient.removeQueries({ queryKey: cookieTodoKeys.detail(id) });
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

// Toggle todo completion mutation (Cookie認証)
export function useCookieToggleTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      // Get current todo data
      const currentData = queryClient.getQueryData(cookieTodoKeys.detail(id)) as TodoResponse | undefined;
      
      if (!currentData) {
        // If not in cache, fetch it first
        const todo = await cookieTodoApi.getById(id);
        
        return cookieTodoApi.update(id, { is_completed: !todo.is_completed });
      }
      
      return cookieTodoApi.update(id, { is_completed: !currentData.is_completed });
    },
    onSuccess: (data: TodoResponse, id) => {
      // Update the specific todo in cache
      queryClient.setQueryData(cookieTodoKeys.detail(id), data);
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}
