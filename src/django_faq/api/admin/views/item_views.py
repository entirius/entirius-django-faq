# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Admin item management — CRUD, reorder, translations, associations."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django_utils.api.v2_errors import raise_pydantic_as_drf
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from pydantic import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_faq.api.admin.pagination import AdminPageNumberPagination
from django_faq.api.admin.permissions import IsAdminUser
from django_faq.schemas.requests.item import FaqItemCreateRequest, FaqItemUpdateRequest, ItemReorderRequest
from django_faq.schemas.requests.t9n import FaqItemT9NCreateRequest, FaqItemT9NUpdateRequest
from django_faq.schemas.responses.item import FaqItemT9NResponse
from django_faq.services import item_service

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List FAQ items",
        tags=["FAQ Items"],
        parameters=[
            OpenApiParameter(name="channel_idx", location="path", description="Channel identifier"),
            OpenApiParameter(name="search", description="Search by question or url_key"),
            OpenApiParameter(name="group", description="Filter by group idx"),
            OpenApiParameter(name="is_active", description="Filter by active status", type=bool),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve FAQ item", tags=["FAQ Items"]),
    create=extend_schema(summary="Create FAQ item", tags=["FAQ Items"]),
    partial_update=extend_schema(summary="Update FAQ item", tags=["FAQ Items"]),
    destroy=extend_schema(summary="Delete FAQ item", tags=["FAQ Items"]),
)
class ItemViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = AdminPageNumberPagination

    def list(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        items = item_service.list_items(
            channel_idx=channel_idx,
            group_idx=request.query_params.get("group"),
            search=request.query_params.get("search"),
            is_active=None,
        )
        paginator = AdminPageNumberPagination()
        page = paginator.paginate_queryset(items, request)
        results = [item_service.serialize_item(i) for i in page]
        return paginator.get_paginated_response(results)

    def retrieve(self, request: Request, channel_idx: str = None, pk: int = None, **kwargs) -> Response:
        try:
            item = item_service.get_item(pk=pk)
        except ObjectDoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(item_service.serialize_item(item), status=status.HTTP_200_OK)

    def create(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        try:
            data = FaqItemCreateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        associations = [a.model_dump() for a in data.associations] if data.associations else None
        try:
            item = item_service.create_item(
                url_key=data.url_key,
                question=data.question,
                answer=data.answer,
                short_answer=data.short_answer,
                group_idx=data.group_idx,
                position=data.position,
                position_in_group=data.position_in_group,
                is_active=data.is_active,
                associations=associations,
            )
        except IntegrityError:
            raise DRFValidationError({"url_key": ["An item with this url_key already exists."]})
        return Response(item_service.serialize_item(item), status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, channel_idx: str = None, pk: int = None, **kwargs) -> Response:
        try:
            data = FaqItemUpdateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        update_kwargs = {}
        for field in ["url_key", "question", "answer", "short_answer", "position", "position_in_group", "is_active"]:
            val = getattr(data, field)
            if val is not None:
                update_kwargs[field] = val

        group_idx = ... if data.group_idx is None and "group_idx" not in request.data else data.group_idx
        associations = [a.model_dump() for a in data.associations] if data.associations is not None else None

        try:
            item = item_service.update_item(pk=pk, group_idx=group_idx, associations=associations, **update_kwargs)
        except ObjectDoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(item_service.serialize_item(item), status=status.HTTP_200_OK)

    def destroy(self, request: Request, channel_idx: str = None, pk: int = None, **kwargs) -> Response:
        try:
            item_service.delete_item(pk=pk)
        except ObjectDoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Reorder FAQ items", tags=["FAQ Items"])
    @action(detail=False, methods=["patch"], url_path="reorder")
    def reorder(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        try:
            data = ItemReorderRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        item_service.reorder_items(ordered_pks=data.ordered_pks, within_group=data.within_group)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    # --- T9N ---

    @extend_schema(summary="List item translations", tags=["FAQ Items"])
    @action(detail=True, methods=["get"], url_path="translations", url_name="translations-list")
    def translations_list(self, request: Request, channel_idx: str = None, pk: int = None, **kwargs) -> Response:
        t9ns = item_service.list_item_translations(item_pk=pk)
        results = [
            FaqItemT9NResponse(
                language=t.language.iso2,
                url_key=t.url_key,
                question=t.question,
                answer=t.answer,
                short_answer=t.short_answer,
            ).model_dump()
            for t in t9ns
        ]
        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(summary="Create item translation", tags=["FAQ Items"])
    @action(detail=True, methods=["post"], url_path="translations/create", url_name="translations-create")
    def translations_create(self, request: Request, channel_idx: str = None, pk: int = None, **kwargs) -> Response:
        try:
            data = FaqItemT9NCreateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        t9n = item_service.create_item_translation(
            item_pk=pk,
            language_iso2=data.language,
            url_key=data.url_key,
            question=data.question,
            answer=data.answer,
            short_answer=data.short_answer,
        )
        return Response(
            FaqItemT9NResponse(
                language=t9n.language.iso2,
                url_key=t9n.url_key,
                question=t9n.question,
                answer=t9n.answer,
                short_answer=t9n.short_answer,
            ).model_dump(),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Update item translation", tags=["FAQ Items"])
    @action(
        detail=True, methods=["patch"], url_path=r"translations/(?P<language>[a-z]{2})", url_name="translations-update"
    )
    def translations_update(
        self, request: Request, channel_idx: str = None, pk: int = None, language: str = None, **kwargs
    ) -> Response:
        try:
            data = FaqItemT9NUpdateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        update_kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
        t9n = item_service.update_item_translation(item_pk=pk, language_iso2=language, **update_kwargs)
        return Response(
            FaqItemT9NResponse(
                language=t9n.language.iso2,
                url_key=t9n.url_key,
                question=t9n.question,
                answer=t9n.answer,
                short_answer=t9n.short_answer,
            ).model_dump(),
            status=status.HTTP_200_OK,
        )

    @extend_schema(summary="Delete item translation", tags=["FAQ Items"])
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"translations/(?P<language>[a-z]{2})/delete",
        url_name="translations-delete",
    )
    def translations_delete(
        self, request: Request, channel_idx: str = None, pk: int = None, language: str = None, **kwargs
    ) -> Response:
        try:
            item_service.delete_item_translation(item_pk=pk, language_iso2=language)
        except ObjectDoesNotExist:
            return Response({"detail": "Translation not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
