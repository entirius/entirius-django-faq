# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Entity discovery — autocomplete for associations."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_faq.api.admin.permissions import IsAdminUser
from django_faq.schemas.responses.item import DiscoverResponse
from django_faq.services import association_service


class DiscoverViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Discover entities for FAQ associations",
        description="Search for products, categories, or blog posts. Returns empty when optional modules are not installed.",
        tags=["FAQ Discovery"],
        parameters=[
            OpenApiParameter(name="channel_idx", location="path", description="Channel identifier"),
            OpenApiParameter(
                name="entity_type", required=True, description="Entity type: product, category, blog-post, page"
            ),
            OpenApiParameter(name="search", required=True, description="Search query"),
        ],
        responses={200: DiscoverResponse},
    )
    def list(self, request: Request, channel_idx: str = None, **kwargs) -> Response:
        entity_type = request.query_params.get("entity_type", "")
        search = request.query_params.get("search", "")
        if not entity_type or not search:
            return Response(DiscoverResponse(results=[]).model_dump(), status=status.HTTP_200_OK)
        results = association_service.discover_entities(entity_type=entity_type, search=search)
        return Response(DiscoverResponse(results=results).model_dump(), status=status.HTTP_200_OK)
