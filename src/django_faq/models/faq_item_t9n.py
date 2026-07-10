# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models
from django_utils.models.base_model import BaseModel


class FaqItemT9N(BaseModel):
    """Translation row for FaqItem — one per language.

    Optional ``url_key`` overrides the base FaqItem.url_key for SEO when set.
    Empty url_key means: fall back to base FaqItem.url_key for this language.
    """

    item = models.ForeignKey("django_faq.FaqItem", on_delete=models.CASCADE, related_name="translations")
    language = models.ForeignKey("django_regional.Language", on_delete=models.CASCADE, related_name="+")
    url_key = models.CharField(
        max_length=128,
        blank=True,
        default="",
        db_index=True,
        help_text="Per-language SEO slug. Empty = fall back to base FaqItem.url_key.",
    )
    question = models.CharField(max_length=512)
    answer = models.TextField()
    short_answer = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        db_table = "faq_item_t9n"
        constraints = [
            models.UniqueConstraint(fields=["item", "language"], name="unique_faq_item_language"),
            models.UniqueConstraint(
                fields=["language", "url_key"],
                name="unique_faq_t9n_url_key_per_language",
                condition=~models.Q(url_key=""),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.item.url_key} [{self.language}]"
