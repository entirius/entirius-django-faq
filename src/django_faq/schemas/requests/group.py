# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, Field


class FaqGroupCreateRequest(BaseModel):
    idx: str = Field(min_length=1, max_length=128, description="Unique slug identifier", examples=["shipping"])
    name: str = Field(min_length=1, max_length=128, description="Display name", examples=["Shipping & Delivery"])
    channel_ids: list[int] = Field(default_factory=list, description="Channel PKs (empty = global)", examples=[[1, 2]])
    position: int = Field(default=0, ge=0, description="Sort order", examples=[0])
    is_active: bool = Field(default=True, description="Whether group is active", examples=[True])


class FaqGroupUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=128, description="Display name", examples=["Shipping & Delivery"])
    channel_ids: list[int] | None = Field(None, description="Channel PKs (empty = global)", examples=[[1, 2]])
    position: int | None = Field(None, ge=0, description="Sort order", examples=[0])
    is_active: bool | None = Field(None, description="Whether group is active", examples=[True])


class GroupReorderRequest(BaseModel):
    ordered_idxs: list[str] = Field(
        description="Group idxs in desired order", examples=[["shipping", "returns", "general"]]
    )
