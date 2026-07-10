# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db import models
from django_utils.models.base_model import BaseModel


class EntityType(models.TextChoices):
    PRODUCT = "product", "Product"
    CATEGORY = "category", "Category"
    BLOG_POST = "blog-post", "Blog Post"
    PAGE = "page", "Page"


class FaqAssociation(BaseModel):
    """Soft reference to an external entity (product, category, blog-post, page).

    Uses string identifiers instead of hard FKs — module works standalone.
    When PIM/ContentDB are present, services validate identifiers.
    """

    faq_item = models.ForeignKey("django_faq.FaqItem", on_delete=models.CASCADE, related_name="associations")
    entity_type = models.CharField(max_length=32, choices=EntityType.choices)
    entity_identifier = models.CharField(max_length=128)

    class Meta:
        db_table = "faq_association"
        constraints = [
            models.UniqueConstraint(
                fields=["faq_item", "entity_type", "entity_identifier"], name="unique_faq_association"
            )
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_identifier}"
