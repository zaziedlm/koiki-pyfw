export const config = {
  api: {
    // Backend API configuration
    url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    prefix: process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1',
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
    
    // Frontend proxy configuration  
    proxyPrefix: '/api/backend',
  },
  app: {
    name: process.env.NEXT_PUBLIC_APP_NAME || 'KOIKI Task Manager',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  },
  auth: {
    tokenKey: process.env.NEXT_PUBLIC_ACCESS_TOKEN_NAME || 'koiki_access_token',
    refreshTokenKey: process.env.NEXT_PUBLIC_REFRESH_TOKEN_NAME || 'koiki_refresh_token',
    tokenExpiration: 30 * 60 * 1000, // 30 minutes in milliseconds
    cookieAuth: {
      enabled: process.env.NEXT_PUBLIC_COOKIE_AUTH_ENABLED === 'true',
      csrfProtection: true,
      sameSite: (process.env.NEXT_PUBLIC_COOKIE_SAMESITE as 'lax' | 'strict' | 'none') || 'lax',
      secure: process.env.NEXT_PUBLIC_COOKIE_SECURE === 'true' || process.env.NODE_ENV === 'production',
    },
  },
  sso: {
    redirectUri: process.env.NEXT_PUBLIC_SSO_REDIRECT_URI || '/sso/callback',
  },
  saml: {
    redirectUri: process.env.NEXT_PUBLIC_SAML_REDIRECT_URI || '/auth/saml/callback',
  },
} as const;
