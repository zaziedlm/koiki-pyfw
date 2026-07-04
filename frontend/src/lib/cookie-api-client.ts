import { config as appConfig } from './config';

const CSRF_COOKIE_NAME = 'koiki_csrf_token';

function isDev(): boolean {
  return import.meta.env.DEV;
}

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, '');
}

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;

  const cookie = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split('=')[1] ?? '') : null;
}

// Cookie認証用のAPIクライアント
class CookieApiClient {
  public csrfToken: string | null = null;
  private readonly baseUrl = normalizeBaseUrl(appConfig.api.baseUrl);

  constructor() {
    // 初期化時にCSRFトークンを取得
    this.initializeCSRFToken();
  }

  private apiUrl(path: string): string {
    if (/^https?:\/\//i.test(path)) {
      return path;
    }

    return `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  }

  // CSRFトークンを取得・設定
  public async initializeCSRFToken(): Promise<void> {
    try {
      const response = await fetch(this.apiUrl('/auth/session/csrf'), {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        this.csrfToken = data.csrf_token;
        if (isDev()) {
          console.log('[CSRF] initialized');
        }
      } else {
        if (isDev()) {
          console.error('[CSRF] init failed http', response.status);
        }
      }
    } catch {
      if (isDev()) {
        console.error('[CSRF] init error');
      }
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
      const cookieValue = readCookie(CSRF_COOKIE_NAME);

      if (cookieValue) {
        csrfToken = cookieValue;
        this.csrfToken = cookieValue; // キャッシュに保存
        if (isDev()) {
          console.log('[CSRF] from cookie');
        }
      }
    }

    if (csrfToken) {
      headers['x-csrf-token'] = csrfToken;
      if (isDev()) {
        console.log('[CSRF] header attached');
      }
    } else if (isDev()) {
      console.warn('[CSRF] header missing');
    }

    return headers;
  }

  // 共通のfetchメソッド
  public async fetchWithCredentials(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const requestUrl = this.apiUrl(url);
    const response = await fetch(requestUrl, {
      ...options,
      credentials: 'include', // Cookieを自動で送信
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    // CSRF トークンエラーの場合は更新して再試行
    if (response.status === 403) {
      const errorData = await response.clone().json().catch(() => null);
      const errorCode = errorData?.code ?? errorData?.detail?.code;
      if (errorCode === 'CSRF_TOKEN_INVALID') {
        await this.refreshCSRFToken();
        // 新しいCSRFトークンでリトライ
        return fetch(requestUrl, {
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
        if (isDev()) {
          console.log('[AUTH] CSRF missing, init');
        }
        await this.initializeCSRFToken();
      }

      if (isDev()) {
        console.log('[AUTH] login with CSRF');
      }

      return this.fetchWithCredentials('/auth/session/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
    },

    logout: async () => {
      return this.fetchWithCredentials('/auth/session/logout', {
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

      return this.fetchWithCredentials('/auth/session/register', {
        method: 'POST',
        body: JSON.stringify(userData),
      });
    },

    getMe: async () => {
      return this.fetchWithCredentials('/auth/session/me');
    },

    refreshToken: async () => {
      return this.fetchWithCredentials('/auth/session/refresh', {
        method: 'POST',
      });
    },
  };

  sso = {
    authorization: async (params?: { redirect_uri?: string }) => {
      const queryString =
        params && params.redirect_uri
          ? `?${new URLSearchParams({ redirect_uri: params.redirect_uri }).toString()}`
          : '';

      return this.fetchWithCredentials(`/auth/sso/authorization${queryString}`);
    },

    login: async (payload: {
      authorization_code: string;
      code_verifier: string;
      state: string;
      nonce: string;
      redirect_uri: string;
    }) => {
      if (!this.csrfToken) {
        await this.initializeCSRFToken();
      }

      return this.fetchWithCredentials('/auth/session/sso/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
  };

  saml = {
    authorization: async (params?: { redirect_uri?: string }) => {
      const queryString =
        params && params.redirect_uri
          ? `?${new URLSearchParams({ redirect_uri: params.redirect_uri }).toString()}`
          : '';

      return this.fetchWithCredentials(`/auth/saml/authorization${queryString}`);
    },

    login: async (payload: { login_ticket: string; relay_state: string }) => {
      if (!this.csrfToken) {
        await this.initializeCSRFToken();
      }

      return this.fetchWithCredentials('/auth/session/saml/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
  };

  // 既存のAPIクライアントとの互換性のためのプロキシメソッド
  get = async (url: string) => {
    return this.fetchWithCredentials(url);
  };

  post = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  put = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  patch = async (url: string, data?: unknown) => {
    return this.fetchWithCredentials(url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  };

  delete = async (url: string) => {
    return this.fetchWithCredentials(url, {
      method: 'DELETE',
    });
  };
}

// シングルトンインスタンス
export const cookieApiClient = new CookieApiClient();

// Cookie対応のAPIメソッド
export const cookieApi = {
  // 認証API（FastAPI Cookie session contract）
  auth: cookieApiClient.auth,
  sso: cookieApiClient.sso,
  saml: cookieApiClient.saml,

  // その他のAPI（直接バックエンド、Cookie自動送信）
  get: cookieApiClient.get,
  post: cookieApiClient.post,
  put: cookieApiClient.put,
  patch: cookieApiClient.patch,
  delete: cookieApiClient.delete,
};

// Todo API methods (Cookie版)
export const cookieTodoApi = {
  getAll: (params?: { skip?: number; limit?: number }) => {
    const queryString = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()}` : '';
    return cookieApiClient.fetchWithCredentials(`/todos${queryString}`, {
      method: 'GET',
    });
  },

  getById: (id: number) => cookieApiClient.fetchWithCredentials(`/todos/${id}`, {
    method: 'GET',
  }),

  create: async (data: { title: string; description?: string }) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials('/todos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: number, data: { title?: string; description?: string; is_completed?: boolean }) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials(`/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: number) => {
    // CSRFトークンを確実に取得
    if (!cookieApiClient.csrfToken) {
      await cookieApiClient.initializeCSRFToken();
    }

    return cookieApiClient.fetchWithCredentials(`/todos/${id}`, {
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
