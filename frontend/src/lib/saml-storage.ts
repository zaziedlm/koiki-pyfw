const STORAGE_KEY = 'koiki_saml_context';

export interface StoredSamlContext {
  relayState: string;
  redirectUri: string;
  expiresAt?: string;
  createdAt: string;
}

export function saveSamlContext(context: StoredSamlContext): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(context));
  } catch (error) {
    console.error('[saml-storage] failed to save context', error);
  }
}

export function loadSamlContext(): StoredSamlContext | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredSamlContext;
  } catch (error) {
    console.error('[saml-storage] failed to load context', error);
    return null;
  }
}

export function clearSamlContext(): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('[saml-storage] failed to clear context', error);
  }
}
