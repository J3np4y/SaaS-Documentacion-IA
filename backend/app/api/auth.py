"""Registration, login, session inspection, and logout endpoints."""

import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import (
    SESSION_COOKIE_NAME,
    Principal,
    get_current_principal,
    require_frontend_origin,
)
from app.core.database import get_db
from app.core.security import hash_password, hash_secret, new_secret, verify_password
from app.core.settings import SESSION_COOKIE_SECURE
from app.models import AuthSession, Invitation, Membership, Organization, User
from app.schemas.auth import AuthUserRead, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["authentication"])
SESSION_LIFETIME = timedelta(days=7)
INVITATION_LIFETIME = timedelta(hours=24)


def _slug_for(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:50].strip("-")
    return f"{base or 'organizacion'}-{uuid4().hex[:8]}"


def _set_session_cookie(response: Response, token: str) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _session_for(user_id, token: str) -> AuthSession:
    return AuthSession(
        user_id=user_id,
        token_hash=hash_secret(token),
        expires_at=datetime.now(UTC) + SESSION_LIFETIME,
    )


def _auth_user(principal: Principal) -> AuthUserRead:
    return AuthUserRead(
        id=principal.user.id,
        email=principal.user.email,
        full_name=principal.user.full_name,
        organization_id=principal.organization.id,
        organization_name=principal.organization.name,
        role=principal.membership.role,
    )


@router.post(
    "/register",
    response_model=AuthUserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_frontend_origin)],
)
def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthUserRead:
    normalized_email = str(body.email).strip().lower()
    user = User(
        email=normalized_email,
        full_name=body.full_name.strip(),
        password_hash=hash_password(body.password),
    )
    token = new_secret()
    now = datetime.now(UTC)

    try:
        db.add(user)
        db.flush()

        if body.invitation_code:
            invitation = db.scalar(
                select(Invitation)
                .where(Invitation.token_hash == hash_secret(body.invitation_code))
                .with_for_update()
            )
            if (
                invitation is None
                or invitation.used_at is not None
                or invitation.expires_at <= now
            ):
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La invitación no es válida o ha caducado",
                )
            organization = db.get(Organization, invitation.organization_id)
            if organization is None:
                db.rollback()
                raise HTTPException(status_code=400, detail="La invitación no es válida o ha caducado")
            invitation.used_at = now
            membership = Membership(
                user_id=user.id, organization_id=organization.id, role="member"
            )
        else:
            if body.organization_name is None:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Indica el nombre de la organización",
                )
            organization = Organization(
                name=body.organization_name,
                slug=_slug_for(body.organization_name),
            )
            db.add(organization)
            db.flush()
            membership = Membership(
                user_id=user.id, organization_id=organization.id, role="owner"
            )

        db.add(membership)
        db.add(_session_for(user.id, token))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo completar el registro",
        ) from exc

    _set_session_cookie(response, token)
    return AuthUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization_id=organization.id,
        organization_name=organization.name,
        role=membership.role,
    )


@router.post(
    "/login",
    response_model=AuthUserRead,
    dependencies=[Depends(require_frontend_origin)],
)
def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthUserRead:
    user = db.scalar(select(User).where(User.email == str(body.email).strip().lower()))
    if not verify_password(body.password, user.password_hash if user else None) or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    organization = db.get(Organization, membership.organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    token = new_secret()
    db.add(_session_for(user.id, token))
    db.commit()
    _set_session_cookie(response, token)
    return AuthUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization_id=organization.id,
        organization_name=organization.name,
        role=membership.role,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_frontend_origin)])
def logout(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    response.headers["Cache-Control"] = "no-store"
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_token:
        auth_session = db.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_secret(raw_token))
        )
        if auth_session and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(UTC)
            db.commit()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AuthUserRead)
def current_user(
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> AuthUserRead:
    response.headers["Cache-Control"] = "no-store"
    return _auth_user(principal)
