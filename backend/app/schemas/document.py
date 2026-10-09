"""Request and response schemas for document management."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    extraction_status: Literal["pending", "ready", "failed"]
    rag_status: Literal["pending", "ready", "failed"]


class DocumentSearchResult(BaseModel):
    id: UUID
    filename: str
    snippet: str


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, question: str) -> str:
        if not question.strip():
            raise ValueError("Escribe una pregunta.")
        return question.strip()


class AnswerCitation(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    excerpt: str


class AnswerRead(BaseModel):
    answer: str
    abstained: bool
    citations: list[AnswerCitation]
