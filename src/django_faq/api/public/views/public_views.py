# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Public FAQ API — channel-scoped, language-aware, active-only."""

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from django_faq.api.admin.pagination import AdminPageNumberPagination
from django_faq.models import FaqChannel, FaqItem
from django_faq.schemas.responses.item import (
    FaqAssociationResponse,
    FaqSiblingResponse,
    PublicFaqGroupResponse,
    PublicFaqItemResponse,
)
from django_faq.services import channel_service, item_service
from django_faq.services import group_service as grp_svc


def _build_alternates(item, channel) -> dict[str, str]:
    """Per-locale slug map: channel default lang -> base url_key, plus each t9n with non-empty url_key.

    Reads from prefetch cache — no extra queries.
    """
    alternates: dict[str, str] = {}
    if channel and channel.default_language:
        alternates[channel.default_language.iso2.lower()] = item.url_key
    for t9n in item.translations.all():
        if t9n.url_key:
            alternates[t9n.language.iso2.lower()] = t9n.url_key
    return alternates


def _build_sibling(
    neighbor: FaqItem | None,
    channel: FaqChannel | None,
    language_iso2: str | None,
) -> dict | None:
    """Build the prev/next link payload. ``url_key`` and ``question`` are resolved
    against the requested language (3-level fallback)."""
    if neighbor is None:
        return None
    resolved = item_service.resolve_translation(neighbor, channel=channel, language_iso2=language_iso2)
    return FaqSiblingResponse(url_key=resolved["url_key"], question=resolved["question"]).model_dump()


def _build_public_item(
    item: FaqItem,
    channel: FaqChannel | None,
    language_iso2: str | None,
    *,
    with_siblings: bool = False,
) -> dict:
    resolved = item_service.resolve_translation(item, channel=channel, language_iso2=language_iso2)
    group_name = grp_svc.resolve_group_name(item.group, channel=channel, language_iso2=language_iso2)
    associations = [
        FaqAssociationResponse(entity_type=a.entity_type, entity_identifier=a.entity_identifier).model_dump()
        for a in item.associations.all()
    ]
    image_url = item.image.url if item.image else None
    prev_payload = None
    next_payload = None
    if with_siblings:
        neighbors = item_service.get_neighbors(item=item, channel_idx=channel.idx if channel is not None else None)
        prev_payload = _build_sibling(neighbors["prev"], channel, language_iso2)
        next_payload = _build_sibling(neighbors["next"], channel, language_iso2)
    return PublicFaqItemResponse(
        url_key=resolved["url_key"],
        question=resolved["question"],
        answer=resolved["answer"],
        short_answer=resolved["short_answer"],
        image_url=image_url,
        group_idx=item.group.idx if item.group else None,
        group_name=group_name,
        alternates=_build_alternates(item, channel),
        associations=associations,
        prev=prev_payload,
        next=next_payload,
    ).model_dump()


@extend_schema_view(
    list=extend_schema(
        summary="List active FAQ items",
        tags=["FAQ Public"],
        parameters=[
            OpenApiParameter(name="channel_idx", location="path", description="Channel identifier"),
            OpenApiParameter(name="language", description="Language ISO2 for translation resolution"),
            OpenApiParameter(name="group", description="Filter by group idx"),
            OpenApiParameter(name="search", description="Search in question text and url_key"),
            OpenApiParameter(
                name="sort",
                description="Sort field(s). Prefix with - for descending. "
                "Allowed: position, position_in_group, question, url_key, created_at. "
                "Example: sort=-created_at",
            ),
            OpenApiParameter(name="entity_type", description="Filter by entity type"),
            OpenApiParameter(name="entity_id", description="Filter by entity identifier"),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve FAQ item by url_key", tags=["FAQ Public"]),
)
class PublicItemViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = AdminPageNumberPagination

    def list(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        language_iso2 = request.query_params.get("language", "").strip().lower() or None
        try:
            channel = channel_service.get_channel(channel_idx)
        except ObjectDoesNotExist:
            return Response({"detail": "Channel not found"}, status=status.HTTP_404_NOT_FOUND)

        sort_raw = request.query_params.getlist("sort")
        sort_params = [field.strip() for s in sort_raw for field in s.split(",")] or None

        items = item_service.list_items(
            channel_idx=channel_idx,
            group_idx=request.query_params.get("group"),
            search=request.query_params.get("search"),
            entity_type=request.query_params.get("entity_type"),
            entity_id=request.query_params.get("entity_id"),
            sort=sort_params,
        )
        paginator = AdminPageNumberPagination()
        page = paginator.paginate_queryset(items, request)
        results = [_build_public_item(i, channel, language_iso2) for i in page]
        return paginator.get_paginated_response(results)

    def retrieve(self, request: Request, channel_idx: str = None, url_key: str = None, **kwargs) -> Response:
        language_iso2 = request.query_params.get("language", "").strip().lower() or None
        try:
            channel = channel_service.get_channel(channel_idx)
        except ObjectDoesNotExist:
            return Response({"detail": "Channel not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            item = item_service.get_item_by_url_key(
                url_key=url_key, channel_idx=channel_idx, language_iso2=language_iso2
            )
        except ObjectDoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            _build_public_item(item, channel, language_iso2, with_siblings=True),
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List active FAQ groups",
        tags=["FAQ Public"],
        parameters=[
            OpenApiParameter(name="channel_idx", location="path", description="Channel identifier"),
            OpenApiParameter(name="language", description="Language ISO2 for translation resolution"),
        ],
    )
)
class PublicGroupViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = AdminPageNumberPagination

    def list(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        language_iso2 = request.query_params.get("language", "").strip().lower() or None
        try:
            channel = channel_service.get_channel(channel_idx)
        except ObjectDoesNotExist:
            return Response({"detail": "Channel not found"}, status=status.HTTP_404_NOT_FOUND)

        groups = grp_svc.list_groups(channel_idx=channel_idx)
        paginator = AdminPageNumberPagination()
        page = paginator.paginate_queryset(groups, request)
        results = []
        for g in page:
            name = grp_svc.resolve_group_name(g, channel=channel, language_iso2=language_iso2)
            results.append(
                PublicFaqGroupResponse(idx=g.idx, name=name, item_count=getattr(g, "item_count", 0)).model_dump()
            )
        return paginator.get_paginated_response(results)
