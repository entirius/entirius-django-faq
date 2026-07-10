# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Admin group management — CRUD, reorder, translations."""

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
from django_faq.schemas.requests.group import FaqGroupCreateRequest, FaqGroupUpdateRequest, GroupReorderRequest
from django_faq.schemas.requests.t9n import FaqGroupT9NCreateRequest, FaqGroupT9NUpdateRequest
from django_faq.schemas.responses.group import FaqGroupT9NResponse
from django_faq.services import group_service

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List FAQ groups",
        tags=["FAQ Groups"],
        parameters=[
            OpenApiParameter(name="channel_idx", location="path", description="Channel identifier"),
            OpenApiParameter(name="search", description="Search by name or idx"),
            OpenApiParameter(name="is_active", description="Filter by active status", type=bool),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve FAQ group", tags=["FAQ Groups"]),
    create=extend_schema(summary="Create FAQ group", tags=["FAQ Groups"]),
    partial_update=extend_schema(summary="Update FAQ group", tags=["FAQ Groups"]),
    destroy=extend_schema(summary="Delete FAQ group", tags=["FAQ Groups"]),
)
class GroupViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = AdminPageNumberPagination

    def list(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        groups = group_service.list_groups(
            channel_idx=channel_idx,
            search=request.query_params.get("search"),
            is_active=None,
        )
        paginator = AdminPageNumberPagination()
        page = paginator.paginate_queryset(groups, request)
        results = [group_service.serialize_group(g) for g in page]
        return paginator.get_paginated_response(results)

    def retrieve(self, request: Request, channel_idx: str = None, idx: str = None, **kwargs) -> Response:
        try:
            group = group_service.get_group(idx=idx)
        except ObjectDoesNotExist:
            return Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(group_service.serialize_group(group), status=status.HTTP_200_OK)

    def create(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        try:
            data = FaqGroupCreateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        try:
            group = group_service.create_group(
                idx=data.idx,
                name=data.name,
                channel_ids=data.channel_ids,
                position=data.position,
                is_active=data.is_active,
            )
        except IntegrityError:
            raise DRFValidationError({"idx": ["A group with this idx already exists."]})
        return Response(group_service.serialize_group(group), status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, channel_idx: str = None, idx: str = None, **kwargs) -> Response:
        try:
            data = FaqGroupUpdateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        update_kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
        channel_ids = update_kwargs.pop("channel_ids", None)
        try:
            group = group_service.update_group(idx=idx, channel_ids=channel_ids, **update_kwargs)
        except ObjectDoesNotExist:
            return Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(group_service.serialize_group(group), status=status.HTTP_200_OK)

    def destroy(self, request: Request, channel_idx: str = None, idx: str = None, **kwargs) -> Response:
        try:
            group_service.delete_group(idx=idx)
        except ObjectDoesNotExist:
            return Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Reorder FAQ groups", tags=["FAQ Groups"])
    @action(detail=False, methods=["patch"], url_path="reorder")
    def reorder(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        try:
            data = GroupReorderRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        group_service.reorder_groups(ordered_idxs=data.ordered_idxs)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    # --- T9N ---

    @extend_schema(summary="List group translations", tags=["FAQ Groups"])
    @action(detail=True, methods=["get"], url_path="translations", url_name="translations-list")
    def translations_list(self, request: Request, channel_idx: str = None, idx: str = None, **kwargs) -> Response:
        t9ns = group_service.list_group_translations(group_idx=idx)
        results = [FaqGroupT9NResponse(language=t.language.iso2, name=t.name).model_dump() for t in t9ns]
        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(summary="Create group translation", tags=["FAQ Groups"])
    @action(detail=True, methods=["post"], url_path="translations/create", url_name="translations-create")
    def translations_create(self, request: Request, channel_idx: str = None, idx: str = None, **kwargs) -> Response:
        try:
            data = FaqGroupT9NCreateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        t9n = group_service.create_group_translation(group_idx=idx, language_iso2=data.language, name=data.name)
        return Response(
            FaqGroupT9NResponse(language=t9n.language.iso2, name=t9n.name).model_dump(), status=status.HTTP_201_CREATED
        )

    @extend_schema(summary="Update group translation", tags=["FAQ Groups"])
    @action(
        detail=True, methods=["patch"], url_path=r"translations/(?P<language>[a-z]{2})", url_name="translations-update"
    )
    def translations_update(
        self, request: Request, channel_idx: str = None, idx: str = None, language: str = None, **kwargs
    ) -> Response:
        try:
            data = FaqGroupT9NUpdateRequest(**request.data)
        except ValidationError as exc:
            raise_pydantic_as_drf(exc)
        update_kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
        t9n = group_service.update_group_translation(group_idx=idx, language_iso2=language, **update_kwargs)
        return Response(
            FaqGroupT9NResponse(language=t9n.language.iso2, name=t9n.name).model_dump(), status=status.HTTP_200_OK
        )

    @extend_schema(summary="Delete group translation", tags=["FAQ Groups"])
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"translations/(?P<language>[a-z]{2})/delete",
        url_name="translations-delete",
    )
    def translations_delete(
        self, request: Request, channel_idx: str = None, idx: str = None, language: str = None, **kwargs
    ) -> Response:
        try:
            group_service.delete_group_translation(group_idx=idx, language_iso2=language)
        except ObjectDoesNotExist:
            return Response({"detail": "Translation not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
