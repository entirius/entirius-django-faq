# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Entity validation and discovery — soft dependency on PIM/ContentDB."""

import logging

from django_faq.models.faq_association import EntityType

logger = logging.getLogger(__name__)


def validate_entity(entity_type: str, entity_identifier: str) -> bool:
    """Validate entity exists. Returns True if valid or validation unavailable."""
    if entity_type == EntityType.PRODUCT:
        return _validate_product(entity_identifier)
    if entity_type == EntityType.CATEGORY:
        return _validate_category(entity_identifier)
    if entity_type == EntityType.BLOG_POST:
        return _validate_blog_post(entity_identifier)
    return True


def discover_entities(entity_type: str, search: str, limit: int = 20) -> list[dict]:
    """Search for entities by type. Returns list of {identifier, label} dicts."""
    if entity_type == EntityType.PRODUCT:
        return _discover_products(search, limit)
    if entity_type == EntityType.CATEGORY:
        return _discover_categories(search, limit)
    if entity_type == EntityType.BLOG_POST:
        return _discover_blog_posts(search, limit)
    return []


def _validate_product(identifier: str) -> bool:
    try:
        from django_pim.models import RealProduct

        return RealProduct.objects.filter(sku__iexact=identifier).exists()
    except ImportError:
        return True


def _validate_category(identifier: str) -> bool:
    try:
        from django_pim.models import Category

        return Category.objects.filter(idx__iexact=identifier).exists()
    except ImportError:
        return True


def _validate_blog_post(identifier: str) -> bool:
    try:
        from django_contentdb.models import Route

        return Route.objects.filter(url=identifier).exists()
    except ImportError:
        return True


def _discover_products(search: str, limit: int) -> list[dict]:
    try:
        from django.db.models import Q
        from django_pim.models import RealProduct

        qs = RealProduct.objects.filter(Q(sku__icontains=search) | Q(name__icontains=search))[:limit]
        return [{"identifier": p.sku, "label": f"{p.sku} — {p.name}"} for p in qs]
    except ImportError:
        return []


def _discover_categories(search: str, limit: int) -> list[dict]:
    try:
        from django.db.models import Q
        from django_pim.models import Category

        qs = Category.objects.filter(Q(idx__icontains=search) | Q(name_t9n__icontains=search))[:limit]
        return [{"identifier": c.idx, "label": c.idx} for c in qs]
    except ImportError:
        return []


def _discover_blog_posts(search: str, limit: int) -> list[dict]:
    try:
        from django_contentdb.models import Route

        qs = Route.objects.filter(url__icontains=search)[:limit]
        return [{"identifier": r.url, "label": r.url} for r in qs]
    except ImportError:
        return []
