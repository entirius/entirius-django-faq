# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""FAQ item management — CRUD, T9N resolution, channel scoping."""

from django.db.models import Prefetch, Q, QuerySet

from django_faq.models import FaqAssociation, FaqChannel, FaqGroup, FaqItem, FaqItemT9N
from django_faq.schemas.responses.item import FaqAssociationResponse, FaqItemResponse, FaqItemT9NResponse

_ITEM_PREFETCH = Prefetch("translations", queryset=FaqItemT9N.objects.select_related("language"))

_ITEM_UPDATE_FIELDS = {"url_key", "question", "answer", "short_answer", "position", "position_in_group", "is_active"}

_SORT_ALLOWED_FIELDS = {"position", "position_in_group", "question", "url_key", "created_at"}


def _apply_sort(qs: QuerySet, sort_params: list[str] | None) -> QuerySet:
    """Apply sort with allowlist. Format: 'field' or '-field'. Consistent with ContentDB v2."""
    if not sort_params:
        return qs
    validated = [p for p in sort_params if p.lstrip("-") in _SORT_ALLOWED_FIELDS]
    if validated:
        return qs.order_by(*validated)
    return qs


def _apply_channel_scope(qs: QuerySet[FaqItem], channel_idx: str | None) -> QuerySet[FaqItem]:
    """Filter items to those visible in ``channel_idx`` scope.

    Visible = item is ungrouped, or its group has the channel in M2M, or its group
    has empty M2M (global). Uses ``__idx`` lookup so an unknown channel yields an
    empty queryset rather than raising ``FaqChannel.DoesNotExist``. ``.distinct()``
    is required because the M2M join can duplicate rows.
    """
    if not channel_idx:
        return qs
    return qs.filter(
        Q(group__channels__idx=channel_idx) | Q(group__channels__isnull=True) | Q(group__isnull=True)
    ).distinct()


def list_items(
    *,
    channel_idx: str | None = None,
    group_idx: str | None = None,
    search: str | None = None,
    is_active: bool | None = True,
    entity_type: str | None = None,
    entity_id: str | None = None,
    sort: list[str] | None = None,
) -> QuerySet[FaqItem]:
    """List items with optional filters. Channel scoping via group.channels."""
    qs = FaqItem.objects.select_related("group").prefetch_related("associations", _ITEM_PREFETCH)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    qs = _apply_channel_scope(qs, channel_idx)
    if group_idx:
        qs = qs.filter(group__idx=group_idx)
        if not sort:
            qs = qs.order_by("position_in_group")
    if search:
        qs = qs.filter(Q(question__icontains=search) | Q(url_key__icontains=search))
    if entity_type and entity_id:
        qs = qs.filter(associations__entity_type=entity_type, associations__entity_identifier=entity_id)
    elif entity_type:
        qs = qs.filter(associations__entity_type=entity_type)
    return _apply_sort(qs, sort)


def get_item(*, pk: int) -> FaqItem:
    """Get item by PK. Raises FaqItem.DoesNotExist."""
    return FaqItem.objects.select_related("group").prefetch_related("associations", _ITEM_PREFETCH).get(pk=pk)


def get_item_by_url_key(*, url_key: str, channel_idx: str | None = None, language_iso2: str | None = None) -> FaqItem:
    """Get item by url_key. When ``language_iso2`` is given, look up T9N url_key first,
    fall back to base url_key. Raises FaqItem.DoesNotExist when not found or not active.
    """
    item: FaqItem | None = None

    if language_iso2:
        t9n = (
            FaqItemT9N.objects.filter(language__iso2__iexact=language_iso2, url_key=url_key)
            .select_related("item")
            .first()
        )
        if t9n:
            item = t9n.item

    if item is None:
        qs = FaqItem.objects.select_related("group").prefetch_related("associations", _ITEM_PREFETCH)
        item = qs.get(url_key=url_key, is_active=True)
    elif not item.is_active:
        raise FaqItem.DoesNotExist("FaqItem matching T9N url_key is not active")

    if channel_idx and item.group:
        channel = FaqChannel.objects.get(idx=channel_idx)
        if item.group.channels.exists() and not item.group.channels.filter(pk=channel.pk).exists():
            raise FaqItem.DoesNotExist("Item not visible in channel")

    return get_item(pk=item.pk)


def get_neighbors(*, item: FaqItem, channel_idx: str | None = None) -> dict:
    """Return ``{"prev": FaqItem | None, "next": FaqItem | None}`` for an item.

    Grouped (``item.group`` set): siblings are other active items in the same group,
    ordered by ``position_in_group``.
    Ungrouped (``item.group`` is None): siblings are other active ungrouped items
    in the same channel scope, ordered by ``position``.

    Channel scoping mirrors :func:`list_items` via :func:`_apply_channel_scope`.
    Translations are prefetched so the caller can call :func:`resolve_translation`
    on the returned items without extra queries.
    """
    qs = FaqItem.objects.select_related("group").prefetch_related(_ITEM_PREFETCH).filter(is_active=True)
    qs = _apply_channel_scope(qs, channel_idx)

    if item.group_id is not None:
        scope = qs.filter(group_id=item.group_id).exclude(pk=item.pk)
        prev_item = (
            scope.filter(position_in_group__lt=item.position_in_group).order_by("-position_in_group", "-pk").first()
        )
        next_item = (
            scope.filter(position_in_group__gt=item.position_in_group).order_by("position_in_group", "pk").first()
        )
    else:
        scope = qs.filter(group__isnull=True).exclude(pk=item.pk)
        prev_item = scope.filter(position__lt=item.position).order_by("-position", "-pk").first()
        next_item = scope.filter(position__gt=item.position).order_by("position", "pk").first()

    return {"prev": prev_item, "next": next_item}


