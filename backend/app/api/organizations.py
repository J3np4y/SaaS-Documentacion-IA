"""Organization member and invitation management."""

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_frontend_origin, require_owner
from app.core.database import get_db
from app.core.security import hash_secret, new_secret
from app.models import AuthSession, Invitation, Membership, Organization, User
from app.schemas.auth import InvitationRead, MemberRead, RoleUpdate

router = APIRouter(prefix="/organizations/me", tags=["organizations"])
INVITATION_LIFETIME = timedelta(hours=24)


@router.get("/members", response_model=list[MemberRead])
def list_members(
    response: Response,
    principal: Annotated[Principal, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[MemberRead]:
    response.headers["Cache-Control"] = "no-store"
    rows = db.execute(
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == principal.organization.id)
        .order_by(User.email)
    ).all()
    return [
        MemberRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role,
        )
        for user, membership in rows
    ]


@router.post(
    "/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_frontend_origin)],
)
def create_invitation(
    response: Response,
    principal: Annotated[Principal, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationRead:
    raw_code = new_secret()
    expires_at = datetime.now(UTC) + INVITATION_LIFETIME
    db.add(
        Invitation(
            organization_id=principal.organization.id,
            created_by_user_id=principal.user.id,
            token_hash=hash_secret(raw_code),
            expires_at=expires_at,
        )
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return InvitationRead(code=raw_code, expires_at=expires_at)


@router.patch(
    "/members/{user_id}",
    response_model=MemberRead,
    dependencies=[Depends(require_frontend_origin)],
)
def update_member_role(
    user_id: UUID,
    body: RoleUpdate,
    response: Response,
    principal: Annotated[Principal, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> MemberRead:
    db.scalar(
        select(Organization)
        .where(Organization.id == principal.organization.id)
        .with_for_update()
    )
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == principal.organization.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if membership.role == "owner" and body.role == "member":
        owner_count = db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.organization_id == principal.organization.id,
                Membership.role == "owner",
            )
        )
        if owner_count <= 1:
            raise HTTPException(status_code=409, detail="La organización debe conservar un propietario")
    membership.role = body.role
    user = db.get(User, user_id)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return MemberRead(id=user.id, email=user.email, full_name=user.full_name, role=membership.role)


@router.delete(
    "/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_frontend_origin)],
)
def remove_member(
    user_id: UUID,
    principal: Annotated[Principal, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    db.scalar(
        select(Organization)
        .where(Organization.id == principal.organization.id)
        .with_for_update()
    )
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == principal.organization.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if membership.role == "owner":
        owner_count = db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.organization_id == principal.organization.id,
                Membership.role == "owner",
            )
        )
        if owner_count <= 1:
            raise HTTPException(status_code=409, detail="La organización debe conservar un propietario")

    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
