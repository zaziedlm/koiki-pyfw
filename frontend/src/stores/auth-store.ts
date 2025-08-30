import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, LoginCredentials, RegisterData } from '@/types';
import { authApi, tokenStorage } from '@/lib/api-client';
import { isTokenExpired } from '@/lib/token-utils';

interface AuthStore extends AuthState {
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  checkTokenValidity: () => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authApi.login({
            username: credentials.email,
            password: credentials.password,
          });

          const { access_token, refresh_token } = response.data;
          
          // Store tokens first
          tokenStorage.set('koiki_access_token', access_token);
          tokenStorage.set('koiki_refresh_token', refresh_token);

          // トークンの有効性をチェック
          get().checkTokenValidity();

          // Set authenticated state first
          set({
            isAuthenticated: true,
            user: null, // Will be set after getMe call
            token: access_token,
            refreshToken: refresh_token,
            isLoading: false,
            error: null,
          });

          // Set mock user for now to test basic login flow
          const mockUser = { 
            id: 3, 
            username: 'security', 
            email: credentials.email,
            full_name: 'Security User',
            is_active: true,
            is_superuser: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            roles: []
          };
          
          set((state) => ({ ...state, user: mockUser }));
          
        } catch (error: unknown) {
          const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Login failed';
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });
        
        try {
          await authApi.register(data);
          
          // After successful registration, automatically log in
          await get().login({
            email: data.email,
            password: data.password,
          });
        } catch (error: unknown) {
          const errorMessage = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Registration failed';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await authApi.logout();
        } catch (error) {
          // Continue with logout even if API call fails
          console.warn('Logout API call failed:', error);
        } finally {
          // Clear tokens and state
          tokenStorage.clear();
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
            isLoading: false,
            error: null,
          });
        }
      },

      refreshUser: async () => {
        const token = tokenStorage.get('koiki_access_token');
        if (!token) {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
          });
          return;
        }

        try {
          const response = await authApi.getMe();
          const user = response.data;
          
          set({
            isAuthenticated: true,
            user,
            token,
            refreshToken: tokenStorage.get('koiki_refresh_token'),
            error: null,
          });
        } catch {
          // Token might be expired, clear auth state
          tokenStorage.clear();
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
            error: null,
          });
        }
      },

      checkTokenValidity: () => {
        const token = tokenStorage.get('koiki_access_token');
        const state = get();
        
        // トークンが存在しない場合、またはトークンが期限切れの場合
        if (!token || isTokenExpired(token)) {
          if (state.isAuthenticated) {
            // 認証状態をクリア
            tokenStorage.clear();
            set({
              isAuthenticated: false,
              user: null,
              token: null,
              refreshToken: null,
              error: null,
            });
          }
        } else {
          // トークンが有効で、まだ認証状態がセットされていない場合
          if (!state.isAuthenticated) {
            set({
              isAuthenticated: true,
              token,
              refreshToken: tokenStorage.get('koiki_refresh_token'),
            });
          }
        }
      },

      clearError: () => set({ error: null }),
      
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user, // ユーザー情報のみ永続化（認証状態はトークンから判断）
      }),
      onRehydrateStorage: () => (state) => {
        // ストア復元時にトークンの有効性をチェック
        if (state) {
          state.checkTokenValidity();
        }
      },
    }
  )
);