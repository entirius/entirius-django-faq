# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import BaseModel, ConfigDict, Field


class FaqItemT9NResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str = Field(description="Language ISO2", examples=["en"])
    url_key: str = Field(
        default="",
        description="Per-language SEO slug. Empty = fall back to base item url_key.",
        examples=["how-to-return"],
    )
    question: str = Field(description="Translated question", examples=["How do I return?"])
    answer: str = Field(description="Translated answer (HTML)", examples=["<p>Return within 30 days.</p>"])
    short_answer: str = Field(default="", description="Translated short answer", examples=["Return within 30 days"])


class FaqAssociationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_type: str = Field(description="Entity type", examples=["product"])
    entity_identifier: str = Field(description="Entity identifier", examples=["CHAIR-001"])


class FaqItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Item PK", examples=[1])
    url_key: str = Field(description="SEO-friendly URL slug", examples=["how-to-return"])
    question: str = Field(description="Base question text", examples=["How do I return an item?"])
    answer: str = Field(description="Base full answer (HTML)", examples=["<p>Return within 30 days.</p>"])
    short_answer: str = Field(default="", description="Short answer", examples=["Return within 30 days"])
    image_url: str | None = Field(None, description="Image URL", examples=["/media/faq/returns.jpg"])
    group_idx: str | None = Field(None, description="Group identifier", examples=["shipping"])
    group_name: str | None = Field(None, description="Group display name", examples=["Shipping & Delivery"])
    position: int = Field(description="Global sort order", examples=[0])
    position_in_group: int = Field(description="Position within group", examples=[0])
    is_active: bool = Field(description="Whether item is active", examples=[True])
    translations: list[FaqItemT9NResponse] = Field(default_factory=list, description="Translations")
    associations: list[FaqAssociationResponse] = Field(default_factory=list, description="Entity associations")


class FaqItemListResponse(BaseModel):
    count: int = Field(description="Total item count", examples=[42])
    next: str | None = Field(None, description="Next page URL", examples=["?page=2"])
    previous: str | None = Field(None, description="Previous page URL", examples=[None])
    results: list[FaqItemResponse] = Field(description="Page results")


class FaqSiblingResponse(BaseModel):
    """Minimal shape for prev/next neighbour link on item detail."""

    model_config = ConfigDict(from_attributes=True)

    url_key: str = Field(
        description="SEO slug of the neighbour (per-language when available)", examples=["how-to-return"]
    )
    question: str = Field(description="Neighbour question (resolved)", examples=["How do I return?"])


class PublicFaqItemResponse(BaseModel):
    """Public API response — resolved translations, no admin fields."""

    model_config = ConfigDict(from_attributes=True)

    url_key: str = Field(description="SEO-friendly URL slug", examples=["how-to-return"])
    question: str = Field(description="Resolved question", examples=["How do I return an item?"])
    answer: str = Field(description="Resolved full answer (HTML)", examples=["<p>Return within 30 days.</p>"])
    short_answer: str = Field(default="", description="Resolved short answer", examples=["Return within 30 days"])
    image_url: str | None = Field(None, description="Image URL", examples=["/media/faq/returns.jpg"])
    group_idx: str | None = Field(None, description="Group identifier", examples=["shipping"])
    group_name: str | None = Field(None, description="Group name (resolved)", examples=["Shipping & Delivery"])
    alternates: dict[str, str] = Field(
        default_factory=dict,
        description="Per-locale slug map for hreflang and canonical redirects. "
        "Keys are ISO2 language codes; values are the url_key for that locale. "
        "Includes channel default language (mapped to base url_key) and any t9n url_keys.",
        examples=[{"pl": "atrybucja-w-e-commerce", "en": "what-is-attribution-for-an-online-store"}],
    )
    associations: list[FaqAssociationResponse] = Field(default_factory=list, description="Entity associations")
    prev: FaqSiblingResponse | None = Field(
        default=None,
        description="Previous item (lower position_in_group when grouped, lower position when ungrouped). null at boundary.",
    )
    next: FaqSiblingResponse | None = Field(
        default=None,
        description="Next item (higher position_in_group when grouped, higher position when ungrouped). null at boundary.",
    )


class PublicFaqItemListResponse(BaseModel):
    count: int = Field(description="Total item count", examples=[42])
    next: str | None = Field(None, description="Next page URL", examples=["?page=2"])
    previous: str | None = Field(None, description="Previous page URL", examples=[None])
    results: list[PublicFaqItemResponse] = Field(description="Page results")


class PublicFaqGroupResponse(BaseModel):
    """Public API group with item count."""

    idx: str = Field(description="Group identifier", examples=["shipping"])
    name: str = Field(description="Group name (resolved)", examples=["Shipping & Delivery"])
    item_count: int = Field(default=0, description="Number of active items", examples=[5])


class PublicFaqGroupListResponse(BaseModel):
    count: int = Field(description="Total item count", examples=[2])
    next: str | None = Field(None, description="Next page URL", examples=[None])
    previous: str | None = Field(None, description="Previous page URL", examples=[None])
    results: list[PublicFaqGroupResponse] = Field(description="Page results")


class DiscoverResult(BaseModel):
    identifier: str = Field(description="Entity identifier", examples=["CHAIR-001"])
    label: str = Field(description="Display label", examples=["CHAIR-001 — Ergonomic Office Chair"])


class DiscoverResponse(BaseModel):
    results: list[DiscoverResult] = Field(default_factory=list, description="Discovery results")
