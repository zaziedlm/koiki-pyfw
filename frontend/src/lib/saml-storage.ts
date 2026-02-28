const SESSION_STORAGE_KEY = 'koiki_saml_context';
const LOCAL_STORAGE_KEY = 'koiki_saml_context_backup';

export interface StoredSamlContext {
  relayState: string;
  redirectUri: string;
  expiresAt?: string;
  createdAt: string;
}

export function saveSamlContext(context: StoredSamlContext): void {
  if (typeof window === 'undefined') return;
  const serialized = JSON.stringify(context);
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, serialized);
  } catch (error) {
    console.error('[saml-storage] failed to save context', error);
  }
  try {
    window.localStorage.setItem(LOCAL_STORAGE_KEY, serialized);
  } catch (error) {
    console.error('[saml-storage] failed to save backup context', error);
  }
}

export function loadSamlContext(): StoredSamlContext | null {
  if (typeof window === 'undefined') return null;
  try {
    const primary = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (primary) {
      return JSON.parse(primary) as StoredSamlContext;
    }

    const backup = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!backup) return null;

    // Safari 等で sessionStorage が失われた場合に復元する
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, backup);
    return JSON.parse(backup) as StoredSamlContext;
  } catch (error) {
    console.error('[saml-storage] failed to load context', error);
    return null;
  }
}

export function clearSamlContext(): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
  } catch (error) {
    console.error('[saml-storage] failed to clear context', error);
  }
  try {
    window.localStorage.removeItem(LOCAL_STORAGE_KEY);
  } catch (error) {
    console.error('[saml-storage] failed to clear backup context', error);
  }
}
