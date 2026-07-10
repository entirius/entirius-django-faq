# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.urls import path

from django_faq.api.admin.views.channel_views import ChannelViewSet
from django_faq.api.admin.views.discover_views import DiscoverViewSet
from django_faq.api.admin.views.group_views import GroupViewSet
from django_faq.api.admin.views.item_views import ItemViewSet

urlpatterns = [
    # Channels
    path("channels/", ChannelViewSet.as_view({"get": "list"}), name="faq-admin-channels"),
    path("channels/sync/", ChannelViewSet.as_view({"post": "sync"}), name="faq-admin-channels-sync"),
    # Groups (channel-scoped)
    path("<str:channel_idx>/groups/", GroupViewSet.as_view({"get": "list", "post": "create"}), name="faq-admin-groups"),
    path(
        "<str:channel_idx>/groups/reorder/",
        GroupViewSet.as_view({"patch": "reorder"}),
        name="faq-admin-groups-reorder",
    ),
    path(
        "<str:channel_idx>/groups/<str:idx>/",
        GroupViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="faq-admin-group-detail",
    ),
    # Group translations
    path(
        "<str:channel_idx>/groups/<str:idx>/translations/",
        GroupViewSet.as_view({"get": "translations_list", "post": "translations_create"}),
        name="faq-admin-group-translations",
    ),
    path(
        "<str:channel_idx>/groups/<str:idx>/translations/<str:language>/",
        GroupViewSet.as_view({"patch": "translations_update", "delete": "translations_delete"}),
        name="faq-admin-group-translation-detail",
    ),
    # Items (channel-scoped)
    path("<str:channel_idx>/items/", ItemViewSet.as_view({"get": "list", "post": "create"}), name="faq-admin-items"),
    path(
        "<str:channel_idx>/items/reorder/",
        ItemViewSet.as_view({"patch": "reorder"}),
        name="faq-admin-items-reorder",
    ),
    path(
        "<str:channel_idx>/items/<int:pk>/",
        ItemViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="faq-admin-item-detail",
    ),
    # Item translations
    path(
        "<str:channel_idx>/items/<int:pk>/translations/",
        ItemViewSet.as_view({"get": "translations_list", "post": "translations_create"}),
        name="faq-admin-item-translations",
    ),
    path(
        "<str:channel_idx>/items/<int:pk>/translations/<str:language>/",
        ItemViewSet.as_view({"patch": "translations_update", "delete": "translations_delete"}),
        name="faq-admin-item-translation-detail",
    ),
    # Entity discovery
    path(
        "<str:channel_idx>/discover/",
        DiscoverViewSet.as_view({"get": "list"}),
        name="faq-admin-discover",
    ),
]
