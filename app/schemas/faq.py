from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class FAQCreate(BaseModel):
    topic: str = Field(
        min_length=2,
        max_length=255,
    )

    keywords: list[str] = Field(
        min_length=1,
    )

    message_link: HttpUrl


class FAQUpdate(BaseModel):
    topic: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    keywords: list[str] | None = None

    message_link: HttpUrl | None = None

    is_active: bool | None = None


class FAQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    keywords: list[str]
    message_link: str
    is_active: bool
    created_at: datetime
