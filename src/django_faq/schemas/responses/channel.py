# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, ConfigDict, Field


class FaqChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Channel PK", examples=[1])
    idx: str = Field(description="Channel identifier", examples=["default-europe"])
    name: str = Field(description="Display name", examples=["Default Europe"])
    language_codes: list[str] = Field(
        default_factory=list, description="Available language ISO2 codes", examples=[["en", "pl"]]
    )
    default_language: str | None = Field(None, description="Default language ISO2", examples=["en"])


class FaqChannelListResponse(BaseModel):
    count: int = Field(description="Total item count", examples=[2])
    next: str | None = Field(None, description="Next page URL", examples=[None])
    previous: str | None = Field(None, description="Previous page URL", examples=[None])
    results: list[FaqChannelResponse] = Field(description="Page results")
