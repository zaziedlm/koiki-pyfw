# App Extension Patterns Reference

Use this reference when the `koiki-app-feature-work` skill needs a compact reminder of application-side implementation patterns.

## Focus Areas

- project-specific API and service wiring under `components/koiki_ref_app/`
- reuse of `components/libkoiki/` capabilities before adding framework changes
- current `components/koiki_ref_app/src/koiki_ref_app/api/v1/` and `components/koiki_ref_app/src/koiki_ref_app/main.py` composition style
- business-specific SSO, SAML, and domain logic placement

## Source Material

Primary source material comes from:

- `docs/design_kkfw_0.6.0.md` sections on application implementation examples
- current `components/koiki_ref_app/` implementation
- shared agent docs in `docs/agent/`

## Practical Reminder

Before changing `components/koiki_ref_app/`, confirm both of these:

- the behavior is actually project-specific
- the feature cannot be solved cleanly by composing existing `components/libkoiki/` behavior alone
