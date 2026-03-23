# Framework Patterns Reference

Use this reference when the `koiki-libkoiki-feature-work` skill needs a compact reminder of framework-side implementation patterns.

## Focus Areas

- shared layer placement under `libkoiki/`
- API -> Service -> Repository -> Model/Schema flow
- DI and transaction consistency
- avoiding project-specific assumptions in shared code

## Source Material

Primary source material comes from:

- `docs/design_kkfw_0.6.0.md` sections on config, DI, models, schemas, repositories, and services
- current `libkoiki/` implementation
- shared agent docs in `docs/agent/`

## Practical Reminder

Before extending `libkoiki/`, confirm both of these:

- the behavior is reusable beyond the current project
- `app/` can consume the resulting contract without project-specific workarounds
