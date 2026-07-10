# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from django_faq.models import FaqGroup, FaqGroupT9N, FaqItem, FaqItemT9N
from django_faq.services import association_service, group_service, item_service


@pytest.mark.django_db
class TestGroupService:
    def test_create_group(self, faq_channel):
        group = group_service.create_group(idx="new-group", name="New Group", channel_ids=[faq_channel.pk])
        assert group.idx == "new-group"
        assert faq_channel in group.channels.all()

    def test_list_groups_channel_scoped(self, faq_group, faq_group_global, faq_channel):
        groups = list(group_service.list_groups(channel_idx=faq_channel.idx, is_active=None))
        idxs = [g.idx for g in groups]
        assert "shipping" in idxs
        assert "general" in idxs  # global (empty channels)

    def test_update_group(self, faq_group):
        updated = group_service.update_group(idx="shipping", name="Updated Name")
        assert updated.name == "Updated Name"

    def test_update_group_rejects_unknown_field(self, faq_group):
        with pytest.raises(ValueError, match="Cannot update field"):
            group_service.update_group(idx="shipping", pk=999)

    def test_delete_group(self, faq_group):
        group_service.delete_group(idx="shipping")
        assert FaqGroup.objects.filter(idx="shipping").count() == 0

    def test_reorder_groups(self):
        FaqGroup.objects.create(idx="a", name="A", position=0)
        FaqGroup.objects.create(idx="b", name="B", position=1)
        group_service.reorder_groups(ordered_idxs=["b", "a"])
        assert FaqGroup.objects.get(idx="b").position == 0
        assert FaqGroup.objects.get(idx="a").position == 1

    def test_create_group_translation(self, faq_group, language_en):
        t9n = group_service.create_group_translation(group_idx="shipping", language_iso2="en", name="Shipping EN")
        assert t9n.name == "Shipping EN"

    def test_list_group_translations(self, faq_group, language_en):
        group_service.create_group_translation(group_idx="shipping", language_iso2="en", name="Shipping EN")
        t9ns = list(group_service.list_group_translations(group_idx="shipping"))
        assert len(t9ns) == 1

    def test_update_group_translation(self, faq_group, language_en):
        group_service.create_group_translation(group_idx="shipping", language_iso2="en", name="Shipping EN")
        updated = group_service.update_group_translation(group_idx="shipping", language_iso2="en", name="Updated")
        assert updated.name == "Updated"

    def test_delete_group_translation(self, faq_group, language_en):
        group_service.create_group_translation(group_idx="shipping", language_iso2="en", name="Shipping EN")
        group_service.delete_group_translation(group_idx="shipping", language_iso2="en")
        assert FaqGroupT9N.objects.count() == 0

    def test_resolve_group_name_no_language(self, faq_group):
        assert group_service.resolve_group_name(faq_group) == faq_group.name

    def test_resolve_group_name_none(self):
        assert group_service.resolve_group_name(None) == ""


@pytest.mark.django_db
class TestItemService:
    def test_create_item(self, faq_group):
        item = item_service.create_item(url_key="new-q", question="New?", answer="Yes.", group_idx="shipping")
        assert item.url_key == "new-q"
        assert item.group == faq_group

    def test_create_item_with_associations(self, faq_group):
        item = item_service.create_item(
            url_key="assoc-q",
            question="Q?",
            answer="A.",
            associations=[{"entity_type": "product", "entity_identifier": "SKU-1"}],
        )
        assert item.associations.count() == 1

    def test_list_items_by_group(self, faq_item, faq_item_ungrouped):
        items = list(item_service.list_items(group_idx="shipping", is_active=None))
        assert len(items) == 1
        assert items[0].url_key == "how-to-return"

    def test_list_items_channel_scoped(self, faq_item, faq_item_ungrouped, faq_channel):
        items = list(item_service.list_items(channel_idx=faq_channel.idx, is_active=None))
        url_keys = [i.url_key for i in items]
        assert "how-to-return" in url_keys
        assert "about-us" in url_keys  # ungrouped = visible everywhere

    def test_get_item_by_url_key(self, faq_item, faq_channel):
        item = item_service.get_item_by_url_key(url_key="how-to-return", channel_idx=faq_channel.idx)
        assert item.pk == faq_item.pk

    def test_update_item(self, faq_item):
        updated = item_service.update_item(pk=faq_item.pk, question="Updated question?")
        assert updated.question == "Updated question?"

    def test_update_item_rejects_unknown_field(self, faq_item):
        with pytest.raises(ValueError, match="Cannot update field"):
            item_service.update_item(pk=faq_item.pk, id=999)

    def test_delete_item(self, faq_item):
        item_service.delete_item(pk=faq_item.pk)
        assert FaqItem.objects.filter(pk=faq_item.pk).count() == 0

    def test_reorder_items(self):
        i1 = FaqItem.objects.create(url_key="r1", question="Q1", answer="A1", position=0)
        i2 = FaqItem.objects.create(url_key="r2", question="Q2", answer="A2", position=1)
        item_service.reorder_items(ordered_pks=[i2.pk, i1.pk])
        assert FaqItem.objects.get(pk=i2.pk).position == 0
        assert FaqItem.objects.get(pk=i1.pk).position == 1


