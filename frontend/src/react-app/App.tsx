import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ApiError, api, Todo, User } from './api';

const ssoStorageKey = 'koiki.sso.context';
const samlStorageKey = 'koiki.saml.context';

function navigate(path: string): void {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : '処理に失敗しました。';
}

function randomVerifier(): string {
  const values = new Uint8Array(32);
  crypto.getRandomValues(values);
  return btoa(String.fromCharCode(...values)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function challengeFor(verifier: string): Promise<string> {
  const bytes = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return btoa(String.fromCharCode(...new Uint8Array(digest))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

export function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const loadSession = async (): Promise<User | null> => {
    try {
      const current = await api.me();
      setUser(current);
      return current;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        try {
          await api.refresh();
          const current = await api.me();
          setUser(current);
          return current;
        } catch {
          setUser(null);
          return null;
        }
      }
      setUser(null);
      return null;
    }
  };

  useEffect(() => {
    loadSession().finally(() => setLoading(false));
  }, []);

  const session = useMemo(() => ({ user, loading, reload: loadSession }), [user, loading]);

  if (path === '/sso/callback') return <SsoCallback session={session} />;
  if (path === '/auth/saml/callback') return <SamlCallback session={session} />;
  if (path === '/auth/login') return <Login session={session} />;
  if (path === '/dashboard' || path === '/dashboard/tasks') {
    return <Dashboard session={session} />;
  }
  return <Home user={user} />;
}

type Session = { user: User | null; loading: boolean; reload: () => Promise<User | null> };

function Home({ user }: { user: User | null }) {
  return <main className="centered"><section className="card"><h1>KOIKI Task Manager</h1><p>React と FastAPI の最小構成サンプルです。</p><button onClick={() => navigate(user ? '/dashboard' : '/auth/login')}>{user ? 'Todo を開く' : 'ログイン'}</button></section></main>;
}

function Login({ session }: { session: Session }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (!session.loading && session.user) navigate('/dashboard'); }, [session.loading, session.user]);

  const passwordLogin = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null);
    try { await api.login(email, password); await session.reload(); navigate('/dashboard'); }
    catch (reason) { setError(messageOf(reason)); }
    finally { setBusy(false); }
  };

  const startSso = async () => {
    setBusy(true); setError(null);
    try {
      const redirectUri = new URL('/sso/callback', window.location.origin).toString();
      const context = await api.ssoAuthorization(redirectUri);
      const verifier = randomVerifier();
      sessionStorage.setItem(ssoStorageKey, JSON.stringify({ verifier, state: context.state, nonce: context.nonce, redirectUri: context.redirect_uri, expiresAt: context.expires_at }));
      const separator = context.authorization_base_url.includes('?') ? '&' : '?';
      window.location.assign(`${context.authorization_base_url}${separator}code_challenge=${encodeURIComponent(await challengeFor(verifier))}&code_challenge_method=${encodeURIComponent(context.code_challenge_method || 'S256')}`);
    } catch (reason) { setError(messageOf(reason)); setBusy(false); }
  };

  const startSaml = async () => {
    setBusy(true); setError(null);
    try {
      const redirectUri = new URL('/auth/saml/callback', window.location.origin).toString();
      const context = await api.samlAuthorization(redirectUri);
      sessionStorage.setItem(samlStorageKey, JSON.stringify({ relayState: context.relay_state, expiresAt: context.expires_at }));
      window.location.assign(context.redirect_url || context.sso_url);
    } catch (reason) { setError(messageOf(reason)); setBusy(false); }
  };

  return <main className="centered"><section className="card login-card"><h1>ログイン</h1><form onSubmit={passwordLogin}><label>メールアドレス<input autoComplete="username" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label>パスワード<input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label><button disabled={busy} type="submit">{busy ? '処理中…' : 'パスワードでログイン'}</button></form><div className="button-row"><button disabled={busy} type="button" onClick={startSso}>SSO ログイン</button><button disabled={busy} type="button" onClick={startSaml}>SAML ログイン</button></div>{error && <p className="error" role="alert">{error}</p>}</section></main>;
}

