# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models
from django_utils.models.base_model import BaseModel


class FaqGroup(BaseModel):
    """Thematic FAQ collection — organizes items like PIM FeatureSet organizes features."""

    idx = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    channels = models.ManyToManyField("django_faq.FaqChannel", blank=True, related_name="groups")
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "faq_group"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return f"{self.idx} — {self.name}"
