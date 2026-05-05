# プロジェクト構造

## ディレクトリ概要

```
├── components/
│   ├── libkoiki/              # reusable framework package
│   │   ├── src/libkoiki/      # framework source
│   │   └── tests/             # framework tests
│   └── koiki_ref_app/         # reference application package
│       ├── src/koiki_ref_app/ # reference app source
│       └── tests/             # reference app tests
├── app/                       # compatibility wrapper
├── frontend/                  # Next.js frontend starter
├── tests/                     # root shared / integration tests
├── ops/                       # operational helpers
├── docker/                    # Docker related files
└── docs/                      # documentation
```

## 階層アーキテクチャ

```
API層
    ↓
Service層
    ↓
Repository層
    ↓
Model層 + DB
```

## libkoiki vs koiki_ref_app

| 機能 | components/libkoiki | components/koiki_ref_app |
|------|---------------------|---------------------------|
| framework auth / config / middleware | yes | no |
| framework user / permission capabilities | yes | no |
| app factory / ASGI entrypoint | no | yes |
| SSO / SAML reference integration | no | yes |
| reference todo domain | no | yes |

## Entry Points

- Current ASGI entrypoint: `koiki_ref_app.asgi:app`
- Legacy compatibility entrypoint: `app.main:app`

新規作業では `components/` 配下を正本として扱う。
