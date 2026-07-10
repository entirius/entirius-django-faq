# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Import FAQ items from CSV. Supports grouped CSV with url_key and per-row group columns."""

import csv
import re
from unicodedata import normalize

from django.core.management.base import BaseCommand
from django.db import transaction

from django_faq.models import FaqChannel, FaqGroup, FaqItem


def _slugify(text: str) -> str:
    """Generate url_key from question text."""
    slug = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", slug).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug[:128] or "faq-item"


def _unique_url_key(base: str, existing: set[str]) -> str:
    """Append -2, -3 etc. on collision. Checks in-memory set."""
    candidate = base
    counter = 2
    while candidate in existing:
        suffix = f"-{counter}"
        candidate = base[: 128 - len(suffix)] + suffix
        counter += 1
    return candidate


class Command(BaseCommand):
    help = "Import FAQ items from CSV (supports url_key and group columns)"
    BATCH_SIZE = 500

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="Path to CSV file")
        parser.add_argument("--channel", required=False, help="Channel idx to scope groups to")
        parser.add_argument("--group", required=False, help="Default group idx (used when CSV has no group column)")

    def handle(self, *args, **options):
        csv_path = options["csv"]
        default_group_idx = options.get("group")
        channel_idx = options.get("channel")

        existing_keys = set(FaqItem.objects.values_list("url_key", flat=True))
        groups_cache: dict[str, FaqGroup] = {}
        batch: list[FaqItem] = []
        skipped = 0
        position = 0

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for position, row in enumerate(reader):
                question = row.get("question", "").strip()
                answer = row.get("answer", "").strip()
                is_active = row.get("publish", "f").strip().lower() == "t"

                if not question:
                    skipped += 1
                    continue

                url_key = row.get("url_key", "").strip()
                if not url_key:
                    url_key = _unique_url_key(_slugify(question), existing_keys)
                existing_keys.add(url_key)

                group_idx = row.get("group", "").strip() or default_group_idx
                group = None
                if group_idx:
                    group = self._get_or_create_group(group_idx, groups_cache)

                batch.append(
                    FaqItem(
                        group=group,
                        url_key=url_key,
                        question=question,
                        answer=answer,
                        is_active=is_active,
                        position=position,
                    )
                )
                if len(batch) >= self.BATCH_SIZE:
                    self._flush(batch)
                    batch.clear()

        if batch:
            self._flush(batch)

        if channel_idx:
            self._assign_channel(channel_idx, groups_cache)

        imported = position + 1 - skipped
        self.stdout.write(f"Imported {imported} FAQ items, skipped {skipped}")

    def _get_or_create_group(self, idx: str, cache: dict[str, FaqGroup]) -> FaqGroup:
        if idx not in cache:
            group, created = FaqGroup.objects.get_or_create(idx=idx, defaults={"name": idx.replace("-", " ").title()})
            cache[idx] = group
            if created:
                self.stdout.write(f"Created group: {idx}")
        return cache[idx]

    def _assign_channel(self, channel_idx: str, groups: dict[str, FaqGroup]) -> None:
        try:
            channel = FaqChannel.objects.get(idx=channel_idx)
            for group in groups.values():
                group.channels.add(channel)
        except FaqChannel.DoesNotExist:
            self.stderr.write(f"Channel {channel_idx} not found, skipping channel assignment")

    @transaction.atomic
    def _flush(self, batch: list[FaqItem]) -> None:
        FaqItem.objects.bulk_create(batch, batch_size=self.BATCH_SIZE)
