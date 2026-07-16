function optionalEnvValue(key: string): string | undefined {
  const viteValue = import.meta.env[key];
  if (viteValue !== undefined) {
    return viteValue;
  }
  return undefined;
}

function envValue(key: string, fallback: string): string {
  return optionalEnvValue(key) ?? fallback;
}

const apiUrl = envValue('VITE_API_URL', 'http://localhost:8000');
const apiPrefix = envValue('VITE_API_PREFIX', '/api/v1');

function alignLocalhostWithBrowserHost(value: string): string {
  if (typeof window === 'undefined') {
    return value;
  }

  const browserHost = window.location.hostname;
  if (browserHost !== 'localhost' && browserHost !== '127.0.0.1') {
    return value;
  }

  try {
    const url = new URL(value);
    if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
      url.hostname = browserHost;
      return url.toString().replace(/\/$/, '');
    }
  } catch {
    // Relative API base URLs should be left unchanged.
  }

  return value;
}

const apiBaseUrl = alignLocalhostWithBrowserHost(
  envValue('VITE_API_BASE_URL', `${apiUrl}${apiPrefix}`)
);

export const config = {
  api: {
    // Backend API configuration
    url: apiUrl,
    prefix: apiPrefix,
    baseUrl: apiBaseUrl,
  },
  app: {
    name: envValue('VITE_APP_NAME', 'KOIKI Task Manager'),
    version: envValue('VITE_APP_VERSION', '1.0.0'),
  },
  sso: {
    redirectUri: envValue('VITE_SSO_REDIRECT_URI', '/sso/callback'),
  },
  saml: {
    redirectUri: envValue('VITE_SAML_REDIRECT_URI', '/auth/saml/callback'),
  },
} as const;
