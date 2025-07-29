import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { todoApi } from '@/lib/api-client';
import { TodoCreate, TodoUpdate, TodoListParams } from '@/types';

// Query keys
export const todoKeys = {
  all: ['todos'] as const,
  lists: () => [...todoKeys.all, 'list'] as const,
  list: (params: TodoListParams) => [...todoKeys.lists(), params] as const,
  details: () => [...todoKeys.all, 'detail'] as const,
  detail: (id: number) => [...todoKeys.details(), id] as const,
} as const;

// Get todos list
export function useTodos(params: TodoListParams = {}) {
  return useQuery({
    queryKey: todoKeys.list(params),
    queryFn: () => todoApi.getAll(params).then(res => res.data),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Get single todo
export function useTodo(id: number) {
  return useQuery({
    queryKey: todoKeys.detail(id),
    queryFn: () => todoApi.getById(id).then(res => res.data),
    enabled: !!id,
  });
}

// Create todo mutation
export function useCreateTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TodoCreate) => todoApi.create(data).then(res => res.data),
    onSuccess: () => {
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}

// Update todo mutation
export function useUpdateTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TodoUpdate }) => 
      todoApi.update(id, data).then(res => res.data),
    onSuccess: (data, variables) => {
      // Update the specific todo in cache
      queryClient.setQueryData(todoKeys.detail(variables.id), data);
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}

// Delete todo mutation
export function useDeleteTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => todoApi.delete(id),
    onSuccess: (_, id) => {
      // Remove the todo from cache
      queryClient.removeQueries({ queryKey: todoKeys.detail(id) });
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}

// Toggle todo completion mutation
export function useToggleTodo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      // Get current todo data
      const currentData = queryClient.getQueryData(todoKeys.detail(id)) as any;
      if (!currentData) {
        // If not in cache, fetch it first
        const response = await todoApi.getById(id);
        const todo = response.data;
        return todoApi.update(id, { is_completed: !todo.is_completed }).then(res => res.data);
      }
      
      return todoApi.update(id, { is_completed: !currentData.is_completed }).then(res => res.data);
    },
    onSuccess: (data, id) => {
      // Update the specific todo in cache
      queryClient.setQueryData(todoKeys.detail(id), data);
      // Invalidate all todo lists
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}