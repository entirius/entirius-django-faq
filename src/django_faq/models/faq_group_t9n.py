# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models
from django_utils.models.base_model import BaseModel


class FaqGroupT9N(BaseModel):
    """Translation row for FaqGroup — one per language."""

    group = models.ForeignKey("django_faq.FaqGroup", on_delete=models.CASCADE, related_name="translations")
    language = models.ForeignKey("django_regional.Language", on_delete=models.CASCADE, related_name="+")
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "faq_group_t9n"
        constraints = [models.UniqueConstraint(fields=["group", "language"], name="unique_faq_group_language")]

    def __str__(self) -> str:
        return f"{self.group.idx} [{self.language}]"