function SsoCallback({ session }: { session: Session }) {
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const finish = async () => {
      const params = new URLSearchParams(window.location.search);
      const stored = JSON.parse(sessionStorage.getItem(ssoStorageKey) || '{}') as Record<string, string>;
      const code = params.get('code'); const state = params.get('state');
      if (!code || !state || !stored.verifier || stored.state !== state) throw new Error('SSO の state 検証に失敗しました。');
      if (stored.expiresAt && Date.now() > new Date(stored.expiresAt).getTime()) throw new Error('SSO 認証状態の有効期限が切れました。');
      await api.ssoLogin({ authorization_code: code, code_verifier: stored.verifier, state, nonce: stored.nonce, redirect_uri: stored.redirectUri });
      sessionStorage.removeItem(ssoStorageKey); await session.reload(); navigate('/dashboard');
    };
    finish().catch((reason) => setError(messageOf(reason)));
  }, []);
  return <CallbackStatus title="SSO ログインを完了しています…" error={error} />;
}

function SamlCallback({ session }: { session: Session }) {
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const finish = async () => {
      const params = new URLSearchParams(window.location.search);
      const stored = JSON.parse(sessionStorage.getItem(samlStorageKey) || '{}') as Record<string, string>;
      const ticket = params.get('saml_ticket'); const relayState = params.get('relay_state') || params.get('RelayState') || stored.relayState;
      if (!ticket || !relayState) throw new Error('SAML ログインチケットまたは RelayState がありません。');
      if (stored.relayState && stored.relayState !== relayState) throw new Error('SAML RelayState の検証に失敗しました。');
      if (stored.expiresAt && Date.now() > new Date(stored.expiresAt).getTime()) throw new Error('SAML 認証状態の有効期限が切れました。');
      await api.samlLogin({ login_ticket: ticket, relay_state: relayState });
      sessionStorage.removeItem(samlStorageKey); await session.reload(); navigate('/dashboard');
    };
    finish().catch((reason) => setError(messageOf(reason)));
  }, []);
  return <CallbackStatus title="SAML ログインを完了しています…" error={error} />;
}

function CallbackStatus({ title, error }: { title: string; error: string | null }) {
  return <main className="centered"><section className="card"><h1>{error ? 'ログインに失敗しました' : title}</h1>{error ? <><p className="error">{error}</p><button onClick={() => navigate('/auth/login')}>ログイン画面へ戻る</button></> : <p>認証結果を確認しています。</p>}</section></main>;
}

function Dashboard({ session }: { session: Session }) {
  const [todos, setTodos] = useState<Todo[]>([]); const [title, setTitle] = useState(''); const [error, setError] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const refreshTodos = async () => { try { setTodos(await api.todos.list()); } catch (reason) { setError(messageOf(reason)); } };
  useEffect(() => { if (!session.loading && !session.user) navigate('/auth/login'); else if (session.user) void refreshTodos(); }, [session.loading, session.user]);
  const addTodo = async (event: FormEvent) => { event.preventDefault(); if (!title.trim()) return; setBusy(true); try { await api.todos.create(title.trim()); setTitle(''); await refreshTodos(); } catch (reason) { setError(messageOf(reason)); } finally { setBusy(false); } };
  const logout = async () => { try { await api.logout(); } finally { await session.reload(); navigate('/auth/login'); } };
  if (session.loading || !session.user) return <main className="centered">読み込み中…</main>;
  return <main className="page"><header><div><h1>Todo 管理</h1><p>{session.user.email}</p></div><button onClick={logout}>ログアウト</button></header><section className="card"><form className="inline-form" onSubmit={addTodo}><input placeholder="新しい Todo" value={title} onChange={(e) => setTitle(e.target.value)} /><button disabled={busy}>追加</button></form>{error && <p className="error">{error}</p>}<ul className="todo-list">{todos.map((todo) => <li key={todo.id}><label><input type="checkbox" checked={todo.is_completed} onChange={async () => { try { await api.todos.update(todo.id, { is_completed: !todo.is_completed }); await refreshTodos(); } catch (reason) { setError(messageOf(reason)); } }} /><span className={todo.is_completed ? 'completed' : ''}>{todo.title}</span></label><button aria-label={`${todo.title} を削除`} onClick={async () => { try { await api.todos.remove(todo.id); await refreshTodos(); } catch (reason) { setError(messageOf(reason)); } }}>削除</button></li>)}</ul>{todos.length === 0 && <p>Todo はまだありません。</p>}</section></main>;
}
