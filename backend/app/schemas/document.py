"""Request and response schemas for document management."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    extraction_status: Literal["pending", "ready", "failed"]


class DocumentSearchResult(BaseModel):
    id: UUID
    filename: str
    snippet: str
