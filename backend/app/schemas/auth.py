"""Request and response schemas for authentication and organization access."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str | None = Field(default=None, min_length=1, max_length=120)
    invitation_code: str | None = Field(default=None, min_length=20, max_length=128)

    @field_validator("full_name", "organization_name")
    @classmethod
    def strip_name_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("El valor no puede estar vacío")
        return value

    @model_validator(mode="after")
    def require_organization_or_invitation(self) -> "RegisterRequest":
        if (self.organization_name is None) == (self.invitation_code is None):
            raise ValueError("Indica el nombre de la organización o un código de invitación")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthUserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    organization_id: UUID
    organization_name: str
    role: Literal["owner", "member"]


class MemberRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["owner", "member"]


class InvitationRead(BaseModel):
    code: str
    expires_at: datetime


class RoleUpdate(BaseModel):
    role: Literal["owner", "member"]
