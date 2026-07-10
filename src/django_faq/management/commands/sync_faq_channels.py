# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.core.management.base import BaseCommand

from django_faq.services import channel_service


class Command(BaseCommand):
    help = "Sync FAQ channels from PIM"

    def handle(self, *args, **options):
        count = channel_service.sync_channels_from_pim()
        self.stdout.write(f"Synced {count} FAQ channels from PIM")
