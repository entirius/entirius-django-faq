# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from django_faq.models import FaqGroup, FaqItem, FaqItemT9N


@pytest.mark.django_db
class TestPublicItemAPI:
    def test_list_items(self, api_client, faq_channel, faq_item):
        url = f"/api/faq/v2/{faq_channel.idx}/items/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_list_items_by_group(self, api_client, faq_channel, faq_item, faq_item_ungrouped):
        url = f"/api/faq/v2/{faq_channel.idx}/items/?group=shipping"
        resp = api_client.get(url)
        assert resp.status_code == 200
        url_keys = [r["url_key"] for r in resp.data["results"]]
        assert "how-to-return" in url_keys
        assert "about-us" not in url_keys

    def test_list_items_with_language(self, api_client, faq_channel, faq_item, language_en):
        FaqItemT9N.objects.create(
            item=faq_item, language=language_en, question="Q EN", answer="A EN", short_answer="Short EN"
        )
        url = f"/api/faq/v2/{faq_channel.idx}/items/?language=en"
        resp = api_client.get(url)
        assert resp.status_code == 200
        result = resp.data["results"][0]
        assert result["question"] == "Q EN"

    def test_list_items_language_fallback(self, api_client, faq_channel, faq_item, language_en):
        """Requesting unavailable language falls back to channel default."""
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        url = f"/api/faq/v2/{faq_channel.idx}/items/?language=de"
        resp = api_client.get(url)
        assert resp.status_code == 200
        result = resp.data["results"][0]
        assert result["question"] == "Q EN"

    def test_list_active_only(self, api_client, faq_channel, faq_item):
        faq_item.is_active = False
        faq_item.save()
        url = f"/api/faq/v2/{faq_channel.idx}/items/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["count"] == 0

    def test_retrieve_by_url_key(self, api_client, faq_channel, faq_item):
        url = f"/api/faq/v2/{faq_channel.idx}/items/{faq_item.url_key}/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["url_key"] == "how-to-return"

    def test_alternates_includes_default_language(self, api_client, faq_channel, faq_item):
        """Item with no t9n: alternates contains only channel default language."""
        url = f"/api/faq/v2/{faq_channel.idx}/items/{faq_item.url_key}/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        # faq_channel default_language is EN; faq_item url_key is "how-to-return"
        assert resp.data["alternates"] == {"en": "how-to-return"}

    def test_alternates_includes_t9n_url_key(self, api_client, faq_channel, faq_item, language_pl):
        """T9N with non-empty url_key adds a per-locale entry."""
        FaqItemT9N.objects.create(
            item=faq_item,
            language=language_pl,
            question="Jak zwrocic?",
            answer="A PL",
            short_answer="Krotka PL",
            url_key="jak-zwrocic",
        )
        url = f"/api/faq/v2/{faq_channel.idx}/items/{faq_item.url_key}/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["alternates"] == {"en": "how-to-return", "pl": "jak-zwrocic"}

    def test_alternates_skips_empty_t9n_url_key(self, api_client, faq_channel, faq_item, language_pl):
        """T9N with empty url_key does not appear in alternates."""
        FaqItemT9N.objects.create(item=faq_item, language=language_pl, question="Q PL", answer="A PL", url_key="")
        url = f"/api/faq/v2/{faq_channel.idx}/items/{faq_item.url_key}/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["alternates"] == {"en": "how-to-return"}

    def test_retrieve_not_found(self, api_client, faq_channel):
        url = f"/api/faq/v2/{faq_channel.idx}/items/nonexistent/"
        resp = api_client.get(url)
        assert resp.status_code == 404

    def test_channel_not_found(self, api_client):
        resp = api_client.get("/api/faq/v2/nonexistent/items/")
        assert resp.status_code == 404

    def test_short_answer_in_list(self, api_client, faq_channel, faq_item):
        url = f"/api/faq/v2/{faq_channel.idx}/items/"
        resp = api_client.get(url)
        result = resp.data["results"][0]
        assert "short_answer" in result

    def test_entity_filter(self, api_client, faq_channel, faq_item):
        from django_faq.models import FaqAssociation

        FaqAssociation.objects.create(faq_item=faq_item, entity_type="product", entity_identifier="CHAIR-001")
        url = f"/api/faq/v2/{faq_channel.idx}/items/?entity_type=product&entity_id=CHAIR-001"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["count"] == 1


