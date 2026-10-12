# entirius-django-faq

A Django module for frequently asked questions in Entirius, the open-source modular ecommerce platform. It stores
questions and answers in groups, translated per language and scoped per sales channel, and links them to products,
categories and blog posts. The CMS manages them over an admin API; the storefront reads a public API.

[![PyPI](https://img.shields.io/pypi/v/entirius-django-faq.svg)](https://pypi.org/project/entirius-django-faq/)
[![Python](https://img.shields.io/pypi/pyversions/entirius-django-faq.svg)](https://pypi.org/project/entirius-django-faq/)
[![License: MPL-2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](https://github.com/entirius/entirius-django-faq/blob/develop/LICENSE)

## What it does

- Stores questions with a full and a short answer, an image and a URL key, organised in groups.
- Translates groups and items per language, falling back to the channel's default language.
- Scopes questions per sales channel.
- Links a question to a product, a category or a blog post without a hard dependency on those modules.
- Exposes an admin API for the CMS and a read-only, channel-scoped public API for the storefront.

## Installation

```shell
uv add entirius-django-faq
pip install entirius-django-faq
```

```python
INSTALLED_APPS = [
    ...
    "django_utils",
    "django_regional",
    "django_faq",
]

# urls.py
urlpatterns = [
    path("", include("django_faq.urls")),
]
```

The module reads no settings of its own. Channel scoping and the public API are described in
https://github.com/entirius/entirius-django-faq/blob/develop/docs/index.md

## Quick start

```python
from django_faq.services.item_service import get_item_by_url_key

item = get_item_by_url_key(url_key="how-do-i-return-an-order", channel_idx="default", language_iso2="en")
```

Channels are copied from the product module, and questions can be imported in bulk:

```shell
python manage.py sync_faq_channels
python manage.py import_faq --csv faq.csv --channel default
```

## Requirements

- Python 3.11 or newer, Django 5.0 or newer.
- Entirius packages pulled in: `entirius-django-utils`, `entirius-django-regional`.

## Documentation

- Module docs: https://github.com/entirius/entirius-django-faq/tree/develop/docs
- Entirius documentation: https://docs.entirius.com/
- Changelog: https://github.com/entirius/entirius-django-faq/blob/develop/CHANGELOG.md

## Part of Entirius

This module runs inside the Entirius backend service (Volkanos), next to the product and content modules.

- Backend service: https://github.com/entirius/entirius-service-volkanos
- Docker harness: https://github.com/entirius/entirius-zeno
- Sibling modules: https://github.com/entirius/entirius-django-pim, https://github.com/entirius/entirius-django-contentdb,
  https://github.com/entirius/entirius-django-sitemap

## Development

```shell
make install     # sync dependencies (uv)
make check       # lint + format check (ruff)
make test        # test suite (pytest + pytest-django)
```

Development and agent instructions: https://github.com/entirius/entirius-django-faq/blob/develop/AGENTS.md

## License

Mozilla Public License 2.0 (MPL-2.0) — see https://github.com/entirius/entirius-django-faq/blob/develop/LICENSE.
