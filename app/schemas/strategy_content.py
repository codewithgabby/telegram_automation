from pydantic import BaseModel, Field, ConfigDict


class StrategyServiceCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=1000)
    price_ngn: int = Field(gt=0)
    duration_minutes: int = Field(gt=0)
    session_count: int = Field(ge=1)
    features: list[str]
    is_active: bool = True
    display_order: int = 0


class StrategyServiceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    price_ngn: int | None = Field(default=None, gt=0)
    duration_minutes: int | None = Field(default=None, gt=0)
    session_count: int | None = Field(default=None, ge=1)
    features: list[str] | None = None
    is_active: bool | None = None
    display_order: int | None = None


class StrategyServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    price_ngn: int
    duration_minutes: int
    session_count: int
    features: list[str]
    is_active: bool
    display_order: int


class StrategySettingUpsert(BaseModel):
    value: dict
    is_public: bool = False


class StrategySettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: dict
    is_public: bool


class StrategyContentCreate(BaseModel):
    section_key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    eyebrow: str | None = Field(default=None, max_length=150)
    body: str = Field(min_length=1, max_length=5000)
    is_active: bool = True
    display_order: int = 0


class StrategyContentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    eyebrow: str | None = Field(default=None, max_length=150)
    body: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = None
    display_order: int | None = None


class StrategyContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_key: str
    title: str
    eyebrow: str | None
    body: str
    is_active: bool
    display_order: int


class StrategyPublicContentResponse(BaseModel):
    services: list[StrategyServiceResponse]
    sections: list[StrategyContentResponse]
    settings: dict[str, dict]
