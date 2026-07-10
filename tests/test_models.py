# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from django.db import IntegrityError

from django_faq.models import FaqAssociation, FaqChannel, FaqGroup, FaqGroupT9N, FaqItem, FaqItemT9N


@pytest.mark.django_db
class TestFaqChannel:
    def test_create(self):
        ch = FaqChannel.objects.create(idx="my-channel", name="My Channel")
        assert ch.idx == "my-channel"
        assert str(ch) == "my-channel"

    def test_idx_unique(self):
        FaqChannel.objects.create(idx="unique-ch")
        with pytest.raises(IntegrityError):
            FaqChannel.objects.create(idx="unique-ch")


@pytest.mark.django_db
class TestFaqGroup:
    def test_create(self, faq_channel):
        group = FaqGroup.objects.create(idx="returns", name="Returns")
        group.channels.add(faq_channel)
        assert group.idx == "returns"
        assert str(group) == "returns — Returns"
        assert faq_channel in group.channels.all()

    def test_idx_unique(self):
        FaqGroup.objects.create(idx="dup-group", name="A")
        with pytest.raises(IntegrityError):
            FaqGroup.objects.create(idx="dup-group", name="B")

    def test_ordering(self):
        FaqGroup.objects.create(idx="g2", name="B", position=2)
        FaqGroup.objects.create(idx="g1", name="A", position=1)
        groups = list(FaqGroup.objects.all())
        assert groups[0].idx == "g1"


@pytest.mark.django_db
class TestFaqGroupT9N:
    def test_create(self, faq_group, language_en):
        t9n = FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="Shipping EN")
        assert str(t9n) == f"{faq_group.idx} [{language_en}]"

    def test_unique_constraint(self, faq_group, language_en):
        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="A")
        with pytest.raises(IntegrityError):
            FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="B")

    def test_cascade_delete(self, faq_group, language_en):
        FaqGroupT9N.objects.create(group=faq_group, language=language_en, name="A")
        faq_group.delete()
        assert FaqGroupT9N.objects.count() == 0


@pytest.mark.django_db
class TestFaqItem:
    def test_create(self, faq_group):
        item = FaqItem.objects.create(group=faq_group, url_key="test-q", question="Test?", answer="Yes.")
        assert item.url_key == "test-q"
        assert item.group == faq_group

    def test_url_key_unique(self):
        FaqItem.objects.create(url_key="dup-key", question="Q1?", answer="A1")
        with pytest.raises(IntegrityError):
            FaqItem.objects.create(url_key="dup-key", question="Q2?", answer="A2")

    def test_nullable_group(self):
        item = FaqItem.objects.create(url_key="no-group", question="Q?", answer="A")
        assert item.group is None

    def test_str(self):
        item = FaqItem.objects.create(url_key="my-key", question="What is FAQ?", answer="A")
        assert "my-key" in str(item)


@pytest.mark.django_db
class TestFaqItemT9N:
    def test_create(self, faq_item, language_en):
        t9n = FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q EN", answer="A EN")
        assert str(t9n) == f"{faq_item.url_key} [{language_en}]"

    def test_unique_constraint(self, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q", answer="A")
        with pytest.raises(IntegrityError):
            FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q2", answer="A2")

    def test_cascade_delete(self, faq_item, language_en):
        FaqItemT9N.objects.create(item=faq_item, language=language_en, question="Q", answer="A")
        faq_item.delete()
        assert FaqItemT9N.objects.count() == 0


@pytest.mark.django_db
class TestFaqAssociation:
    def test_create(self, faq_item):
        assoc = FaqAssociation.objects.create(faq_item=faq_item, entity_type="product", entity_identifier="CHAIR-001")
        assert str(assoc) == "product:CHAIR-001"

    def test_unique_constraint(self, faq_item):
        FaqAssociation.objects.create(faq_item=faq_item, entity_type="product", entity_identifier="SKU-1")
        with pytest.raises(IntegrityError):
            FaqAssociation.objects.create(faq_item=faq_item, entity_type="product", entity_identifier="SKU-1")

    def test_cascade_delete(self, faq_item):
        FaqAssociation.objects.create(faq_item=faq_item, entity_type="product", entity_identifier="SKU-1")
        faq_item.delete()
        assert FaqAssociation.objects.count() == 0
