---
applyTo: "libkoiki/core/security*.py,libkoiki/core/middleware.py,libkoiki/api/v1/endpoints/auth*.py,libkoiki/api/v1/endpoints/security_monitor.py,libkoiki/services/auth_service.py,libkoiki/services/login_security_service.py,libkoiki/services/password_reset_service.py,libkoiki/repositories/refresh_token_repository.py,libkoiki/repositories/password_reset_repository.py,libkoiki/repositories/login_attempt_repository.py,libkoiki/models/refresh_token.py,libkoiki/models/password_reset.py,libkoiki/models/login_attempt.py,libkoiki/schemas/refresh_token.py,app/services/sso_service.py,app/services/saml*.py,app/repositories/*sso*.py,app/repositories/*saml*.py,app/models/*sso*.py,app/models/*saml*.py,app/schemas/sso.py,app/schemas/saml.py,app/api/v1/endpoints/sso_auth.py,app/api/v1/endpoints/saml_auth.py,app/core/sso_config.py,app/core/saml_config.py,tests/unit/app/services/test_sso_service.py,tests/unit/app/services/test_saml_service.py,tests/unit/app/repositories/test_user_table_sso_repository.py"
---

# Auth and Security Instructions

This scope is security-sensitive.

- trace the full auth or security flow before editing
- keep shared token, permission, password, audit, and rate-limit behavior in `libkoiki/`
- keep application-specific SSO and SAML integration behavior in `app/`
- preserve failure behavior unless there is an explicit reason to change it
- update validation, logging, and tests together

Do not rely on frontend behavior alone for authorization or access control.
