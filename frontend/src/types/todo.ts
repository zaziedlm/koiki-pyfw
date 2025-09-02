// Todo related types matching backend API schemas

export interface TodoResponse {
  id: number;
  title: string;
  description?: string;
  is_completed: boolean;
  owner_id: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface TodoCreate {
  title: string; // 1-255 chars
  description?: string;
}

export interface TodoUpdate {
  title?: string; // 1-255 chars
  description?: string;
  is_completed?: boolean;
}

// Frontend-specific todo types
export interface TodoListParams {
  skip?: number;
  limit?: number;
}

export interface TodoState {
  todos: TodoResponse[];
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  filter: TodoFilter;
}

export interface TodoFilter {
  completed?: boolean;
  search?: string;
}

export interface TodoFormData {
  title: string;
  description: string;
}

export interface TodoStats {
  total: number;
  completed: number;
  pending: number;
  completionRate: number;
}