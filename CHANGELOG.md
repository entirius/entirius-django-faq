# Changelog

## 2.0.0 — 2026-07-10

- Initial public release: structured Q&A with groups, per-language T9N
  (question / answer / short_answer / url_key), soft entity associations
  (PIM products and categories, ContentDB posts and pages), and channel
  scoping (Pattern 2).
- Admin v2 API (JWT + IsAdminUser) and public API with 3-level translation
  fallback, `?search=` and allowlisted `?sort=`.
- `alternates` per-locale slug map for hreflang, and `prev`/`next` neighbour
  links on item retrieve for in-topic navigation.
- Grouped CSV import via the `import_faq` management command.
- Migrations squashed into a single initial migration for the Entirius epoch.
