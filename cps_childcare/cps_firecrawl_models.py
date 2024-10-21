from datetime import datetime, timezone
from functools import partial

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel


class CrawlerRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    index: int
    school_name: str
    school_id: int
    school_type: str
    page_title: str | None
    page_url: str
    description: str | None
    status_code: int
    markdown: str | None
    html: str | None
    crawled_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))


# this will be the model that we use for the gpt structured output response
class CrawlerOpenAIResponse(BaseModel):
    emails: list[str]
    is_contact_page: bool
    before_or_after_care_details: str


# add a few extra fields for the database record
class CrawlerOpenAIRecord(SQLModel, CrawlerOpenAIResponse, table=True):
    id: int | None = Field(default=None, primary_key=True)
    school_id: int
    school_type: str
    page_url: str
    emails: str
    
    @field_validator("emails",mode="before")
    def list_to_str(cls, emails_list: list[str]) -> str:
        return ",".join(emails_list)
    
    openai_model_name: str
    prompt_version: str | None = Field(default="v1")
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))


# alembic revision --autogenerate -m "init"
# alembic upgrade head
