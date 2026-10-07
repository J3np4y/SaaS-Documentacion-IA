"""Authentication dependencies for request-scoped principals."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_secret
from app.models import AuthSession, Membership, Organization, User

SESSION_COOKIE_NAME = "docs_assistant_session"


@dataclass(frozen=True)
class Principal:
    user: User
    organization: Organization
    membership: Membership
    session: AuthSession


def get_current_principal(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> Principal:
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida")

    statement = (
        select(AuthSession, User, Membership, Organization)
        .join(User, User.id == AuthSession.user_id)
        .join(Membership, Membership.user_id == User.id)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(
            AuthSession.token_hash == hash_secret(raw_token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida")
    auth_session, user, membership, organization = row
    return Principal(user, organization, membership, auth_session)


def require_owner(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
    if principal.membership.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente")
    return principal


def require_frontend_origin(request: Request) -> None:
    from app.core.settings import FRONTEND_ORIGIN

    if request.headers.get("origin") != FRONTEND_ORIGIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origen no permitido")
