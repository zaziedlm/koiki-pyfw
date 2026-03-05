-- Temporary table for migration-target style SSO link storage.
-- This does NOT replace framework standard "users" table.
-- It is intended for E2E verification with SSO_LINK_BACKEND=user_table.

CREATE TABLE IF NOT EXISTS "user" (
    user_id INT PRIMARY KEY,
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    role_id INT,
    user_sso_provider VARCHAR(50),
    user_sso_subject VARCHAR(255),
    user_is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_sso_provider_subject_active
ON "user"(user_sso_provider, user_sso_subject)
WHERE is_deleted = FALSE
  AND user_sso_provider IS NOT NULL
  AND user_sso_subject IS NOT NULL;

