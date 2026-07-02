export type User = {
  id: number;
  email: string;
  username?: string;
  full_name?: string | null;
};

export type Todo = {
  id: number;
  title: string;
  description?: string | null;
  is_completed: boolean;
  created_at?: string;
  updated_at?: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const csrfCookieName = 'koiki_csrf_token';
const csrfHeaderName = 'x-csrf-token';
const browserSessionHeader = 'x-koiki-browser-session';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

function readCookie(name: string): string | undefined {
  return document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

async function parseError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null) as
    | { detail?: string | { message?: string }; message?: string }
    | null;
  const detail = typeof payload?.detail === 'string'
    ? payload.detail
    : payload?.detail?.message || payload?.message || `Request failed (${response.status})`;
  return new ApiError(response.status, detail);
}

async function issueCsrfToken(): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/auth/browser/csrf`, { credentials: 'include' });
  if (!response.ok) throw await parseError(response);
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const method = (init.method || 'GET').toUpperCase();
  const unsafe = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  if (unsafe && !readCookie(csrfCookieName)) await issueCsrfToken();

  const headers = new Headers(init.headers);
  headers.set(browserSessionHeader, '1');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (unsafe) {
    const csrfToken = readCookie(csrfCookieName);
    if (csrfToken) headers.set(csrfHeaderName, decodeURIComponent(csrfToken));
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  });

  if (response.status === 403 && retry) {
    const payload = await response.clone().json().catch(() => null) as { code?: string } | null;
    if (payload?.code === 'CSRF_TOKEN_INVALID') {
      await issueCsrfToken();
      return request<T>(path, init, false);
    }
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  csrf: () => issueCsrfToken(),
  me: () => request<User>('/auth/browser/me'),
  login: (email: string, password: string) => request('/auth/browser/login', {
    method: 'POST', body: JSON.stringify({ email, password }),
  }),
  refresh: () => request('/auth/browser/refresh', { method: 'POST' }),
  logout: () => request('/auth/browser/logout', { method: 'POST' }),
  todos: {
    list: () => request<Todo[]>('/auth/browser/todos'),
    create: (title: string, description?: string) => request<Todo>('/auth/browser/todos', {
      method: 'POST', body: JSON.stringify({ title, description: description || undefined }),
    }),
    update: (id: number, patch: Partial<Pick<Todo, 'title' | 'description' | 'is_completed'>>) => request<Todo>(`/auth/browser/todos/${id}`, {
      method: 'PUT', body: JSON.stringify(patch),
    }),
    remove: (id: number) => request<void>(`/auth/browser/todos/${id}`, { method: 'DELETE' }),
  },
  ssoAuthorization: (redirectUri: string) => request<{
    authorization_base_url: string;
    state: string;
    nonce: string;
    redirect_uri: string;
    expires_at?: string;
    code_challenge_method?: string;
  }>(`/auth/sso/authorization?redirect_uri=${encodeURIComponent(redirectUri)}`),
  ssoLogin: (payload: Record<string, string>) => request('/auth/browser/sso/login', {
    method: 'POST', body: JSON.stringify(payload),
  }),
  samlAuthorization: (redirectUri: string) => request<{
    redirect_url?: string;
    sso_url: string;
    relay_state: string;
    expires_at?: string;
  }>(`/auth/saml/authorization?redirect_uri=${encodeURIComponent(redirectUri)}`),
  samlLogin: (payload: { login_ticket: string; relay_state: string }) => request('/auth/browser/saml/login', {
    method: 'POST', body: JSON.stringify(payload),
  }),
};
