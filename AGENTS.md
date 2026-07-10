# AGENTS.md

FAQ module for Volkanos — distribution `entirius-django-faq`, Django app `django_faq`.
Structured Q&A with soft entity references, T9N translations, image support and group management.

## Commands

| Command | Meaning |
|---|---|
| `make install` | sync dependencies (uv, incl. extras) |
| `make check` | lint + format-check (ruff) |
| `make fix` | auto-fix lint + format |
| `make test` | test suite (pytest + pytest-django) |

## Conventions

- English only: code, docs, commits, branches, PRs.
- MPL-2.0: every non-trivial source file carries the license header (pre-commit inserts it).
- Toolchain: uv + ruff + hatchling + pytest; all config in `pyproject.toml`; `uv.lock` committed.
- Git flow: `master` (production) + `develop` (integration); changes land via PR; semver tag on `master`.
- Never rename the package / Django app_label / DB table prefix `django_faq` — it is a schema contract.
- Migrations are part of the public contract — never edit an already released migration.
- Default: do not commit — git is the user's call.

## Architecture

- `models/` — `FaqChannel` (scoping), `FaqGroup` + `FaqGroupT9N`, `FaqItem` + `FaqItemT9N`
  (question/answer/short_answer per language, `url_key`), `FaqAssociation` (soft entity references
  with `EntityType` enum: product / category / blog post).
- `services/` — channel sync from PIM, group/item CRUD with T9N fallback resolution,
  association validation and entity discovery.
- `schemas/` — pydantic request/response models.
- `api/` — `admin/` (v2, JWT + IsAdminUser) and `public/` (v2, AllowAny, channel-scoped).

Layer rule: `API → Services → Models → DB`. No ORM in views.

## Gotchas

- Entity references are soft: `django_pim` / `django_contentdb` imports are lazy with
  `try/except ImportError` fallbacks — validation passes and discovery returns empty when absent.
- `channel_service.sync_channels_from_pim()` is a no-op (returns 0) when `django_pim` is not installed.
- T9N resolution falls back: requested language → channel default language → base item fields.
