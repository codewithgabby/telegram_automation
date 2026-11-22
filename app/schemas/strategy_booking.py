import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyBookingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    whatsapp: str = Field(min_length=9, max_length=16)
    country: str = Field(min_length=2, max_length=100)
    package_code: str = Field(min_length=1, max_length=30)
    case_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address.")

        return value

    @field_validator("whatsapp")
    @classmethod
    def validate_whatsapp(cls, value: str) -> str:
        if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
            raise ValueError("Use international format, for example +2348012345678.")

        return value

    @field_validator("package_code")
    @classmethod
    def validate_package_code(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9_-]{1,30}", value):
            raise ValueError("Invalid consultation package code.")

        return value


class StrategyBookingCreateResponse(BaseModel):
    booking_reference: str
    package_name: str
    amount_ngn: int
    session_count: int
    status: str
    continuation_url: str
    message: str
