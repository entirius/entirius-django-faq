# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from rest_framework import status

from django_faq.models import FaqGroup, FaqGroupT9N, FaqItemT9N


@pytest.mark.django_db
class TestAdminAuth:
    """Auth tests: 401 no token, 403 regular user, 200 admin."""

    def test_no_auth_returns_401(self, api_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_regular_user_returns_403(self, regular_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/"
        resp = regular_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_returns_200(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/"
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGroupAdminAPI:
    def test_list_groups(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_create_group(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/"
        resp = admin_client.post(url, {"idx": "returns", "name": "Returns"}, format="json")
        assert resp.status_code == 201
        assert resp.data["idx"] == "returns"

    def test_retrieve_group(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["idx"] == "shipping"

    def test_update_group(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/"
        resp = admin_client.patch(url, {"name": "Updated Name"}, format="json")
        assert resp.status_code == 200
        assert resp.data["name"] == "Updated Name"

    def test_update_group_not_found(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/nonexistent/"
        resp = admin_client.patch(url, {"name": "X"}, format="json")
        assert resp.status_code == 404

    def test_delete_group(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/"
        resp = admin_client.delete(url)
        assert resp.status_code == 204

    def test_delete_group_not_found(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/nonexistent/"
        resp = admin_client.delete(url)
        assert resp.status_code == 404

    def test_reorder_groups(self, admin_client, faq_channel, faq_group, faq_group_global):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/reorder/"
        resp = admin_client.patch(url, {"ordered_idxs": ["general", "shipping"]}, format="json")
        assert resp.status_code == 200
        assert FaqGroup.objects.get(idx="general").position == 0
        assert FaqGroup.objects.get(idx="shipping").position == 1


@pytest.mark.django_db
class TestGroupTranslationAPI:
    def test_create_translation(self, admin_client, faq_channel, faq_group, language_en):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/translations/"
        resp = admin_client.post(url, {"language": "en", "name": "Shipping EN"}, format="json")
        assert resp.status_code == 201
        assert resp.data["language"] == "en"

    def test_list_translations(self, admin_client, faq_channel, faq_group, language_en):
        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="Shipping EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/translations/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_update_translation(self, admin_client, faq_channel, faq_group, language_en):
        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="Shipping EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/translations/en/"
        resp = admin_client.patch(url, {"name": "Updated"}, format="json")
        assert resp.status_code == 200
        assert resp.data["name"] == "Updated"

    def test_delete_translation(self, admin_client, faq_channel, faq_group, language_en):
        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="Shipping EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/translations/en/"
        resp = admin_client.delete(url)
        assert resp.status_code == 204

    def test_delete_translation_not_found(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/groups/{faq_group.idx}/translations/xx/"
        resp = admin_client.delete(url)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestItemAdminAPI:
    def test_list_items(self, admin_client, faq_channel, faq_item):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_create_item(self, admin_client, faq_channel, faq_group):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/"
        resp = admin_client.post(
            url,
            {
                "url_key": "new-faq",
                "question": "New question?",
                "answer": "New answer.",
                "group_idx": "shipping",
                "associations": [{"entity_type": "product", "entity_identifier": "SKU-1"}],
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["url_key"] == "new-faq"
        assert len(resp.data["associations"]) == 1

    def test_retrieve_item(self, admin_client, faq_channel, faq_item):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["url_key"] == "how-to-return"

    def test_update_item(self, admin_client, faq_channel, faq_item):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/"
        resp = admin_client.patch(url, {"question": "Updated?"}, format="json")
        assert resp.status_code == 200
        assert resp.data["question"] == "Updated?"

    def test_update_item_not_found(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/99999/"
        resp = admin_client.patch(url, {"question": "X"}, format="json")
        assert resp.status_code == 404

    def test_delete_item(self, admin_client, faq_channel, faq_item):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/"
        resp = admin_client.delete(url)
        assert resp.status_code == 204

    def test_delete_item_not_found(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/99999/"
        resp = admin_client.delete(url)
        assert resp.status_code == 404

    def test_create_item_validation_error(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/"
        resp = admin_client.post(url, {"url_key": ""}, format="json")
        assert resp.status_code == 400

    def test_create_item_invalid_entity_type(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/"
        resp = admin_client.post(
            url,
            {
                "url_key": "test",
                "question": "Q?",
                "answer": "A.",
                "associations": [{"entity_type": "invalid", "entity_identifier": "x"}],
            },
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestItemTranslationAPI:
    def test_create_translation(self, admin_client, faq_channel, faq_item, language_en):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/translations/"
        resp = admin_client.post(url, {"language": "en", "question": "Q EN", "answer": "A EN"}, format="json")
        assert resp.status_code == 201

    def test_list_translations(self, admin_client, faq_channel, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/translations/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_update_translation(self, admin_client, faq_channel, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/translations/en/"
        resp = admin_client.patch(url, {"question": "Updated Q"}, format="json")
        assert resp.status_code == 200

    def test_delete_translation(self, admin_client, faq_channel, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/translations/en/"
        resp = admin_client.delete(url)
        assert resp.status_code == 204

    def test_delete_translation_not_found(self, admin_client, faq_channel, faq_item):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/items/{faq_item.pk}/translations/xx/"
        resp = admin_client.delete(url)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDiscoverAPI:
    def test_discover_empty_without_deps(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/discover/?entity_type=product&search=chair"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["results"] == []

    def test_discover_missing_params(self, admin_client, faq_channel):
        url = f"/api/faq/v2/admin/{faq_channel.idx}/discover/"
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.data["results"] == []


@pytest.mark.django_db
class TestChannelAdminAPI:
    def test_list_channels(self, admin_client, faq_channel):
        resp = admin_client.get("/api/faq/v2/admin/channels/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_sync_channels(self, admin_client):
        resp = admin_client.post("/api/faq/v2/admin/channels/sync/")
        assert resp.status_code == 200
        assert "synced" in resp.data
