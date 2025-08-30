import { create } from 'zustand';
import { TodoState, TodoResponse, TodoCreate, TodoUpdate, TodoFilter, TodoStats } from '@/types';
import { todoApi } from '@/lib/api-client';

interface TodoStore extends TodoState {
  // Actions
  fetchTodos: (params?: { skip?: number; limit?: number }) => Promise<void>;
  createTodo: (data: TodoCreate) => Promise<TodoResponse>;
  updateTodo: (id: number, data: TodoUpdate) => Promise<TodoResponse>;
  deleteTodo: (id: number) => Promise<void>;
  toggleTodo: (id: number) => Promise<void>;
  setFilter: (filter: Partial<TodoFilter>) => void;
  clearError: () => void;
  getTodoStats: () => TodoStats;
}

export const useTodoStore = create<TodoStore>()((set, get) => ({
  // Initial state
  todos: [],
  isLoading: false,
  error: null,
  totalCount: 0,
  filter: {},

  // Actions
  fetchTodos: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await todoApi.getAll(params);
      const todos = response.data;
      
      set({
        todos,
        totalCount: todos.length,
        isLoading: false,
        error: null,
      });
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to fetch todos';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  createTodo: async (data: TodoCreate) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await todoApi.create(data);
      const newTodo = response.data;
      
      set((state) => ({
        todos: [newTodo, ...state.todos],
        totalCount: state.totalCount + 1,
        isLoading: false,
        error: null,
      }));
      
      return newTodo;
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to create todo';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  updateTodo: async (id: number, data: TodoUpdate) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await todoApi.update(id, data);
      const updatedTodo = response.data;
      
      set((state) => ({
        todos: state.todos.map((todo) =>
          todo.id === id ? updatedTodo : todo
        ),
        isLoading: false,
        error: null,
      }));
      
      return updatedTodo;
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to update todo';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  deleteTodo: async (id: number) => {
    set({ isLoading: true, error: null });
    
    try {
      await todoApi.delete(id);
      
      set((state) => ({
        todos: state.todos.filter((todo) => todo.id !== id),
        totalCount: state.totalCount - 1,
        isLoading: false,
        error: null,
      }));
    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to delete todo';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  toggleTodo: async (id: number) => {
    const todo = get().todos.find((t) => t.id === id);
    if (!todo) return;

    try {
      await get().updateTodo(id, { is_completed: !todo.is_completed });
    } catch (error) {
      // Error is already handled in updateTodo
      throw error;
    }
  },

  setFilter: (filter: Partial<TodoFilter>) => {
    set((state) => ({
      filter: { ...state.filter, ...filter },
    }));
  },

  clearError: () => set({ error: null }),

  getTodoStats: (): TodoStats => {
    const { todos } = get();
    const total = todos.length;
    const completed = todos.filter((todo) => todo.is_completed).length;
    const pending = total - completed;
    const completionRate = total > 0 ? (completed / total) * 100 : 0;

    return {
      total,
      completed,
      pending,
      completionRate,
    };
  },
}));