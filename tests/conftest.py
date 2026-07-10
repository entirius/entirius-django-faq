# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from django_faq.models import FaqChannel, FaqGroup, FaqItem

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="user", password="user123", email="user@test.com")


@pytest.fixture
def regular_client(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def language_en(db):
    from django_regional.models import Language

    lang, _ = Language.objects.get_or_create(
        iso2="en", defaults={"iso3": "eng", "name_en": "English", "name_pl": "Angielski", "name_source": "English"}
    )
    return lang


@pytest.fixture
def language_pl(db):
    from django_regional.models import Language

    lang, _ = Language.objects.get_or_create(
        iso2="pl", defaults={"iso3": "pol", "name_en": "Polish", "name_pl": "Polski", "name_source": "Polski"}
    )
    return lang


@pytest.fixture
def faq_channel(db, language_en, language_pl):
    ch = FaqChannel.objects.create(idx="test-channel", name="Test Channel", default_language=language_en)
    ch.languages.set([language_en, language_pl])
    return ch


@pytest.fixture
def faq_group(db, faq_channel):
    group = FaqGroup.objects.create(idx="shipping", name="Shipping & Delivery", position=0)
    group.channels.add(faq_channel)
    return group


@pytest.fixture
def faq_group_global(db):
    return FaqGroup.objects.create(idx="general", name="General", position=1)


@pytest.fixture
def faq_item(db, faq_group):
    return FaqItem.objects.create(
        group=faq_group,
        url_key="how-to-return",
        question="How do I return an item?",
        answer="<p>You can return items within 30 days.</p>",
        short_answer="Return within 30 days",
        position=0,
        position_in_group=0,
    )


@pytest.fixture
def faq_item_ungrouped(db):
    return FaqItem.objects.create(
        url_key="about-us",
        question="Who are you?",
        answer="<p>We are a company.</p>",
        short_answer="A company",
        position=1,
    )
