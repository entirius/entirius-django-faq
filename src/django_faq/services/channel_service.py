# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""FAQ channel management — sync from PIM, list, get."""

import logging

from django.db.models import QuerySet

from django_faq.models import FaqChannel

logger = logging.getLogger(__name__)


def list_channels() -> QuerySet[FaqChannel]:
    return FaqChannel.objects.all()


def get_channel(channel_idx: str) -> FaqChannel:
    """Get channel by idx. Raises FaqChannel.DoesNotExist."""
    return FaqChannel.objects.get(idx=channel_idx)


def get_channels_by_pks(pks: list[int]) -> QuerySet[FaqChannel]:
    return FaqChannel.objects.filter(pk__in=pks)


def sync_channels_from_pim() -> int:
    """Sync FaqChannels from PIM Channel model.

    Creates or updates local channels keyed by idx.
    Returns count of synced channels.
    """
    try:
        from django_pim.models import Channel
    except ImportError:
        logger.info("django_pim not installed, skipping FAQ channel sync")
        return 0

    from django_regional.models import Language

    count = 0
    for pim_channel in Channel.objects.prefetch_related("languages").all():
        local_lang = None
        if pim_channel.default_language:
            local_lang = Language.objects.filter(iso2__iexact=pim_channel.default_language.iso2).first()

        faq_channel, _ = FaqChannel.objects.update_or_create(
            idx=pim_channel.idx, defaults={"name": pim_channel.name, "default_language": local_lang}
        )

        pim_lang_iso2s = list(pim_channel.languages.values_list("iso2", flat=True))
        local_langs = Language.objects.filter(iso2__in=pim_lang_iso2s)
        faq_channel.languages.set(local_langs)

        count += 1

    return count