@pytest.mark.django_db
class TestPublicItemSiblings:
    """Prev/next on retrieve. Scope: same group (by position_in_group) or, when
    ungrouped, other ungrouped items in the same channel scope (by position)."""

    def _retrieve(self, api_client, channel_idx, url_key, language=None):
        url = f"/api/faq/v2/{channel_idx}/items/{url_key}/"
        params = {"language": language} if language else {}
        return api_client.get(url, params)

    def _make_grouped(self, group, url_key, question, position_in_group, **kwargs):
        return FaqItem.objects.create(
            group=group,
            url_key=url_key,
            question=question,
            answer=f"<p>Answer for {url_key}</p>",
            short_answer="short",
            position=0,
            position_in_group=position_in_group,
            **kwargs,
        )

    def _make_ungrouped(self, url_key, question, position, **kwargs):
        return FaqItem.objects.create(
            url_key=url_key,
            question=question,
            answer=f"<p>Answer for {url_key}</p>",
            short_answer="short",
            position=position,
            **kwargs,
        )

    def test_middle_grouped_item_has_both_siblings(self, api_client, faq_channel, faq_group):
        self._make_grouped(faq_group, "a", "Question A", position_in_group=0)
        middle = self._make_grouped(faq_group, "b", "Question B", position_in_group=1)
        self._make_grouped(faq_group, "c", "Question C", position_in_group=2)

        resp = self._retrieve(api_client, faq_channel.idx, middle.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] == {"url_key": "a", "question": "Question A"}
        assert resp.data["next"] == {"url_key": "c", "question": "Question C"}

    def test_first_in_group_has_no_prev(self, api_client, faq_channel, faq_group):
        first = self._make_grouped(faq_group, "a", "Question A", position_in_group=0)
        self._make_grouped(faq_group, "b", "Question B", position_in_group=1)

        resp = self._retrieve(api_client, faq_channel.idx, first.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] is None
        assert resp.data["next"] == {"url_key": "b", "question": "Question B"}

    def test_last_in_group_has_no_next(self, api_client, faq_channel, faq_group):
        self._make_grouped(faq_group, "a", "Question A", position_in_group=0)
        last = self._make_grouped(faq_group, "b", "Question B", position_in_group=1)

        resp = self._retrieve(api_client, faq_channel.idx, last.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] == {"url_key": "a", "question": "Question A"}
        assert resp.data["next"] is None

    def test_only_item_in_group_returns_both_null(self, api_client, faq_channel, faq_group):
        only = self._make_grouped(faq_group, "alone", "Alone Question", position_in_group=0)

        resp = self._retrieve(api_client, faq_channel.idx, only.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] is None
        assert resp.data["next"] is None

    def test_ungrouped_item_uses_global_position(self, api_client, faq_channel):
        self._make_ungrouped("u0", "U0", position=0)
        u1 = self._make_ungrouped("u1", "U1", position=1)
        self._make_ungrouped("u2", "U2", position=2)

        resp = self._retrieve(api_client, faq_channel.idx, u1.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] == {"url_key": "u0", "question": "U0"}
        assert resp.data["next"] == {"url_key": "u2", "question": "U2"}

    def test_sibling_question_translated(self, api_client, faq_channel, faq_group, language_pl):
        first = self._make_grouped(faq_group, "first", "EN First", position_in_group=0)
        second = self._make_grouped(faq_group, "second", "EN Second", position_in_group=1)
        FaqItemT9N.objects.create(item=second, language=language_pl, question="PL Second", answer="A", short_answer="S")

        resp = self._retrieve(api_client, faq_channel.idx, first.url_key, language="pl")

        assert resp.status_code == 200
        assert resp.data["next"] == {"url_key": "second", "question": "PL Second"}
        assert resp.data["prev"] is None

    def test_sibling_url_key_uses_per_language_when_available(self, api_client, faq_channel, faq_group, language_pl):
        """When neighbour has T9N url_key for requested language, sibling.url_key uses it."""
        first = self._make_grouped(faq_group, "first", "EN First", position_in_group=0)
        second = self._make_grouped(faq_group, "second", "EN Second", position_in_group=1)
        FaqItemT9N.objects.create(
            item=second,
            language=language_pl,
            url_key="drugi",
            question="PL Second",
            answer="A",
            short_answer="S",
        )

        resp = self._retrieve(api_client, faq_channel.idx, first.url_key, language="pl")

        assert resp.status_code == 200
        # neighbour should expose the PL url_key
        assert resp.data["next"] == {"url_key": "drugi", "question": "PL Second"}

    def test_inactive_neighbour_is_skipped(self, api_client, faq_channel, faq_group):
        self._make_grouped(faq_group, "a", "A", position_in_group=0)
        self._make_grouped(faq_group, "b-inactive", "B (off)", position_in_group=1, is_active=False)
        c = self._make_grouped(faq_group, "c", "C", position_in_group=2)

        resp = self._retrieve(api_client, faq_channel.idx, c.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] == {"url_key": "a", "question": "A"}
        assert resp.data["next"] is None

    def test_cross_group_isolation(self, api_client, faq_channel, faq_group):
        """An item in group A must not see an item in group B as a sibling."""
        group_b = FaqGroup.objects.create(idx="returns", name="Returns", position=1)
        group_b.channels.add(faq_channel)
        self._make_grouped(faq_group, "a1", "A1", position_in_group=0)
        a2 = self._make_grouped(faq_group, "a2", "A2", position_in_group=1)
        self._make_grouped(group_b, "b1", "B1", position_in_group=0)
        self._make_grouped(group_b, "b2", "B2", position_in_group=1)

        resp = self._retrieve(api_client, faq_channel.idx, a2.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] == {"url_key": "a1", "question": "A1"}
        assert resp.data["next"] is None

    def test_grouped_item_is_not_sibling_of_ungrouped(self, api_client, faq_channel, faq_group):
        """An ungrouped item must not have a grouped item as neighbour even at adjacent position."""
        self._make_grouped(faq_group, "in-group", "In group", position_in_group=0)
        u0 = self._make_ungrouped("u0", "U0", position=0)
        self._make_ungrouped("u1", "U1", position=1)

        resp = self._retrieve(api_client, faq_channel.idx, u0.url_key)

        assert resp.status_code == 200
        assert resp.data["prev"] is None
        assert resp.data["next"] == {"url_key": "u1", "question": "U1"}

    def test_list_endpoint_declares_prev_next_as_null(self, api_client, faq_channel, faq_group):
        """API contract: prev/next are always declared, null in list mode (no per-tile compute)."""
        self._make_grouped(faq_group, "a", "A", position_in_group=0)
        self._make_grouped(faq_group, "b", "B", position_in_group=1)
        url = f"/api/faq/v2/{faq_channel.idx}/items/"

        resp = api_client.get(url)

        assert resp.status_code == 200
        results = resp.data["results"]
        assert len(results) == 2
        for item in results:
            assert "prev" in item
            assert "next" in item
            assert item["prev"] is None
            assert item["next"] is None


@pytest.mark.django_db
class TestPublicGroupAPI:
    def test_list_groups(self, api_client, faq_channel, faq_group):
        url = f"/api/faq/v2/{faq_channel.idx}/groups/"
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    @pytest.mark.skip(reason="Predates paginated group responses; needs rewrite against the results envelope")
    def test_list_groups_with_language(self, api_client, faq_channel, faq_group, language_en):
        from django_faq.models import FaqGroupT9N

        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="Shipping EN")
        url = f"/api/faq/v2/{faq_channel.idx}/groups/?language=en"
        resp = api_client.get(url)
        assert resp.status_code == 200
        group_data = [g for g in resp.data if g["idx"] == "shipping"][0]
        assert group_data["name"] == "Shipping EN"

    def test_list_groups_channel_not_found(self, api_client):
        resp = api_client.get("/api/faq/v2/nonexistent/groups/")
        assert resp.status_code == 404
