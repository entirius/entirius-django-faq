# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Admin channel management — list and sync from PIM."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_faq.api.admin.pagination import AdminPageNumberPagination
from django_faq.api.admin.permissions import IsAdminUser
from django_faq.schemas.responses.channel import FaqChannelResponse
from django_faq.services import channel_service


@extend_schema_view(
    list=extend_schema(summary="List FAQ channels", tags=["FAQ Channels"]),
)
class ChannelViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = AdminPageNumberPagination

    def list(self, request: Request, **kwargs) -> Response:
        channels = channel_service.list_channels().prefetch_related("languages")
        results = []
        for ch in channels:
            lang_codes = list(ch.languages.values_list("iso2", flat=True))
            default_lang = ch.default_language.iso2 if ch.default_language else None
            results.append(
                FaqChannelResponse(
                    id=ch.pk, idx=ch.idx, name=ch.name, language_codes=lang_codes, default_language=default_lang
                ).model_dump()
            )
        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Sync FAQ channels from PIM",
        description="Syncs FAQ channels from PIM Channel model. Idempotent.",
        tags=["FAQ Channels"],
        responses={200: {"description": "Sync result"}},
    )
    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request: Request, **kwargs) -> Response:
        count = channel_service.sync_channels_from_pim()
        return Response({"synced": count}, status=status.HTTP_200_OK)
