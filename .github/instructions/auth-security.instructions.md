---
applyTo: "components/libkoiki/src/libkoiki/core/security*.py,components/libkoiki/src/libkoiki/core/middleware.py,components/libkoiki/src/libkoiki/api/v1/endpoints/auth*.py,components/libkoiki/src/libkoiki/api/v1/endpoints/security_monitor.py,components/libkoiki/src/libkoiki/services/auth_service.py,components/libkoiki/src/libkoiki/services/login_security_service.py,components/libkoiki/src/libkoiki/services/password_reset_service.py,components/libkoiki/src/libkoiki/repositories/refresh_token_repository.py,components/libkoiki/src/libkoiki/repositories/password_reset_repository.py,components/libkoiki/src/libkoiki/repositories/login_attempt_repository.py,components/libkoiki/src/libkoiki/models/refresh_token.py,components/libkoiki/src/libkoiki/models/password_reset.py,components/libkoiki/src/libkoiki/models/login_attempt.py,components/libkoiki/src/libkoiki/schemas/refresh_token.py,components/koiki_ref_app/src/koiki_ref_app/services/sso_service.py,components/koiki_ref_app/src/koiki_ref_app/services/saml*.py,components/koiki_ref_app/src/koiki_ref_app/repositories/*sso*.py,components/koiki_ref_app/src/koiki_ref_app/repositories/*saml*.py,components/koiki_ref_app/src/koiki_ref_app/models/*sso*.py,components/koiki_ref_app/src/koiki_ref_app/models/*saml*.py,components/koiki_ref_app/src/koiki_ref_app/schemas/sso.py,components/koiki_ref_app/src/koiki_ref_app/schemas/saml.py,components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py,components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/saml_auth.py,components/koiki_ref_app/src/koiki_ref_app/core/sso_config.py,components/koiki_ref_app/src/koiki_ref_app/core/saml_config.py,components/koiki_ref_app/tests/unit/app/services/test_sso_service.py,components/koiki_ref_app/tests/unit/app/services/test_saml_service.py,components/koiki_ref_app/tests/unit/app/repositories/test_user_table_sso_repository.py"
---

# Auth and Security Instructions

This scope is security-sensitive.

- trace the full auth or security flow before editing
- keep shared token, permission, password, audit, and rate-limit behavior in `components/libkoiki`
- keep application-specific SSO and SAML integration behavior in `components/koiki_ref_app`
- preserve failure behavior unless there is an explicit reason to change it
- update validation, logging, and tests together

Do not rely on frontend behavior alone for authorization or access control.