def create_item(
    *,
    url_key: str,
    question: str,
    answer: str,
    group_idx: str | None = None,
    associations: list[dict] | None = None,
    **kwargs,
) -> FaqItem:
    group = None
    if group_idx:
        group = FaqGroup.objects.get(idx=group_idx)
    item = FaqItem.objects.create(url_key=url_key, question=question, answer=answer, group=group, **kwargs)
    if associations:
        _sync_associations(item, associations)
    return get_item(pk=item.pk)


def update_item(*, pk: int, group_idx: str | None = ..., associations: list[dict] | None = None, **kwargs) -> FaqItem:
    """Update item fields. group_idx=... means unchanged, group_idx=None means ungroup."""
    item = FaqItem.objects.get(pk=pk)
    if group_idx is not ...:
        if group_idx is None:
            item.group = None
        else:
            item.group = FaqGroup.objects.get(idx=group_idx)
    for field, value in kwargs.items():
        if field not in _ITEM_UPDATE_FIELDS:
            raise ValueError(f"Cannot update field: {field}")
        setattr(item, field, value)
    item.save()
    if associations is not None:
        _sync_associations(item, associations)
    return get_item(pk=item.pk)


def delete_item(*, pk: int) -> None:
    FaqItem.objects.get(pk=pk).delete()


def reorder_items(*, ordered_pks: list[int], within_group: bool = False) -> None:
    """Set position (or position_in_group) based on list order using bulk_update."""
    field = "position_in_group" if within_group else "position"
    items = {i.pk: i for i in FaqItem.objects.filter(pk__in=ordered_pks)}
    for position, pk in enumerate(ordered_pks):
        if pk in items:
            setattr(items[pk], field, position)
    FaqItem.objects.bulk_update(items.values(), fields=[field], batch_size=500)


def _sync_associations(item: FaqItem, associations: list[dict]) -> None:
    """Replace all associations for an item."""
    FaqAssociation.objects.filter(faq_item=item).delete()
    FaqAssociation.objects.bulk_create(
        [
            FaqAssociation(faq_item=item, entity_type=a["entity_type"], entity_identifier=a["entity_identifier"])
            for a in associations
        ],
        ignore_conflicts=True,
    )


# --- Serialization (used by views) ---


def serialize_item(item) -> dict:
    """Build response dict from prefetched item. No extra queries."""
    translations = [
        FaqItemT9NResponse(
            language=t.language.iso2,
            url_key=t.url_key,
            question=t.question,
            answer=t.answer,
            short_answer=t.short_answer,
        ).model_dump()
        for t in item.translations.all()
    ]
    associations = [
        FaqAssociationResponse(entity_type=a.entity_type, entity_identifier=a.entity_identifier).model_dump()
        for a in item.associations.all()
    ]
    image_url = item.image.url if item.image else None
    return FaqItemResponse(
        id=item.pk,
        url_key=item.url_key,
        question=item.question,
        answer=item.answer,
        short_answer=item.short_answer,
        image_url=image_url,
        group_idx=item.group.idx if item.group else None,
        group_name=item.group.name if item.group else None,
        position=item.position,
        position_in_group=item.position_in_group,
        is_active=item.is_active,
        translations=translations,
        associations=associations,
    ).model_dump()


# --- T9N resolution ---


def resolve_translation(item: FaqItem, channel: FaqChannel | None = None, language_iso2: str | None = None) -> dict:
    """Resolve translated fields using 3-level fallback. Reads from prefetch cache."""
    base = {
        "url_key": item.url_key,
        "question": item.question,
        "answer": item.answer,
        "short_answer": item.short_answer,
    }
    if not language_iso2:
        return base

    t9ns = {t.language.iso2.lower(): t for t in item.translations.all()}
    t9n = t9ns.get(language_iso2.lower())
    if t9n:
        return _t9n_to_dict(t9n, base)

    if channel and channel.default_language:
        t9n = t9ns.get(channel.default_language.iso2.lower())
        if t9n:
            return _t9n_to_dict(t9n, base)

    return base


def _t9n_to_dict(t9n: FaqItemT9N, base: dict) -> dict:
    """Merge T9N fields with base, falling back to base for empty values."""
    return {
        "url_key": t9n.url_key or base["url_key"],
        "question": t9n.question or base["question"],
        "answer": t9n.answer or base["answer"],
        "short_answer": t9n.short_answer or base["short_answer"],
    }


# --- Item T9N CRUD ---


def list_item_translations(*, item_pk: int) -> QuerySet[FaqItemT9N]:
    return FaqItemT9N.objects.filter(item__pk=item_pk).select_related("language")


def create_item_translation(*, item_pk: int, language_iso2: str, question: str, answer: str, **kwargs) -> FaqItemT9N:
    from django_regional.models import Language

    item = FaqItem.objects.get(pk=item_pk)
    language = Language.objects.get(iso2__iexact=language_iso2)
    return FaqItemT9N.objects.create(item=item, language=language, question=question, answer=answer, **kwargs)


_ITEM_T9N_UPDATE_FIELDS = {"url_key", "question", "answer", "short_answer"}


def update_item_translation(*, item_pk: int, language_iso2: str, **kwargs) -> FaqItemT9N:
    t9n = FaqItemT9N.objects.select_related("language").get(item__pk=item_pk, language__iso2__iexact=language_iso2)
    for field, value in kwargs.items():
        if field not in _ITEM_T9N_UPDATE_FIELDS:
            raise ValueError(f"Cannot update field: {field}")
        setattr(t9n, field, value)
    t9n.save()
    return t9n


def delete_item_translation(*, item_pk: int, language_iso2: str) -> None:
    FaqItemT9N.objects.get(item__pk=item_pk, language__iso2__iexact=language_iso2).delete()
