/**
 * JWT トークン関連のユーティリティ関数
 */

interface JWTPayload {
  exp?: number;
  sub?: string;
  iat?: number;
}

/**
 * JWTトークンをデコードする（署名検証なし）
 */
export function decodeToken(token: string): JWTPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = parts[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded;
  } catch (error) {
    console.error('Token decode error:', error);
    return null;
  }
}

/**
 * トークンの有効期限をチェックする
 * @param token JWT トークン
 * @param bufferSeconds 有効期限前の猶予時間（秒）
 * @returns トークンが有効かどうか
 */
export function isTokenExpired(token: string | null, bufferSeconds: number = 60): boolean {
  if (!token) {
    return true;
  }

  const payload = decodeToken(token);
  if (!payload || !payload.exp) {
    return true;
  }

  const now = Math.floor(Date.now() / 1000);
  const expiration = payload.exp - bufferSeconds; // 猶予時間を考慮
  
  return now >= expiration;
}

/**
 * トークンの残り有効時間を取得する（秒）
 */
export function getTokenRemainingTime(token: string | null): number {
  if (!token) {
    return 0;
  }

  const payload = decodeToken(token);
  if (!payload || !payload.exp) {
    return 0;
  }

  const now = Math.floor(Date.now() / 1000);
  const remaining = payload.exp - now;
  
  return Math.max(0, remaining);
}

/**
 * トークンが指定時間内に期限切れになるかどうか
 */
export function willTokenExpireSoon(token: string | null, thresholdSeconds: number = 300): boolean {
  if (!token) {
    return true;
  }

  const remainingTime = getTokenRemainingTime(token);
  return remainingTime <= thresholdSeconds;
}