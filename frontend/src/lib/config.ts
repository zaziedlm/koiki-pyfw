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

function envValue(key: string, fallback: string): string {
  return optionalEnvValue(key) ?? fallback;
}

export const config = {
  api: {
    // Backend API configuration
    url: envValue('NEXT_PUBLIC_API_URL', 'http://localhost:8000'),
    prefix: envValue('NEXT_PUBLIC_API_PREFIX', '/api/v1'),
    // baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',

    // For AWS ECS,Flexible base URL construction to support different deployment scenarios
    baseUrl: optionalEnvValue('BACKEND_API_URL')
      ? `${optionalEnvValue('BACKEND_API_URL')}${envValue('BACKEND_API_PREFIX', '/api/v1')}`
      : envValue('NEXT_PUBLIC_API_BASE_URL', 'http://localhost:8000/api/v1'),
    // Frontend proxy configuration  
    proxyPrefix: '/api/backend',
  },
  app: {
    name: envValue('NEXT_PUBLIC_APP_NAME', 'KOIKI Task Manager'),
    version: envValue('NEXT_PUBLIC_APP_VERSION', '1.0.0'),
  },
  auth: {
    tokenKey: envValue('NEXT_PUBLIC_ACCESS_TOKEN_NAME', 'koiki_access_token'),
    refreshTokenKey: envValue('NEXT_PUBLIC_REFRESH_TOKEN_NAME', 'koiki_refresh_token'),
    tokenExpiration: 30 * 60 * 1000, // 30 minutes in milliseconds
    cookieAuth: {
      enabled: optionalEnvValue('NEXT_PUBLIC_COOKIE_AUTH_ENABLED') === 'true',
      csrfProtection: true,
      sameSite: (optionalEnvValue('NEXT_PUBLIC_COOKIE_SAMESITE') as 'lax' | 'strict' | 'none') || 'lax',
      secure:
        optionalEnvValue('NEXT_PUBLIC_COOKIE_SECURE') === 'true' ||
        (import.meta.env.PROD && optionalEnvValue('NEXT_PUBLIC_COOKIE_SECURE') !== 'false'),
    },
  },
  sso: {
    redirectUri: envValue('NEXT_PUBLIC_SSO_REDIRECT_URI', '/sso/callback'),
  },
  saml: {
    redirectUri: envValue('NEXT_PUBLIC_SAML_REDIRECT_URI', '/auth/saml/callback'),
  },
} as const;
