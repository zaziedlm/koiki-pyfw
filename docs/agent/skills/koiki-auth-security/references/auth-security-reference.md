# Auth and Security Reference

Use this reference when the `koiki-auth-security` skill needs a compact reminder of the current security split.

## Focus Areas

- shared auth and token behavior in `libkoiki/`
- application-specific SSO and SAML behavior in `app/`
- validation, logging, and audit expectations
- request-flow review before editing security-sensitive paths

## Source Material

Primary source material comes from:

- `docs/design_kkfw_0.6.0.md` sections on auth, security, logging, monitoring, and RBAC
- current auth, SSO, and SAML implementation under `libkoiki/` and `app/`
- shared agent docs in `docs/agent/`

## Practical Reminder

Security-sensitive changes should be reviewed as full flows, not isolated file edits.
