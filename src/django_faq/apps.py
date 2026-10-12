# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.apps import AppConfig


class DjangoFaqConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_faq"
    verbose_name = "FAQ"
    is_volkanos = True
    # Copied 1:1 from entirius-django-access cf538d2 catalogue defaults;
    # the access defaults stay until this module's release.
    access_areas = [
        {"key": "faq.faq", "label": "FAQ"},
    ]
    # Every admin view carries its access_area; no route needs a path rule.
    access_route_rules = []
