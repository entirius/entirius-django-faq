# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models
from django_utils.models.base_model import BaseModel


class FaqItem(BaseModel):
    """Single Q&A pair with optional image, url_key, and group membership."""

    group = models.ForeignKey(
        "django_faq.FaqGroup", on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    url_key = models.CharField(max_length=128, unique=True, db_index=True)
    question = models.CharField(max_length=512)
    answer = models.TextField()
    short_answer = models.CharField(max_length=512, blank=True, default="")
    image = models.ImageField(upload_to="faq/", null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    position_in_group = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "faq_item"
        ordering = ["position"]
        indexes = [
            models.Index(fields=["group", "position_in_group"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.url_key}: {self.question[:60]}"
