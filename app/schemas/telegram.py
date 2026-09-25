from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class TelegramChat(BaseModel):
    id: int


class TelegramBusinessMessage(BaseModel):
    business_connection_id: str
    message_id: int
    from_: TelegramUser = Field(alias="from")
    chat: TelegramChat
    text: str | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    business_message: TelegramBusinessMessage | None = None