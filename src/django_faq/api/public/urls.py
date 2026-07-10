# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.urls import path

from django_faq.api.public.views.public_views import PublicGroupViewSet, PublicItemViewSet

urlpatterns = [
    path("<str:channel_idx>/items/", PublicItemViewSet.as_view({"get": "list"}), name="faq-public-items"),
    path(
        "<str:channel_idx>/items/<str:url_key>/",
        PublicItemViewSet.as_view({"get": "retrieve"}),
        name="faq-public-item-detail",
    ),
    path("<str:channel_idx>/groups/", PublicGroupViewSet.as_view({"get": "list"}), name="faq-public-groups"),
]
