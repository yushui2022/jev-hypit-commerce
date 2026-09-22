from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Item(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    kind: Literal["product", "creator"]
    name: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    image: str = Field(default="", max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=30)
    market: str = Field(default="US", max_length=12)
    language: str = Field(default="en", max_length=12)
    active: bool = True
    sheet_cell: int | None = Field(default=None, ge=0, le=19)

    @field_validator("tags")
    @classmethod
    def tags_bounded(cls, v):
        if any(not t or len(t) > 100 for t in v):
            raise ValueError("Each tag must contain 1–100 characters")
        return list(dict.fromkeys(v))


class CatalogImport(BaseModel):
    items: list[Item] = Field(min_length=1, max_length=1000)


class MatchRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    top_k: int = Field(default=8, ge=1, le=30)
    engine: Literal["baseline", "jev"] = "baseline"
    market: str | None = Field(default=None, max_length=12)
    language: str | None = Field(default=None, max_length=12)


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    creator_id: str | None = Field(default=None, max_length=64)
    note: str = Field(default="", max_length=1000)


class RenderRequest(BaseModel):
    match_job_id: str = Field(min_length=1, max_length=64)
