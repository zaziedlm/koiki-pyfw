// User related types matching backend API schemas

export interface RoleResponseSimple {
  id: number;
  name: string;
  description?: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  roles: RoleResponseSimple[];
}

export interface UserCreate {
  username: string; // 3-50 chars
  email: string;
  password: string; // min 8 chars
  full_name?: string;
  is_active?: boolean; // default: true
}

export interface UserUpdate {
  username?: string;
  email?: string;
  full_name?: string;
  is_active?: boolean;
  password?: string;
}

// Frontend-specific user types
export interface UserListParams {
  skip?: number;
  limit?: number;
}

export interface UserState {
  users: UserResponse[];
  currentUser: UserResponse | null;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
}

export interface UserFormData {
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
}