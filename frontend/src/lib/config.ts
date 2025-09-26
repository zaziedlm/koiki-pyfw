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
    tokenKey: 'koiki_access_token',
    refreshTokenKey: 'koiki_refresh_token',
    tokenExpiration: 30 * 60 * 1000, // 30 minutes in milliseconds
    
    // Cookie認証設定
      cookieAuth: {
        enabled: process.env.NEXT_PUBLIC_COOKIE_AUTH_ENABLED === 'true' || true, // デフォルトで有効
        csrfProtection: true,
      },
  },
  sso: {
    redirectUri: process.env.NEXT_PUBLIC_SSO_REDIRECT_URI || '/sso/callback',
  },
} as const;
