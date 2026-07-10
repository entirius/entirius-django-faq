# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Literal

from pydantic import BaseModel, Field

ENTITY_TYPES = Literal["product", "category", "blog-post", "page"]


class AssociationInput(BaseModel):
    entity_type: ENTITY_TYPES = Field(description="Entity type", examples=["product"])
    entity_identifier: str = Field(description="Entity identifier", examples=["CHAIR-001"])


class FaqItemCreateRequest(BaseModel):
    url_key: str = Field(min_length=1, max_length=128, description="SEO-friendly URL slug", examples=["how-to-return"])
    question: str = Field(
        min_length=1, max_length=512, description="Base question text", examples=["How do I return an item?"]
    )
    answer: str = Field(
        min_length=1, description="Base full answer (HTML)", examples=["<p>You can return items within 30 days.</p>"]
    )
    short_answer: str = Field(
        default="", max_length=512, description="Short answer for list views", examples=["Return within 30 days"]
    )
    group_idx: str | None = Field(None, description="Group idx (null = ungrouped)", examples=["shipping"])
    position: int = Field(default=0, ge=0, description="Global sort order", examples=[0])
    position_in_group: int = Field(default=0, ge=0, description="Position within group", examples=[0])
    is_active: bool = Field(default=True, description="Whether item is active", examples=[True])
    associations: list[AssociationInput] = Field(default_factory=list, description="Entity associations")


class FaqItemUpdateRequest(BaseModel):
    url_key: str | None = Field(None, max_length=128, description="SEO-friendly URL slug", examples=["how-to-return"])
    question: str | None = Field(
        None, max_length=512, description="Base question text", examples=["How do I return an item?"]
    )
    answer: str | None = Field(None, description="Base full answer (HTML)", examples=["<p>Updated answer.</p>"])
    short_answer: str | None = Field(
        None, max_length=512, description="Short answer", examples=["Return within 30 days"]
    )
    group_idx: str | None = Field(None, description="Group idx (null = ungrouped)", examples=["shipping"])
    position: int | None = Field(None, ge=0, description="Global sort order", examples=[0])
    position_in_group: int | None = Field(None, ge=0, description="Position within group", examples=[0])
    is_active: bool | None = Field(None, description="Whether item is active", examples=[True])
    associations: list[AssociationInput] | None = Field(None, description="Entity associations (replaces all)")


class ItemReorderRequest(BaseModel):
    ordered_pks: list[int] = Field(description="Item PKs in desired order", examples=[[3, 1, 2]])
    within_group: bool = Field(default=False, description="If true, updates position_in_group instead of position")
