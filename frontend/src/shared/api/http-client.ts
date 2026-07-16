import { config as appConfig } from '@/lib/config';

const CSRF_COOKIE_NAME = 'koiki_csrf_token';

interface ApiErrorPayload {
  message?: string;
  detail?: string | { code?: string; message?: string; [key: string]: unknown };
  code?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor({
    status,
    message,
    code,
    details,
  }: {
    status: number;
    message: string;
    code?: string;
    details?: unknown;
  }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

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

async function parseJsonResponse(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  const payload = await parseJsonResponse(response).catch(() => null) as ApiErrorPayload | string | null;
  const detail = typeof payload === 'object' && payload !== null ? payload.detail : undefined;
  const detailMessage = typeof detail === 'object' && detail !== null ? detail.message : detail;
  const detailCode = typeof detail === 'object' && detail !== null ? detail.code : undefined;
  const message =
    (typeof payload === 'object' && payload !== null ? payload.message : undefined) ||
    detailMessage ||
    response.statusText ||
    `Request failed (${response.status})`;
  const code =
    (typeof payload === 'object' && payload !== null ? payload.code : undefined) ||
    detailCode;

  return new ApiError({
    status: response.status,
    message,
    code,
    details: payload,
  });
}

export class CookieApiClient {
  public csrfToken: string | null = null;
  private csrfInitPromise: Promise<void> | null = null;
  private readonly baseUrl = normalizeBaseUrl(appConfig.api.baseUrl);

  constructor() {
    void this.initializeCSRFToken();
  }

  private apiUrl(path: string): string {
    if (/^https?:\/\//i.test(path)) {
      return path;
    }

    return `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  }

  private async fetchCSRFToken(): Promise<void> {
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
      } else if (isDev()) {
        console.error('[CSRF] init failed http', response.status);
      }
    } catch {
      if (isDev()) {
        console.error('[CSRF] init error');
      }
    }
  }

  public async initializeCSRFToken(): Promise<void> {
    if (!this.csrfInitPromise) {
      this.csrfInitPromise = this.fetchCSRFToken().finally(() => {
        this.csrfInitPromise = null;
      });
    }

    return this.csrfInitPromise;
  }

  private async refreshCSRFToken() {
    await this.initializeCSRFToken();
  }

  private getHeaders(isFormData = false): HeadersInit {
    const headers: HeadersInit = {};

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    let csrfToken = this.csrfToken;

    if (!csrfToken && typeof document !== 'undefined') {
      const cookieValue = readCookie(CSRF_COOKIE_NAME);

      if (cookieValue) {
        csrfToken = cookieValue;
        this.csrfToken = cookieValue;
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

  public async fetchWithCredentials(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const requestUrl = this.apiUrl(url);
    const method = options.method?.toUpperCase() ?? 'GET';

    if (!this.csrfToken && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      await this.initializeCSRFToken();
    }

    const response = await fetch(requestUrl, {
      ...options,
      credentials: 'include',
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (response.status === 403) {
      const errorData = await response.clone().json().catch(() => null);
      const errorCode = errorData?.code ?? errorData?.detail?.code;
      if (errorCode === 'CSRF_TOKEN_INVALID') {
        await this.refreshCSRFToken();
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

  public async requestJson<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await this.fetchWithCredentials(url, options);

    if (!response.ok) {
      throw await toApiError(response);
    }

    return parseJsonResponse(response) as Promise<T>;
  }

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

export const cookieApiClient = new CookieApiClient();
