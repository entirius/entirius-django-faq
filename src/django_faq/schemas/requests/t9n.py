# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, Field


class FaqGroupT9NCreateRequest(BaseModel):
    language: str = Field(min_length=2, max_length=2, description="Language ISO2", examples=["en"])
    name: str = Field(min_length=1, max_length=128, description="Translated group name", examples=["Shipping"])


class FaqGroupT9NUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=128, description="Translated group name", examples=["Shipping"])


class FaqItemT9NCreateRequest(BaseModel):
    language: str = Field(min_length=2, max_length=2, description="Language ISO2", examples=["en"])
    url_key: str = Field(
        default="",
        max_length=128,
        description="Per-language SEO slug. Empty = fall back to base item url_key.",
        examples=["how-to-return"],
    )
    question: str = Field(
        min_length=1, max_length=512, description="Translated question", examples=["How do I return?"]
    )
    answer: str = Field(
        min_length=1, description="Translated answer (HTML)", examples=["<p>Return within 30 days.</p>"]
    )
    short_answer: str = Field(
        default="", max_length=512, description="Translated short answer", examples=["Return within 30 days"]
    )


class FaqItemT9NUpdateRequest(BaseModel):
    url_key: str | None = Field(
        None,
        max_length=128,
        description="Per-language SEO slug. Empty = fall back to base item url_key.",
        examples=["how-to-return"],
    )
    question: str | None = Field(None, max_length=512, description="Translated question", examples=["How do I return?"])
    answer: str | None = Field(None, description="Translated answer (HTML)", examples=["<p>Return within 30 days.</p>"])
    short_answer: str | None = Field(
        None, max_length=512, description="Translated short answer", examples=["Return within 30 days"]
    )
