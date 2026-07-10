# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""FAQ group management — CRUD, reorder, channel scoping, T9N."""

from django.db.models import Count, Prefetch, Q, QuerySet

from django_faq.models import FaqChannel, FaqGroup, FaqGroupT9N
from django_faq.schemas.responses.group import FaqGroupResponse, FaqGroupT9NResponse

_GROUP_PREFETCH = Prefetch("translations", queryset=FaqGroupT9N.objects.select_related("language"))

_GROUP_UPDATE_FIELDS = {"name", "position", "is_active"}


def list_groups(
    *,
    channel_idx: str | None = None,
    search: str | None = None,
    is_active: bool | None = True,
) -> QuerySet[FaqGroup]:
    """List groups scoped to channel (assigned + global). Annotates item_count."""
    qs = FaqGroup.objects.annotate(item_count=Count("items")).prefetch_related("channels", _GROUP_PREFETCH)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if channel_idx:
        channel = FaqChannel.objects.get(idx=channel_idx)
        qs = qs.filter(Q(channels=channel) | Q(channels=None)).distinct()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(idx__icontains=search))
    return qs


def get_group(*, idx: str) -> FaqGroup:
    """Get group by idx. Raises FaqGroup.DoesNotExist."""
    return (
        FaqGroup.objects.annotate(item_count=Count("items")).prefetch_related("channels", _GROUP_PREFETCH).get(idx=idx)
    )


def create_group(*, idx: str, name: str, channel_ids: list[int] | None = None, **kwargs) -> FaqGroup:
    group = FaqGroup.objects.create(idx=idx, name=name, **kwargs)
    if channel_ids:
        from django_faq.services import channel_service

        channels = channel_service.get_channels_by_pks(channel_ids)
        group.channels.set(channels)
    return get_group(idx=group.idx)


def update_group(*, idx: str, channel_ids: list[int] | None = None, **kwargs) -> FaqGroup:
    group = FaqGroup.objects.get(idx=idx)
    for field, value in kwargs.items():
        if field not in _GROUP_UPDATE_FIELDS:
            raise ValueError(f"Cannot update field: {field}")
        setattr(group, field, value)
    group.save()
    if channel_ids is not None:
        from django_faq.services import channel_service

        channels = channel_service.get_channels_by_pks(channel_ids)
        group.channels.set(channels)
    return get_group(idx=group.idx)


def delete_group(*, idx: str) -> None:
    FaqGroup.objects.get(idx=idx).delete()


def reorder_groups(*, ordered_idxs: list[str]) -> None:
    """Set position based on list order using bulk_update."""
    groups = {g.idx: g for g in FaqGroup.objects.filter(idx__in=ordered_idxs)}
    for position, idx in enumerate(ordered_idxs):
        if idx in groups:
            groups[idx].position = position
    FaqGroup.objects.bulk_update(groups.values(), fields=["position"], batch_size=500)


# --- Serialization (used by views) ---


def serialize_group(group) -> dict:
    """Build response dict from prefetched group. No extra queries."""
    channel_ids = list(group.channels.values_list("pk", flat=True))
    translations = [
        FaqGroupT9NResponse(language=t.language.iso2, name=t.name).model_dump() for t in group.translations.all()
    ]
    item_count = getattr(group, "item_count", 0)
    return FaqGroupResponse(
        id=group.pk,
        idx=group.idx,
        name=group.name,
        translations=translations,
        channel_ids=channel_ids,
        position=group.position,
        is_active=group.is_active,
        item_count=item_count,
    ).model_dump()


# --- T9N ---


def resolve_group_name(
    group: FaqGroup | None, channel: FaqChannel | None = None, language_iso2: str | None = None
) -> str:
    """Resolve group name with T9N fallback. Reads from prefetch cache."""
    if not group:
        return ""
    if not language_iso2:
        return group.name
    t9ns = {t.language.iso2.lower(): t for t in group.translations.all()}
    t9n = t9ns.get(language_iso2.lower())
    if t9n:
        return t9n.name or group.name
    if channel and channel.default_language:
        t9n = t9ns.get(channel.default_language.iso2.lower())
        if t9n:
            return t9n.name or group.name
    return group.name


def list_group_translations(*, group_idx: str) -> QuerySet[FaqGroupT9N]:
    return FaqGroupT9N.objects.filter(group__idx=group_idx).select_related("language")


def create_group_translation(*, group_idx: str, language_iso2: str, name: str) -> FaqGroupT9N:
    from django_regional.models import Language

    group = FaqGroup.objects.get(idx=group_idx)
    language = Language.objects.get(iso2__iexact=language_iso2)
    return FaqGroupT9N.objects.create(group=group, language=language, name=name)


_GROUP_T9N_UPDATE_FIELDS = {"name"}


def update_group_translation(*, group_idx: str, language_iso2: str, **kwargs) -> FaqGroupT9N:
    t9n = FaqGroupT9N.objects.select_related("language").get(group__idx=group_idx, language__iso2__iexact=language_iso2)
    for field, value in kwargs.items():
        if field not in _GROUP_T9N_UPDATE_FIELDS:
            raise ValueError(f"Cannot update field: {field}")
        setattr(t9n, field, value)
    t9n.save()
    return t9n


def delete_group_translation(*, group_idx: str, language_iso2: str) -> None:
    FaqGroupT9N.objects.get(group__idx=group_idx, language__iso2__iexact=language_iso2).delete()
