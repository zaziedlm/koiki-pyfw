function optionalEnvValue(key: string): string | undefined {
  const viteValue = import.meta.env[key];
  if (viteValue !== undefined) {
    return viteValue;
  }
  if (typeof process !== 'undefined') {
    return process.env[key];
  }
  return undefined;
}

function publicEnvValue(viteKey: string, nextKey: string, fallback: string): string {
  return optionalEnvValue(viteKey) ?? optionalEnvValue(nextKey) ?? fallback;
}

const apiUrl = publicEnvValue('VITE_API_URL', 'NEXT_PUBLIC_API_URL', 'http://localhost:8000');
const apiPrefix = publicEnvValue('VITE_API_PREFIX', 'NEXT_PUBLIC_API_PREFIX', '/api/v1');
const apiBaseUrl = publicEnvValue(
  'VITE_API_BASE_URL',
  'NEXT_PUBLIC_API_BASE_URL',
  `${apiUrl}${apiPrefix}`,
);

export const config = {
  api: {
    // Backend API configuration
    url: apiUrl,
    prefix: apiPrefix,
    baseUrl: apiBaseUrl,
    // Frontend proxy configuration  
    proxyPrefix: '/api/backend',
  },
  app: {
    name: publicEnvValue('VITE_APP_NAME', 'NEXT_PUBLIC_APP_NAME', 'KOIKI Task Manager'),
    version: publicEnvValue('VITE_APP_VERSION', 'NEXT_PUBLIC_APP_VERSION', '1.0.0'),
  },
  auth: {
    tokenKey: publicEnvValue('VITE_ACCESS_TOKEN_NAME', 'NEXT_PUBLIC_ACCESS_TOKEN_NAME', 'koiki_access_token'),
    refreshTokenKey: publicEnvValue('VITE_REFRESH_TOKEN_NAME', 'NEXT_PUBLIC_REFRESH_TOKEN_NAME', 'koiki_refresh_token'),
    tokenExpiration: 30 * 60 * 1000, // 30 minutes in milliseconds
    cookieAuth: {
      enabled: publicEnvValue('VITE_COOKIE_AUTH_ENABLED', 'NEXT_PUBLIC_COOKIE_AUTH_ENABLED', 'false') === 'true',
      csrfProtection: true,
      sameSite: (optionalEnvValue('VITE_COOKIE_SAMESITE') ??
        optionalEnvValue('NEXT_PUBLIC_COOKIE_SAMESITE') ??
        'lax') as 'lax' | 'strict' | 'none',
      secure:
        publicEnvValue('VITE_COOKIE_SECURE', 'NEXT_PUBLIC_COOKIE_SECURE', 'false') === 'true' ||
        (import.meta.env.PROD &&
          publicEnvValue('VITE_COOKIE_SECURE', 'NEXT_PUBLIC_COOKIE_SECURE', 'false') !== 'false'),
    },
  },
  sso: {
    redirectUri: publicEnvValue('VITE_SSO_REDIRECT_URI', 'NEXT_PUBLIC_SSO_REDIRECT_URI', '/sso/callback'),
  },
  saml: {
    redirectUri: publicEnvValue('VITE_SAML_REDIRECT_URI', 'NEXT_PUBLIC_SAML_REDIRECT_URI', '/auth/saml/callback'),
  },
} as const;