@pytest.mark.django_db
class TestTranslationResolution:
    def test_no_language_returns_base(self, faq_item, faq_channel):
        result = item_service.resolve_translation(faq_item)
        assert result["question"] == faq_item.question

    def test_requested_language_found(self, faq_item, faq_channel, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="en")
        assert result["question"] == "Q EN"

    def test_fallback_to_channel_default(self, faq_item, faq_channel, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="de")
        assert result["question"] == "Q EN"

    def test_fallback_to_base(self, faq_item, faq_channel):
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="de")
        assert result["question"] == faq_item.question

    def test_empty_t9n_field_falls_back(self, faq_item, faq_channel, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="", answer="A EN")
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="en")
        assert result["question"] == faq_item.question
        assert result["answer"] == "A EN"

    def test_create_item_translation(self, faq_item, language_en):
        t9n = item_service.create_item_translation(
            item_pk=faq_item.pk, language_iso2="en", question="Q EN", answer="A EN"
        )
        assert t9n.question == "Q EN"

    def test_list_item_translations(self, faq_item, language_en):
        item_service.create_item_translation(item_pk=faq_item.pk, language_iso2="en", question="Q", answer="A")
        t9ns = list(item_service.list_item_translations(item_pk=faq_item.pk))
        assert len(t9ns) == 1

    def test_update_item_translation(self, faq_item, language_en):
        item_service.create_item_translation(item_pk=faq_item.pk, language_iso2="en", question="Q", answer="A")
        updated = item_service.update_item_translation(item_pk=faq_item.pk, language_iso2="en", question="Updated Q")
        assert updated.question == "Updated Q"

    def test_delete_item_translation(self, faq_item, language_en):
        item_service.create_item_translation(item_pk=faq_item.pk, language_iso2="en", question="Q", answer="A")
        item_service.delete_item_translation(item_pk=faq_item.pk, language_iso2="en")
        assert FaqItemT9N.objects.count() == 0

    def test_t9n_url_key_resolves_in_translation(self, faq_item, faq_channel, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, url_key="how-to-x", question="Q", answer="A")
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="en")
        assert result["url_key"] == "how-to-x"

    def test_t9n_empty_url_key_falls_back_to_base(self, faq_item, faq_channel, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q", answer="A")
        item = item_service.get_item(pk=faq_item.pk)
        result = item_service.resolve_translation(item, channel=faq_channel, language_iso2="en")
        assert result["url_key"] == faq_item.url_key

    def test_get_item_by_t9n_url_key(self, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, url_key="how-to-x", question="Q", answer="A")
        found = item_service.get_item_by_url_key(url_key="how-to-x", language_iso2="en")
        assert found.pk == faq_item.pk

    def test_get_item_by_url_key_falls_back_to_base(self, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q", answer="A")
        found = item_service.get_item_by_url_key(url_key=faq_item.url_key, language_iso2="en")
        assert found.pk == faq_item.pk

    def test_t9n_url_key_not_matched_for_other_language(self, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, url_key="how-to-x", question="Q", answer="A")
        with pytest.raises(FaqItem.DoesNotExist):
            item_service.get_item_by_url_key(url_key="how-to-x", language_iso2="pl")


@pytest.mark.django_db
class TestAssociationService:
    def test_validate_entity_without_pim(self):
        """Without PIM installed, validation always returns True."""
        assert association_service.validate_entity("product", "ANY-SKU") is True

    def test_discover_without_pim(self):
        """Without PIM installed, discovery returns empty."""
        results = association_service.discover_entities("product", "chair")
        assert results == []
