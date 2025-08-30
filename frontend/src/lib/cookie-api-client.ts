import { config as appConfig } from './config';

// Cookie認証用のAPIクライアント
class CookieApiClient {
  public csrfToken: string | null = null;

  constructor() {
    // 初期化時にCSRFトークンを取得
    this.initializeCSRFToken();
  }

  // CSRFトークンを取得・設定
  public async initializeCSRFToken(): Promise<void> {
    try {
      // サーバーサイドでも動作するように絶対URLを使用
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000';
      const response = await fetch(`${baseUrl}/api/auth/csrf`);
      if (response.ok) {
        const data = await response.json();
        this.csrfToken = data.csrf_token;
        console.log('CSRF token initialized:', this.csrfToken ? 'SUCCESS' : 'FAILED');
      } else {
        console.error('Failed to get CSRF token - HTTP', response.status);
      }
    } catch (error) {
      console.error('Failed to initialize CSRF token:', error);
    }
  }

  // CSRFトークンを更新
  private async refreshCSRFToken() {
    await this.initializeCSRFToken();
  }

  // 共通のリクエストヘッダーを取得
  private getHeaders(isFormData = false): HeadersInit {
    const headers: HeadersInit = {};

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    // CSRFトークンをヘッダーに追加（Cookieからも取得を試行）
    let csrfToken = this.csrfToken;
    
    // CSRFトークンがない場合、Cookieから取得を試行
    if (!csrfToken && typeof document !== 'undefined') {
      const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('koiki_csrf_token='))
        ?.split('=')[1];
      
      if (cookieValue) {
        csrfToken = cookieValue;
        this.csrfToken = cookieValue; // キャッシュに保存
        console.log('CSRF token retrieved from cookie:', csrfToken ? 'PRESENT' : 'MISSING');
      }
    }

    if (csrfToken) {
      headers['x-csrf-token'] = csrfToken;
      console.log('CSRF token added to headers');
    } else {
      console.warn('CSRF token not available for request');
    }

    return headers;
  }

  // 共通のfetchメソッド
  public async fetchWithCredentials(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Cookieを自動で送信
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    // CSRF トークンエラーの場合は更新して再試行
    if (response.status === 403) {
      const errorData = await response.json();
      if (errorData.code === 'CSRF_TOKEN_INVALID') {
        await this.refreshCSRFToken();
        // 新しいCSRFトークンでリトライ
        return fetch(url, {
          ...options,
          credentials: 'include',
          headers: {
            ...this.getHeaders(),
            ...options.headers,
          },
        });
      }
    }

    return response;
  }

  // 認証API
  auth = {
    login: async (credentials: { email: string; password: string }) => {
      // CSRFトークンを確実に取得
      if (!this.csrfToken) {
        console.log('CSRF token not found, initializing...');
        await this.initializeCSRFToken();
      }

      console.log('Attempting login with CSRF token:', this.csrfToken ? 'PRESENT' : 'MISSING');

      return this.fetchWithCredentials('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
    },

    logout: async () => {
      return this.fetchWithCredentials('/api/auth/logout', {
        method: 'POST',
      });
    },

    register: async (userData: {
      username: string;
      email: string;
      password: string;
      full_name?: string;
    }) => {
      if (!this.csrfToken) {
        await this.initializeCSRFToken();
      }

      return this.fetchWithCredentials('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData),
      });
    },

    getMe: async () => {
      return this.fetchWithCredentials('/api/auth/me');
    },

    refreshToken: async () => {
      return this.fetchWithCredentials('/api/auth/refresh', {
        method: 'POST',
      });
    },
  };

  // 既存のAPIクライアントとの互換性のためのプロキシメソッド
  get = async (url: string) => {
    return this.fetchWithCredentials(appConfig.api.baseUrl + url);
  };

  post = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(appConfig.api.baseUrl + url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  put = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(appConfig.api.baseUrl + url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  patch = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(appConfig.api.baseUrl + url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  delete = async (url: string) => {
    return this.fetchWithCredentials(appConfig.api.baseUrl + url, {
      method: 'DELETE',
    });
  };
}

// シングルトンインスタンス
export const cookieApiClient = new CookieApiClient();

// Cookie対応のAPIメソッド
export const cookieApi = {
  // 認証API（Route Handlers経由）
  auth: cookieApiClient.auth,

  // その他のAPI（直接バックエンド、Cookie自動送信）
  get: cookieApiClient.get,
  post: cookieApiClient.post,
  put: cookieApiClient.put,
  patch: cookieApiClient.patch,
  delete: cookieApiClient.delete,
};

// Todo API methods (Cookie版) - Route Handler経由
export const cookieTodoApi = {
  getAll: (params?: { skip?: number; limit?: number }) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.fetchWithCredentials(`/api/todos${queryString}`, {
      method: 'GET',
    });
  },

  getById: (id: number) => cookieApiClient.fetchWithCredentials(`/api/todos/${id}`, {
    method: 'GET', 
  }),

  create: async (data: { title: string; description?: string }) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials('/api/todos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: number, data: { title?: string; description?: string; is_completed?: boolean }) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials(`/api/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: number) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials(`/api/todos/${id}`, {
      method: 'DELETE',
    });
  },
};

// User API methods (Cookie版)
export const cookieUserApi = {
  getMe: () => cookieApiClient.get('/users/me'),

  updateMe: (data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
  }) => cookieApiClient.put('/users/me', data),

  getAll: (params?: { skip?: number; limit?: number }) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.get(`/users${queryString}`);
  },

  getById: (id: number) => cookieApiClient.get(`/users/${id}`),

  create: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    is_active?: boolean;
  }) => cookieApiClient.post('/users', data),

  update: (id: number, data: {
    username?: string;
    email?: string;
    full_name?: string;
    is_active?: boolean;
    password?: string;
  }) => cookieApiClient.put(`/users/${id}`, data),

  delete: (id: number) => cookieApiClient.delete(`/users/${id}`),
};
