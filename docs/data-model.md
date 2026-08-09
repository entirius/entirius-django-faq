---
title: Data Model
description: FAQ entity relationships, fields, constraints, and T9N resolution pattern.
---

## Entity Overview

```
FaqChannel (Pattern 2 scoping)
  ↑  M2M
FaqGroup
  ↑  FaqGroupT9N (one row per language)
  ↑  nullable FK
FaqItem
  ↑  FaqItemT9N (one row per language)
  ↑  FK
FaqAssociation (soft entity reference)
```

All models inherit from `django_utils.models.base_model.BaseModel` which provides `created_at` and `modified_at`.

## FaqChannel

Pattern 2 scoping channel — owns only the fields needed for visibility scoping and language resolution. Synced from PIM, no domain-specific configuration.

| Field | Type | Notes |
|-------|------|-------|
| `idx` | CharField(128, unique) | Shared key with PIM Channel |
| `name` | CharField(128, blank) | Display name |
| `default_language` | FK to Language (nullable) | Used as T9N fallback language |
| `languages` | M2M to Language | Available languages for this channel |

Sync: `python manage.py sync_faq_channels`

## FaqGroup

Thematic collection that organises items. Analogous to FeatureSet in PIM — a container with ordering, not a category tree.

| Field | Type | Notes |
|-------|------|-------|
| `idx` | CharField(128, unique) | Natural key: `shipping`, `returns`, `general` |
| `name` | CharField(128) | Base name (untranslated fallback) |
| `channels` | M2M to FaqChannel (blank) | Empty = global; assigned = channel-specific |
| `position` | PositiveIntegerField | Display ordering |
| `is_active` | BooleanField | Soft-disable; inactive groups excluded from public API |

## FaqGroupT9N

Translation row for a group name. One row per language.

| Field | Type | Notes |
|-------|------|-------|
| `group` | FK to FaqGroup (CASCADE) | |
| `language` | FK to Language (CASCADE) | |
| `name` | CharField(128) | Translated group name |

Constraint: `UniqueConstraint(group, language)`

## FaqItem

Single Q&A pair. The core entity. Group membership is optional — ungrouped items are valid and appear in global listings.

| Field | Type | Notes |
|-------|------|-------|
| `group` | FK to FaqGroup (SET_NULL, nullable) | Ungrouped items are valid |
| `url_key` | CharField(128, unique, db_index) | SEO slug — used in public API URL |
| `question` | CharField(512) | Base question (untranslated fallback) |
| `answer` | TextField | HTML allowed — base answer |
| `short_answer` | CharField(512, blank) | Optional summary shown in collapsed view |
| `image` | ImageField(upload_to="faq/", nullable) | Requires Pillow |
| `position` | PositiveIntegerField | Global ordering |
| `position_in_group` | PositiveIntegerField | Ordering within `group` |
| `is_active` | BooleanField | Soft-disable; inactive items excluded from public API |

Indexes: `(group, position_in_group)`, `(is_active)`.

Note: `position` and `position_in_group` are separate. The reorder endpoint accepts `within_group=True` to operate on `position_in_group` instead.

## FaqItemT9N

Translation row for an item. Covers all user-visible text fields.

| Field | Type | Notes |
|-------|------|-------|
| `item` | FK to FaqItem (CASCADE) | |
| `language` | FK to Language (CASCADE) | |
| `question` | CharField(512) | |
| `answer` | TextField | |
| `short_answer` | CharField(512, blank) | |

Constraint: `UniqueConstraint(item, language)`

## FaqAssociation

Soft reference from an FAQ item to an external entity. Uses string identifiers instead of database foreign keys so the module works without PIM or ContentDB installed.

| Field | Type | Notes |
|-------|------|-------|
| `faq_item` | FK to FaqItem (CASCADE) | |
| `entity_type` | CharField(32, choices) | See table below |
| `entity_identifier` | CharField(128) | Type-specific identifier |

Constraint: `UniqueConstraint(faq_item, entity_type, entity_identifier)`

### Entity Type Values

| `entity_type` | Identifier meaning | Validated when |
|---------------|-------------------|----------------|
| `product` | PIM product SKU | `django_pim` installed |
| `category` | PIM category `idx` | `django_pim` installed |
| `blog-post` | ContentDB route slug | `django_contentdb` installed |
| `page` | ContentDB route slug | `django_contentdb` installed |

When the validating module is absent, the association is stored as-is. The discover endpoint (`GET admin/{channel_idx}/discover/`) returns autocomplete results only when the relevant module is present — otherwise returns an empty result set.

## T9N Resolution

The public API resolves translations before returning a response. The fallback chain for each item:

```
1. T9N row matching requested ?language=     → use translated fields
2. T9N row matching channel.default_language  → use as fallback
3. No T9N row found                           → use base item fields
```

Empty T9N fields fall back to the base field, not to an empty string. If `FaqItemT9N.question` is `""`, the response uses `FaqItem.question` instead.

Groups follow the same chain for `name`. Image and `url_key` are not translatable — they come from the base `FaqItem` regardless of language.
