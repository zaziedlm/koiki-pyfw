import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { cookieApiClient } from '@/lib/cookie-api-client';
import { LoginCredentials, RegisterData } from '@/types';

// dev-only minimal logger (no sensitive data)
const devLog = (...args: unknown[]) => {
  if (process.env.NODE_ENV !== 'production') {
    console.log('[cookie-auth]', ...args);
  }
};

// Query keys for cookie auth
export const cookieAuthKeys = {
  all: ['cookie-auth'] as const,
  me: () => [...cookieAuthKeys.all, 'me'] as const,
} as const;

// Get current user (Cookie認証)
export function useCookieMe() {
  return useQuery({
    queryKey: cookieAuthKeys.me(),
    queryFn: async () => {
      const response = await cookieApiClient.auth.getMe();

      // 未ログイン(401)は例外ではなく「未認証」として扱う
      if (response.status === 401) {
        return null;
      }

      if (!response.ok) {
        // 401 以外の異常はエラーにする
        let message = `Failed to fetch user (${response.status})`;
        try {
          const data = await response.json();
          message = data?.detail || data?.message || message;
        } catch {
          // ignore
        }
        throw new Error(message);
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5分
    // 未認証時の 401 は例外にしないため、基本的に再試行は不要
    retry: false,
  });
}

// Login mutation (Cookie認証)
export function useCookieLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      devLog('login: start');

      const response = await cookieApiClient.auth.login({
        email: credentials.email,
        password: credentials.password,
      });

      devLog('login: response', { status: response.status, ok: response.ok });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = (errorData && (errorData.detail || errorData.message)) || `Login failed (${response.status})`;
        throw new Error(errorMessage);
      }

      return response.json();
    },
    onSuccess: async (data) => {
      devLog('login: success');

      try {
        // ログイン成功時にユーザー情報をキャッシュ
        if (data.user) {
          devLog('login: cache user');
          queryClient.setQueryData(cookieAuthKeys.me(), data.user);
        }

        // すべての認証関連クエリを無効化（await で完了を待つ）
        devLog('login: invalidate queries');
        await queryClient.invalidateQueries({ queryKey: cookieAuthKeys.all });
        devLog('login: invalidation done');

        // Cookie設定完了の確認とリダイレクト処理
        devLog('login: check redirect');

        if (data.new_cookie_set) {
          devLog('login: wait cookie propagation');

          // Cookieの伝播を待つためのポーリング機能
          const waitForCookie = async (maxAttempts = 10, delay = 200): Promise<boolean> => {
            for (let attempt = 0; attempt < maxAttempts; attempt++) {
              devLog('login: cookie check attempt', `${attempt + 1}/${maxAttempts}`);

              // document.cookieでクライアント側cookieを確認（httpOnlyなので直接は見えないが、認証状態で判断）
              try {
                // ユーザー情報が取得できるかテスト
                await queryClient.refetchQueries({ queryKey: cookieAuthKeys.me() });
                const userData = queryClient.getQueryData(cookieAuthKeys.me());

                if (userData) {
                  devLog('login: cookie verified');
                  return true;
                }
              } catch {
                devLog('login: cookie verify failed attempt', attempt + 1);
              }

              // 次の試行まで待機
              if (attempt < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, delay));
              }
            }

            devLog('login: cookie verification timeout');
            return false;
          };

          // Cookie伝播を待ってからリダイレクト
          waitForCookie().finally(() => {
            const targetLocation = data.location || '/dashboard';
            devLog('login: redirect to', targetLocation);
            window.location.href = targetLocation;
          });

        } else {
          // フォールバック: Cookie設定フラグがない場合は従来の遅延リダイレクト
          devLog('login: fallback redirect');
          setTimeout(() => {
            window.location.href = data.location || '/dashboard';
          }, 800);
        }
      } catch {
        devLog('login: onSuccess error');
        throw new Error('Login post-success handling failed');
      }
    },
    onError: () => {
      devLog('login: error');
    },
  });
}

// Logout mutation (Cookie認証)
export function useCookieLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await cookieApiClient.auth.logout();

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Logout failed');
      }

      return response.json();
    },
    onSuccess: () => {
      // ログアウト成功時にキャッシュをクリア
      queryClient.clear();

      // または、特定のクエリのみクリア
      queryClient.removeQueries({ queryKey: cookieAuthKeys.all });
    },
    onError: () => {
      // ログアウトエラー時もキャッシュをクリア（強制ログアウト）
      queryClient.clear();
    },
  });
}

// Register mutation (Cookie認証)
export function useCookieRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData: RegisterData) => {
      const response = await cookieApiClient.auth.register(userData);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      return response.json();
    },
    onSuccess: (data) => {
      // 登録成功時にユーザー情報をキャッシュ
      if (data.user) {
        queryClient.setQueryData(cookieAuthKeys.me(), data.user);
      }

      // すべての認証関連クエリを無効化
      queryClient.invalidateQueries({ queryKey: cookieAuthKeys.all });
    },
  });
}

// Refresh token mutation (Cookie認証)
export function useCookieRefreshToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await cookieApiClient.auth.refreshToken();

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Token refresh failed');
      }

      return response.json();
    },
    onSuccess: () => {
      // トークン更新成功時にユーザー情報を再取得
      queryClient.invalidateQueries({ queryKey: cookieAuthKeys.me() });
    },
    onError: () => {
      // トークン更新失敗時はログアウト状態にする
      queryClient.removeQueries({ queryKey: cookieAuthKeys.all });
    },
  });
}

// 認証状態を取得するヘルパーフック
export function useCookieAuth() {
  const { data: user, isLoading, error } = useCookieMe();

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
  };
}