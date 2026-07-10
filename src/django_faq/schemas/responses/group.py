# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, ConfigDict, Field


class FaqGroupT9NResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str = Field(description="Language ISO2", examples=["en"])
    name: str = Field(description="Translated group name", examples=["Shipping"])


class FaqGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Group PK", examples=[1])
    idx: str = Field(description="Group identifier", examples=["shipping"])
    name: str = Field(description="Base group name", examples=["Shipping & Delivery"])
    translations: list[FaqGroupT9NResponse] = Field(default_factory=list, description="Translations")
    channel_ids: list[int] = Field(default_factory=list, description="Channel PKs (empty = global)", examples=[[1]])
    position: int = Field(description="Sort order", examples=[0])
    is_active: bool = Field(description="Whether group is active", examples=[True])
    item_count: int = Field(default=0, description="Number of items in group", examples=[5])


class FaqGroupListResponse(BaseModel):
    count: int = Field(description="Total item count", examples=[42])
    next: str | None = Field(None, description="Next page URL", examples=["?page=2"])
    previous: str | None = Field(None, description="Previous page URL", examples=[None])
    results: list[FaqGroupResponse] = Field(description="Page results")
