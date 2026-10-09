"""Organization-scoped document upload, listing, download, and deletion."""

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import Principal, get_current_principal, require_frontend_origin
from app.core.database import get_db
from app.core.settings import RAG_MAX_CONTEXT_CHUNKS, RAG_MAX_QUERY_CHARS, RAG_MIN_SIMILARITY
from app.models import Document, DocumentChunk
from app.schemas.document import (
    AnswerCitation,
    AnswerRead,
    AnswerRequest,
    DocumentRead,
    DocumentSearchResult,
)
from app.services import rag
from app.services.document_processing import DocumentExtractionError, extract_document_text
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
        extraction_status=document.extraction_status,
        rag_status=document.rag_status,
    )


async def _index_text(db: Session, document: Document) -> None:
    chunks = rag.split_into_chunks(document.extracted_text or "")
    if not chunks:
        document.rag_status = "failed"
        return
    embeddings = await rag.create_embeddings(chunks)
    db.execute(
        DocumentChunk.__table__.delete().where(DocumentChunk.document_id == document.id)
    )
    db.add_all(
        DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True))
    )
    document.rag_status = "ready"


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

    try:
        extracted_text = extract_document_text(content_type, content)
        extraction_status = "ready"
        rag_status = "pending"
    except DocumentExtractionError:
        extracted_text = None
        extraction_status = "failed"
        rag_status = "failed"

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
        extracted_text=extracted_text,
        extraction_status=extraction_status,
        rag_status=rag_status,
    )
    db.add(document)
    try:
        db.flush()
        if extraction_status == "ready" and rag.is_configured():
            try:
                await _index_text(db, document)
                db.flush()
            except rag.RagProviderError:
                document.rag_status = "failed"
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


@router.get("/search", response_model=list[DocumentSearchResult])
def search_documents(
    query: Annotated[str, Query(min_length=1, max_length=200, alias="q")],
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentSearchResult]:
    if not query.strip():
        raise HTTPException(status_code=400, detail="Escribe un término para buscar")

    tsquery = func.plainto_tsquery("spanish", query.strip())
    rows = db.execute(
        select(
            Document.id,
            Document.filename,
            func.ts_headline("spanish", Document.extracted_text, tsquery).label("snippet"),
        )
        .where(
            Document.organization_id == principal.organization.id,
            Document.extraction_status == "ready",
            Document.search_vector.op("@@")(tsquery),
        )
        .order_by(
            func.ts_rank(Document.search_vector, tsquery).desc(),
            Document.filename,
            Document.id,
        )
        .limit(20)
    ).all()
    response.headers["Cache-Control"] = "no-store"
    return [
        DocumentSearchResult(id=row.id, filename=row.filename, snippet=row.snippet)
        for row in rows
    ]


@router.post(
    "/{document_id}/index",
    response_model=DocumentRead,
    dependencies=[Depends(require_frontend_origin)],
)
async def index_document(
    document_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    document = _find_document(db, document_id, principal.organization.id)
    if document.extraction_status != "ready" or not document.extracted_text:
        raise HTTPException(status_code=409, detail="El documento no tiene texto que se pueda indexar.")
    if not rag.is_configured():
        raise HTTPException(status_code=503, detail="El servicio de OpenAI no está configurado.")

    try:
        await _index_text(db, document)
        db.commit()
        db.refresh(document)
    except rag.RagProviderError:
        db.rollback()
        document = _find_document(db, document_id, principal.organization.id)
        db.execute(
            DocumentChunk.__table__.delete().where(DocumentChunk.document_id == document.id)
        )
        document.rag_status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail="No se pudo preparar el documento para preguntas.") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo indexar el documento.") from None

    response.headers["Cache-Control"] = "no-store"
    return _read_model(document)


@router.post(
    "/ask",
    response_model=AnswerRead,
    dependencies=[Depends(require_frontend_origin)],
)
async def ask_documents(
    request: AnswerRequest,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> AnswerRead:
    if len(request.question) > RAG_MAX_QUERY_CHARS:
        raise HTTPException(status_code=422, detail="La pregunta supera el límite permitido.")
    if not rag.is_configured():
        raise HTTPException(status_code=503, detail="El servicio de OpenAI no está configurado.")

    try:
        query_embedding = (await rag.create_embeddings([request.question]))[0]
    except rag.RagProviderError:
        raise HTTPException(status_code=503, detail="No se pudo buscar evidencia.") from None

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    rows = db.execute(
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            Document.filename,
            distance.label("distance"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.organization_id == principal.organization.id,
            Document.rag_status == "ready",
            distance <= 1 - RAG_MIN_SIMILARITY,
        )
        .order_by(distance, DocumentChunk.id)
        .limit(RAG_MAX_CONTEXT_CHUNKS)
    ).all()
    if not rows:
        response.headers["Cache-Control"] = "no-store"
        return AnswerRead(
            answer="No encuentro evidencia suficiente en los documentos de tu organización.",
            abstained=True,
            citations=[],
        )

    sources = [
        {"filename": row.filename, "content": row.content}
        for row in rows
    ]
    try:
        draft = await rag.generate_answer(request.question, sources)
    except rag.RagProviderError:
        raise HTTPException(status_code=503, detail="No se pudo generar una respuesta.") from None

    citation_numbers = draft["citation_numbers"]
    if any(number < 1 or number > len(rows) for number in citation_numbers):
        citation_numbers = []
    citations = [
        AnswerCitation(
            document_id=rows[number - 1].document_id,
            filename=rows[number - 1].filename,
            chunk_index=rows[number - 1].chunk_index,
            excerpt=rows[number - 1].content,
        )
        for number in citation_numbers
    ]
    abstained = not citations
    response.headers["Cache-Control"] = "no-store"
    return AnswerRead(
        answer=(
            "No encuentro evidencia suficiente en los documentos de tu organización."
            if abstained
            else draft["answer"]
        ),
        abstained=abstained,
        citations=citations,
    )


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


@router.post(
    "/{document_id}/extract",
    response_model=DocumentRead,
    dependencies=[Depends(require_frontend_origin)],
)
async def reprocess_document(
    document_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRead:
    document = _find_document(db, document_id, principal.organization.id)
    try:
        content = read_object(document.storage_key)
    except OSError:
        logger.error("No se pudo leer el archivo original durante la extracción")
        raise HTTPException(status_code=500, detail="No se pudo procesar el documento") from None

    try:
        document.extracted_text = extract_document_text(document.content_type, content)
        document.extraction_status = "ready"
    except DocumentExtractionError:
        document.extracted_text = None
        document.extraction_status = "failed"
    document.rag_status = "failed"

    try:
        if document.extraction_status == "ready" and rag.is_configured():
            try:
                await _index_text(db, document)
            except rag.RagProviderError:
                document.rag_status = "failed"
        db.commit()
        db.refresh(document)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo procesar el documento") from None

    response.headers["Cache-Control"] = "no-store"
    return _read_model(document)


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
