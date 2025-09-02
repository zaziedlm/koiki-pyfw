// Security related types for admin monitoring

export interface SecurityMetrics {
  total_login_attempts: number;
  successful_logins: number;
  failed_logins: number;
  unique_users: number;
  login_success_rate: number;
  recent_failures: number;
}

export interface AuthenticationMetrics {
  login_attempts: {
    total: number;
    successful: number;
    failed: number;
    success_rate: number;
  };
  user_activity: {
    active_users: number;
    new_registrations: number;
  };
  security_events: {
    password_changes: number;
    password_resets: number;
    token_refreshes: number;
  };
}

export interface SecuritySummary {
  overview: {
    total_users: number;
    active_sessions: number;
    security_score: number;
    last_updated: string;
  };
  threats: {
    blocked_attempts: number;
    suspicious_activities: number;
    failed_login_rate: number;
  };
  system_health: {
    status: "healthy" | "warning" | "critical";
    uptime: number;
    response_time: number;
  };
}

export interface SecurityHealth {
  status: "healthy" | "degraded" | "down";
  checks: {
    database: boolean;
    redis: boolean;
    authentication: boolean;
    rate_limiting: boolean;
  };
  timestamp: string;
}

export interface LoginAttempt {
  id: number;
  user_id?: number;
  username: string;
  ip_address: string;
  success: boolean;
  failure_reason?: string;
  created_at: string;
}

// Frontend-specific security types
export interface SecurityState {
  metrics: SecurityMetrics | null;
  authMetrics: AuthenticationMetrics | null;
  summary: SecuritySummary | null;
  health: SecurityHealth | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}