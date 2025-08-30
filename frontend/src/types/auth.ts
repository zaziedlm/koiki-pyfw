// Authentication related types matching backend API schemas
import { UserResponse } from './user';

export interface LoginRequest {
  username: string; // email in OAuth2 format
  password: string;
}

export interface TokenWithRefresh {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number; // seconds
}

export interface AuthResponse {
  message: string;
  user?: Record<string, unknown>;
  data?: Record<string, unknown>;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string; // min 8 chars
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string; // min 8 chars
}

// Auth state types for frontend
export interface AuthState {
  isAuthenticated: boolean;
  user: UserResponse | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}