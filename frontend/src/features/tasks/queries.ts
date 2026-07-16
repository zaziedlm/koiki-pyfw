import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { TodoCreate, TodoListParams, TodoResponse, TodoUpdate } from '@/types';
import { cookieTodoApi } from './api';

export const cookieTodoKeys = {
  all: ['cookie-todos'] as const,
  lists: () => [...cookieTodoKeys.all, 'list'] as const,
  list: (params: TodoListParams) => [...cookieTodoKeys.lists(), params] as const,
  details: () => [...cookieTodoKeys.all, 'detail'] as const,
  detail: (id: number) => [...cookieTodoKeys.details(), id] as const,
} as const;

export function useCookieTodos(params: TodoListParams = {}) {
  return useQuery({
    queryKey: cookieTodoKeys.list(params),
    queryFn: async () => {
      return cookieTodoApi.getAll(params);
    },
    staleTime: 30 * 1000,
  });
}

export function useCookieTodo(id: number) {
  return useQuery({
    queryKey: cookieTodoKeys.detail(id),
    queryFn: async () => {
      return cookieTodoApi.getById(id);
    },
    enabled: !!id,
  });
}

export function useCookieCreateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TodoCreate) => {
      return cookieTodoApi.create(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

export function useCookieUpdateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: TodoUpdate }) => {
      return cookieTodoApi.update(id, data);
    },
    onSuccess: (data: TodoResponse, variables) => {
      queryClient.setQueryData(cookieTodoKeys.detail(variables.id), data);
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

export function useCookieDeleteTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      return cookieTodoApi.delete(id);
    },
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: cookieTodoKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}

export function useCookieToggleTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const currentData = queryClient.getQueryData(cookieTodoKeys.detail(id)) as TodoResponse | undefined;

      if (!currentData) {
        const todo = await cookieTodoApi.getById(id);

        return cookieTodoApi.update(id, { is_completed: !todo.is_completed, version: todo.version });
      }

      return cookieTodoApi.update(id, { is_completed: !currentData.is_completed, version: currentData.version });
    },
    onSuccess: (data: TodoResponse, id) => {
      queryClient.setQueryData(cookieTodoKeys.detail(id), data);
      queryClient.invalidateQueries({ queryKey: cookieTodoKeys.lists() });
    },
  });
}
