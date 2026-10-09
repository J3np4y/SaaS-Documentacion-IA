"""Organization-scoped document upload, listing, download, and deletion."""

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import Principal, get_current_principal, require_frontend_origin
from app.core.database import get_db
from app.models import Document
from app.schemas.document import DocumentRead
from app.services.document_storage import (
    MAX_DOCUMENT_SIZE_BYTES,
    InvalidDocument,
    delete_object,
    object_path,
    read_object,
    store_object,
    validate_document,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations/me/documents", tags=["documents"])


def _read_model(document: Document) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        created_at=document.created_at,
    )


def _find_document(db: Session, document_id: UUID, organization_id: UUID) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
            Document.storage_key.is_not(None),
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return document


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_frontend_origin)],
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    content = await file.read(MAX_DOCUMENT_SIZE_BYTES + 1)
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 10 MiB")
    try:
        filename, content_type = validate_document(file.filename, content)
    except InvalidDocument as error:
        raise HTTPException(status_code=400, detail=str(error)) from None

    storage_key = uuid4().hex
    try:
        store_object(storage_key, content)
    except OSError:
        logger.error("No se pudo guardar un documento en el almacenamiento local")
        raise HTTPException(status_code=500, detail="No se pudo guardar el documento") from None

    document = Document(
        organization_id=principal.organization.id,
        filename=filename,
        content_type=content_type,
        storage_key=storage_key,
        size_bytes=len(content),
    )
    db.add(document)
    try:
        db.flush()
        db.refresh(document)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        try:
            delete_object(storage_key)
        except OSError:
            logger.error("Falló la limpieza de un archivo tras un error de base de datos")
        raise HTTPException(status_code=500, detail="No se pudo guardar el documento") from None

    response.headers["Cache-Control"] = "no-store"
    return _read_model(document)


@router.get("", response_model=list[DocumentRead])
def list_documents(
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentRead]:
    documents = db.scalars(
        select(Document)
        .where(
            Document.organization_id == principal.organization.id,
            Document.storage_key.is_not(None),
        )
        .order_by(Document.created_at.desc(), Document.id)
    ).all()
    response.headers["Cache-Control"] = "no-store"
    return [_read_model(document) for document in documents]


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    document = _find_document(db, document_id, principal.organization.id)
    path = object_path(document.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.filename,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_frontend_origin)],
)
def delete_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    document = _find_document(db, document_id, principal.organization.id)
    storage_key = document.storage_key
    try:
        stored_content = read_object(storage_key)
        db.delete(document)
        db.flush()
        delete_object(storage_key)
    except OSError:
        db.rollback()
        logger.error("No se pudo acceder al archivo durante el borrado")
        raise HTTPException(status_code=500, detail="No se pudo borrar el documento") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo borrar el documento") from None

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        try:
            store_object(storage_key, stored_content)
        except OSError:
            logger.error("Falló la restauración del archivo tras un error de base de datos")
        raise HTTPException(status_code=500, detail="No se pudo borrar el documento") from None
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"Cache-Control": "no-store"},
    )
