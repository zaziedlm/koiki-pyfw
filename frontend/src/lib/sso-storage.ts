const STORAGE_KEY = 'koiki_sso_context';

export interface StoredSsoContext {
  state: string;
  nonce: string;
  codeVerifier: string;
  redirectUri: string;
  expiresAt?: string;
  createdAt: string;
}

export function saveSsoContext(context: StoredSsoContext): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(context));
  } catch (error) {
    console.error('[sso-storage] failed to save context', error);
  }
}

export function loadSsoContext(): StoredSsoContext | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredSsoContext;
  } catch (error) {
    console.error('[sso-storage] failed to load context', error);
    return null;
  }
}

export function clearSsoContext(): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('[sso-storage] failed to clear context', error);
  }
}
