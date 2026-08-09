---
title: FAQ
description: Structured Q&A with soft entity references, translations, and channel scoping.
sidebar:
  label: Overview
  collapsed: true
---

django-faq manages structured Q&A content for Volkanos storefronts. Groups organise items, translations handle multilingual display, and soft associations link items to products, categories, or content pages — without hard foreign keys.

## What It Does

- Groups (thematic collections) with T9N name translations
- Items with question, answer, short_answer, optional image, and SEO `url_key`
- Full T9N on items — question, answer, and short_answer all translate
- Soft associations to PIM products, PIM categories, ContentDB blog posts, and ContentDB pages
- Channel scoping (Pattern 2) — empty `channels` M2M on a group means it's global
- Admin API for full CRUD, reorder, translations, and entity discovery
- Public API returning resolved translations with 3-level fallback
- CSV import via `import_faq` management command

## Why Not ContentDB

ContentDB stores freeform JSON page content for the CMS builder. FAQ is relational data: groups contain items, items have typed translations, items link to specific platform entities. A content blob cannot express that without becoming a query nightmare. Use ContentDB for page layouts and rich text sections; use FAQ for Q&A that needs to be filterable, translatable, and entity-linked.

## Soft Dependency Pattern

FAQ is the first Volkanos module to formalise the soft dependency pattern. It works standalone from the moment it's installed. It gains features when optional modules are present:

| Module | Absent | Present |
|--------|--------|---------|
| `django_pim` | Product/category associations accept any string, no validation | SKU and category idx validated on save, autocomplete in admin API |
| `django_contentdb` | Blog post and page associations unvalidated | Route slug validated, autocomplete in admin API |

All conditional imports live in `association_service.py` behind `try/except ImportError`. Nothing at module level touches PIM or ContentDB. The discover endpoint returns `{"results": []}` when optional deps are absent — the CMS shows a plain text input instead of an autocomplete picker.

## Channel Scoping

FaqChannel mirrors PIM channels (Pattern 2 — scoping only, no domain-specific fields). Groups reference channels via M2M. The public API returns:

- Groups with empty `channels` M2M — global, visible everywhere
- Groups assigned to the requested channel

Never filter to channel-only in public views.

Sync channels from PIM:

```bash
python manage.py sync_faq_channels
```

## Public API

```
GET /api/faq/v2/{channel_idx}/groups/?language=en
GET /api/faq/v2/{channel_idx}/items/?language=en&group=shipping
GET /api/faq/v2/{channel_idx}/items/?language=en&entity_type=product&entity_id=CHAIR-001
GET /api/faq/v2/{channel_idx}/items/{url_key}/?language=en
```

Responses use resolved translations — not raw T9N dicts. Inactive groups and items are excluded.

## Pages

- [Data Model](./data-model/) — entities, fields, constraints, T9N resolution
- [Changelog](./changelog/) — version history
