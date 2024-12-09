import json
from datetime import datetime, timezone
from functools import partial

from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, field_validator
from sqlmodel import Field, LargeBinary, SQLModel
from sqlalchemy import text
from sqlalchemy.engine import Engine
import numpy as np


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
    
    # SQLite can't store lists so transform it to a string
    @field_validator("emails", mode="before")
    def list_to_str(cls, emails_list: list[str]) -> str:
        return ",".join(emails_list)
    
    openai_model_name: str
    prompt_version: str | None = Field(default="v1")
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))


# this will be for the second extraction pass
class ChildcareOpenAIResponse(BaseModel):
    webpage_year: str | None

    provides_before_care: bool | None
    before_care_start_time: str | None
    before_care_provider: str | None
    before_care_quote_snippet: str | None = Field(description="The EXACT quoted text from the webpage that contains the reason for your answer.")

    provides_after_care: bool | None
    after_care_end_time: str | None
    after_care_provider: str | None
    after_care_quote_snippet: str | None = Field(description="The EXACT quoted text from the webpage that contains the reason for your answer.")


# add a few extra fields for the database record
class ChildcareOpenAIRecord(SQLModel, ChildcareOpenAIResponse, table=True):
    id: int | None = Field(default=None, primary_key=True)
    school_id: int
    page_url: str
    before_care_quote_snippet_verified: bool | None
    after_care_quote_snippet_verified: bool | None

    openai_model_name: str
    prompt_version: str | None = Field(default="v1")
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))


class CitationSnippet(BaseModel):
    url: str | None
    snippet: str | None


# this will be for the final aggregation pass
class CombinedChildcareOpenAIResponse(BaseModel):
    provides_before_care: bool | None
    before_care_start_time: str | None
    before_care_provider: str | None
    before_care_citations: list[int] | None
    before_care_citation_snippets: list[CitationSnippet] | None

    provides_after_care: bool | None
    after_care_end_time: str | None
    after_care_provider: str | None
    after_care_citations: list[int] | None
    after_care_citation_snippets: list[CitationSnippet] | None


# add a few extra fields for the database record
class CombinedChildcareOpenAIRecord(SQLModel, CombinedChildcareOpenAIResponse, table=True):
    id: int | None = Field(default=None, primary_key=True)
    school_id: int
    before_care_citations: str | None
    before_care_citation_snippets: str | None
    after_care_citations: str | None
    after_care_citation_snippets: str | None

    openai_model_name: str
    prompt_version: str | None = Field(default="v1")
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))

    # SQLite can't store lists so transform to json
    @field_validator("before_care_citations", "after_care_citations",
                     "before_care_citation_snippets", "after_care_citation_snippets",mode="before")
    def list_to_json(cls, list_obj: list | None) -> str | None:
        return json.dumps(list_obj) if list_obj is not None else None


class SchoolToNeighborhood(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    school_id: int
    school_name: str
    neighborhood: str


class Neighborhood(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    neighborhood: str
    student_count: int | None
    low_income_student_count: int | None
    low_income_student_pct: float | None
    black_student_count: int | None
    black_student_pct: float | None
    hispanic_student_count: int | None
    hispanic_student_pct: float | None
    white_student_count: int | None
    white_student_pct: float | None


class WebPageChunk(LanceModel):
    id: str
    school_id: int
    page_url: str
    chunk_text: str
    chunk_embedding: Vector(768)

# alembic revision --autogenerate -m "init"
# alembic upgrade head
