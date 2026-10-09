"""Document upload and tenant authorization checks against isolated PostgreSQL."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.core import settings
from app.core.database import SessionLocal, get_db
from app.main import app
from app.services import document_storage, rag, rag_usage

ORIGIN = {"origin": "http://localhost:3000"}
PASSWORD = "correct-horse-battery-staple"


@pytest.fixture()
def document_client(migrated_database, tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "DOCUMENT_STORAGE_DIR", tmp_path / "private-documents")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def override_get_db():
        with Session(migrated_database) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": email,
            "full_name": "Persona de prueba",
            "password": PASSWORD,
            "organization_name": "Organización de prueba",
        },
    )
    assert response.status_code == 201
    return response.json()


def docx_content(text: str = "Documento de aprendizaje") -> bytes:
    result = BytesIO()
    with ZipFile(result, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>",
        )
    return result.getvalue()


def test_upload_list_download_and_permanently_delete_document(document_client) -> None:
    register(document_client, "owner@example.com")
    content = b"Documento de aprendizaje\n"
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("../manual.txt", content, "application/octet-stream")},
    )

    assert uploaded.status_code == 201
    document = uploaded.json()
    assert document["filename"] == "manual.txt"
    assert document["content_type"] == "text/plain"
    assert document["size_bytes"] == len(content)
    assert document["extraction_status"] == "ready"
    assert uploaded.headers["cache-control"] == "no-store"
    assert len(list((document_storage.DOCUMENT_STORAGE_DIR).iterdir())) == 1

    listing = document_client.get("/organizations/me/documents")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [document["id"]]
    assert listing.headers["cache-control"] == "no-store"

    download = document_client.get(
        f"/organizations/me/documents/{document['id']}/download"
    )
    assert download.content == content
    assert download.headers["content-type"] == "text/plain; charset=utf-8"
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in download.headers["content-security-policy"]

    deleted = document_client.delete(
        f"/organizations/me/documents/{document['id']}", headers=ORIGIN
    )
    assert deleted.status_code == 204
    assert document_client.get("/organizations/me/documents").json() == []
    assert list(document_storage.DOCUMENT_STORAGE_DIR.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "content", "extraction_status"),
    [
        ("manual.pdf", "%PDF-1.7\ncontenido dañado".encode(), "failed"),
        ("manual.docx", docx_content(), "ready"),
        ("manual.txt", "Texto UTF-8: ñ".encode(), "ready"),
    ],
)
def test_upload_accepts_the_agreed_file_types(
    document_client, filename, content, extraction_status
) -> None:
    register(document_client, f"{filename.replace('.', '-')}@example.com")
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == filename
    assert response.json()["extraction_status"] == extraction_status


def test_search_returns_only_documents_from_the_current_organization(document_client) -> None:
    register(document_client, "owner@example.com")
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={
            "file": (
                "contrato.txt",
                b"Los contratos de vivienda requieren una firma.",
                "text/plain",
            )
        },
    )
    assert uploaded.status_code == 201

    other_client = TestClient(app)
    register(other_client, "other@example.com")

    response = document_client.get(
        "/organizations/me/documents/search", params={"q": "contrato"}
    )
    other_response = other_client.get(
        "/organizations/me/documents/search", params={"q": "contrato"}
    )

    assert response.status_code == 200
    assert [result["filename"] for result in response.json()] == ["contrato.txt"]
    assert response.json()[0]["id"] == uploaded.json()["id"]
    assert "contrat" in response.json()[0]["snippet"].lower()
    assert response.headers["cache-control"] == "no-store"
    assert other_response.json() == []


def test_search_requires_a_nonblank_query(document_client) -> None:
    register(document_client, "owner@example.com")
    response = document_client.get(
        "/organizations/me/documents/search", params={"q": "   "}
    )
    assert response.status_code == 400


def test_failed_extraction_keeps_the_original_available_and_can_be_retried(document_client) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("broken.pdf", b"%PDF-1.7\ninvalid", "application/pdf")},
    )
    document = upload.json()
    assert document["extraction_status"] == "failed"

    retry = document_client.post(
        f"/organizations/me/documents/{document['id']}/extract", headers=ORIGIN
    )
    download = document_client.get(
        f"/organizations/me/documents/{document['id']}/download"
    )

    assert retry.status_code == 200
    assert retry.json()["extraction_status"] == "failed"
    assert download.status_code == 200
    assert download.content == b"%PDF-1.7\ninvalid"


def test_existing_document_is_only_indexed_after_explicit_action(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"Los contratos requieren firma.", "text/plain")},
    )
    document = upload.json()
    assert document["rag_status"] == "pending"

    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(texts):
        assert texts == ["Los contratos requieren firma."]
        return [[1.0] + [0.0] * 1535]

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    response = document_client.post(
        f"/organizations/me/documents/{document['id']}/index", headers=ORIGIN
    )

    assert response.status_code == 200
    assert response.json()["rag_status"] == "ready"


def test_configured_new_upload_is_indexed_and_provider_failure_keeps_original(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(texts):
        assert texts == ["Texto nuevo para preguntas."]
        return [[1.0] + [0.0] * 1535]

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("new.txt", b"Texto nuevo para preguntas.", "text/plain")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["rag_status"] == "ready"

    async def provider_failure(_texts):
        raise rag.RagProviderError("private provider detail")

    monkeypatch.setattr(rag, "create_embeddings", provider_failure)
    failed = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("offline.txt", b"Texto guardado aunque falle OpenAI.", "text/plain")},
    )
    assert failed.status_code == 201
    assert failed.json()["rag_status"] == "failed"
    assert document_client.get(
        f"/organizations/me/documents/{failed.json()['id']}/download"
    ).content == b"Texto guardado aunque falle OpenAI."


def test_question_retrieves_only_current_organizations_sources(document_client, monkeypatch) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("contrato.txt", b"El contrato vence en diciembre.", "text/plain")},
    )
    document_id = upload.json()["id"]
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(_texts):
        return [[1.0] + [0.0] * 1535]

    async def generate(_question, sources):
        assert sources == [
            {"filename": "contrato.txt", "content": "El contrato vence en diciembre."}
        ]
        return {"answer": "Vence en diciembre.", "citation_numbers": [1]}

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    monkeypatch.setattr(rag, "generate_answer", generate)
    # Seed the vector through the authorized indexing endpoint.
    indexed = document_client.post(
        f"/organizations/me/documents/{document_id}/index", headers=ORIGIN
    )
    assert indexed.status_code == 200
    answer = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "¿Cuándo vence el contrato?"},
    )

    other_client = TestClient(app)
    register(other_client, "other@example.com")
    other_answer = other_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "¿Cuándo vence el contrato?"},
    )

    assert answer.status_code == 200
    assert answer.json()["answer"] == "Vence en diciembre."
    assert answer.json()["citations"] == [
        {
            "document_id": document_id,
            "filename": "contrato.txt",
            "chunk_index": 0,
            "excerpt": "El contrato vence en diciembre.",
        }
    ]
    assert other_answer.status_code == 200
    assert other_answer.json()["abstained"] is True
    assert other_answer.json()["citations"] == []


def test_question_abstains_without_evidence_and_rejects_long_input(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(_texts):
        return [[1.0] + [0.0] * 1535]

    async def unexpected_generation(*_args):
        pytest.fail("Generation must not run without retrieved evidence")

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    monkeypatch.setattr(rag, "generate_answer", unexpected_generation)
    no_evidence = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "Pregunta sin documentos"},
    )
    too_long = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "x" * 1001},
    )

    assert no_evidence.status_code == 200
    assert no_evidence.json()["abstained"] is True
    assert "No encuentro evidencia" in no_evidence.json()["answer"]
    assert too_long.status_code == 422


def test_invalid_model_citation_is_replaced_with_abstention(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"El importe es 25 euros.", "text/plain")},
    )
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(_texts):
        return [[1.0] + [0.0] * 1535]

    async def invalid_citation(_question, _sources):
        return {"answer": "La cantidad es 25.", "citation_numbers": [2]}

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    monkeypatch.setattr(rag, "generate_answer", invalid_citation)
    indexed = document_client.post(
        f"/organizations/me/documents/{upload.json()['id']}/index", headers=ORIGIN
    )
    assert indexed.status_code == 200

    answer = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "¿Cuál es el importe?"},
    )
    assert answer.status_code == 200
    assert answer.json()["abstained"] is True
    assert answer.json()["citations"] == []


def test_upload_accepts_a_file_at_the_exact_size_limit(document_client) -> None:
    register(document_client, "limit@example.com")
    content = b"x" * (10 * 1024 * 1024)
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("limit.txt", content, "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["size_bytes"] == 10 * 1024 * 1024


@pytest.mark.parametrize(
    ("filename", "content_size", "content", "expected_status"),
    [
        ("empty.txt", 0, b"", 400),
        ("fake.txt", 8, b"%PDF-1.7", 400),
        ("fake-archive.txt", 24, b"PK\x03\x04" + b"\x00" * 20, 400),
        ("unknown.exe", 8, b"anything", 400),
        ("large.txt", 10 * 1024 * 1024 + 1, None, 413),
    ],
)
def test_upload_rejects_invalid_or_oversized_files(
    document_client, filename, content_size, content, expected_status
) -> None:
    register(document_client, f"{filename.replace('.', '-')}@example.com")
    if content is None:
        content = b"a" * content_size
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == expected_status
    assert document_client.get("/organizations/me/documents").json() == []
    assert not document_storage.DOCUMENT_STORAGE_DIR.exists()


def test_rag_evaluation_dataset_measures_retrieval_citations_and_abstention(
    document_client, monkeypatch
) -> None:
    dataset_path = Path(__file__).parent / "fixtures" / "rag_evaluation.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    register(document_client, "evaluation@example.com")
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    vectors = {}

    async def embeddings(texts):
        return [vectors[text] for text in texts]

    monkeypatch.setattr(rag, "create_embeddings", embeddings)

    for index, document in enumerate(dataset["documents"]):
        vector = [0.0] * 1536
        vector[index] = 1.0
        vectors[document["text"]] = vector
        upload = document_client.post(
            "/organizations/me/documents",
            headers=ORIGIN,
            files={
                "file": (
                    document["filename"],
                    document["text"].encode(),
                    "text/plain",
                )
            },
        )
        assert upload.status_code == 201
        assert upload.json()["rag_status"] == "ready"

    for index, case in enumerate(
        case for case in dataset["cases"] if case["expected_source"] is not None
    ):
        vector = [0.0] * 1536
        vector[index] = 1.0
        vectors[case["question"]] = vector
    unrelated_vector = [0.0] * 1536
    unrelated_vector[len(dataset["documents"])] = 1.0
    vectors[
        next(case["question"] for case in dataset["cases"] if case["expected_source"] is None)
    ] = unrelated_vector

    async def answer(question, sources):
        case = next(item for item in dataset["cases"] if item["question"] == question)
        assert [
            (source["filename"], source["content"]) for source in sources
        ] == [(case["expected_source"], case["expected_excerpt"])]
        return {"answer": case["expected_answer"], "citation_numbers": [1]}

    monkeypatch.setattr(rag, "generate_answer", answer)

    measured = {"retrieval": 0, "citations": 0, "abstentions": 0}
    for case in dataset["cases"]:
        response = document_client.post(
            "/organizations/me/documents/ask",
            headers=ORIGIN,
            json={"question": case["question"]},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["answer"] == case["expected_answer"]
        assert result["abstained"] is case["expected_abstained"]

        if case["expected_abstained"]:
            assert result["citations"] == []
            measured["abstentions"] += 1
        else:
            citation = result["citations"][0]
            assert citation["filename"] == case["expected_source"]
            assert citation["excerpt"] == case["expected_excerpt"]
            measured["retrieval"] += 1
            measured["citations"] += 1

    assert measured == {"retrieval": 2, "citations": 2, "abstentions": 1}


def test_rag_quota_blocks_provider_calls_and_preserves_uploads(
    document_client, monkeypatch
) -> None:
    owner = register(document_client, "quota@example.com")
    monkeypatch.setattr(settings, "RAG_DAILY_OPERATION_LIMIT", 1)
    monkeypatch.setattr(rag, "is_configured", lambda: True)
    embedding_calls = []

    async def embeddings(texts):
        embedding_calls.extend(texts)
        return [[1.0] + [0.0] * 1535 for _ in texts]

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    first = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("first.txt", b"Primer documento indexable.", "text/plain")},
    )
    second = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("second.txt", b"Segundo documento preservado.", "text/plain")},
    )
    question = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "¿Qué documentos hay?"},
    )

    assert first.status_code == 201
    assert first.json()["rag_status"] == "ready"
    assert second.status_code == 201
    assert second.json()["rag_status"] == "pending"
    assert question.status_code == 429
    assert len(embedding_calls) == 1
    downloaded = document_client.get(
        f"/organizations/me/documents/{second.json()['id']}/download"
    )
    assert downloaded.content == b"Segundo documento preservado."

    with SessionLocal() as db:
        rows = db.scalars(
            select(models.RagUsagePeriod).where(
                models.RagUsagePeriod.organization_id == owner["organization_id"],
                models.RagUsagePeriod.period_type == "day",
            )
        ).all()
    assert len(rows) == 1
    assert rows[0].operation_count == 1


def test_failed_provider_attempt_consumes_quota(document_client, monkeypatch) -> None:
    register(document_client, "failed-quota@example.com")
    monkeypatch.setattr(settings, "RAG_DAILY_OPERATION_LIMIT", 1)
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def provider_failure(_texts):
        raise rag.RagProviderError("provider detail must not be returned")

    monkeypatch.setattr(rag, "create_embeddings", provider_failure)
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("failure.txt", b"El proveedor puede fallar.", "text/plain")},
    )
    rejected = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "¿Qué ocurrió?"},
    )

    assert uploaded.status_code == 201
    assert uploaded.json()["rag_status"] == "failed"
    assert rejected.status_code == 429
    assert "provider detail" not in rejected.text


def test_quota_store_failure_fails_closed_but_keeps_new_upload(
    document_client, monkeypatch
) -> None:
    from app.api import documents

    register(document_client, "quota-store-failure@example.com")
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    def quota_unavailable(_organization_id: int) -> None:
        raise rag_usage.RagQuotaUnavailable()

    monkeypatch.setattr(
        documents, "reserve_rag_operation", quota_unavailable
    )
    monkeypatch.setattr(
        rag,
        "create_embeddings",
        lambda _texts: pytest.fail("OpenAI must not be called without quota approval"),
    )
    content = b"Keep this source document."

    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("kept.txt", content, "text/plain")},
    )
    question = document_client.post(
        "/organizations/me/documents/ask",
        headers=ORIGIN,
        json={"question": "What does it say?"},
    )
    download = document_client.get(
        f"/organizations/me/documents/{uploaded.json()['id']}/download"
    )

    assert uploaded.status_code == 201
    assert uploaded.json()["rag_status"] == "pending"
    assert question.status_code == 503
    assert "límite de uso" in question.json()["detail"]
    assert download.content == content


def test_rag_quota_isolated_by_organization(document_client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "RAG_DAILY_OPERATION_LIMIT", 1)
    monkeypatch.setattr(rag, "is_configured", lambda: True)

    async def embeddings(texts):
        return [[1.0] + [0.0] * 1535 for _ in texts]

    monkeypatch.setattr(rag, "create_embeddings", embeddings)
    register(document_client, "first-tenant@example.com")
    first = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={
            "file": (
                "first.txt",
                b"Documento de la primera organizacion.",
                "text/plain",
            )
        },
    )

    other_client = TestClient(app)
    register(other_client, "second-tenant@example.com")
    second = other_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={
            "file": ("second.txt", b"Documento de otra organizacion.", "text/plain")
        },
    )

    assert first.json()["rag_status"] == "ready"
    assert second.json()["rag_status"] == "ready"


def test_rag_quota_resets_at_utc_day_and_month_boundaries(
    document_client, monkeypatch
) -> None:
    owner = register(document_client, "utc-quota@example.com")
    monkeypatch.setattr(settings, "RAG_DAILY_OPERATION_LIMIT", 1)
    monkeypatch.setattr(settings, "RAG_MONTHLY_OPERATION_LIMIT", 2)
    organization_id = owner["organization_id"]
    last_january_day = datetime(2026, 1, 31, 23, 59, tzinfo=UTC)
    first_february_day = datetime(2026, 2, 1, 0, 1, tzinfo=UTC)
    next_february_day = datetime(2026, 2, 2, 0, 1, tzinfo=UTC)
    third_february_day = datetime(2026, 2, 3, 0, 1, tzinfo=UTC)

    rag_usage.reserve_rag_operation(organization_id, last_january_day)
    with pytest.raises(rag_usage.RagQuotaExceeded):
        rag_usage.reserve_rag_operation(organization_id, last_january_day)
    rag_usage.reserve_rag_operation(organization_id, first_february_day)
    rag_usage.reserve_rag_operation(organization_id, next_february_day)
    with pytest.raises(rag_usage.RagQuotaExceeded):
        rag_usage.reserve_rag_operation(organization_id, third_february_day)


def test_rag_quota_reservations_are_atomic_under_concurrent_requests(
    document_client, monkeypatch
) -> None:
    owner = register(document_client, "concurrent-quota@example.com")
    monkeypatch.setattr(settings, "RAG_DAILY_OPERATION_LIMIT", 3)
    monkeypatch.setattr(settings, "RAG_MONTHLY_OPERATION_LIMIT", 30)
    organization_id = owner["organization_id"]
    instant = datetime(2026, 5, 4, 12, 0, tzinfo=UTC)

    def attempt_reservation() -> bool:
        try:
            rag_usage.reserve_rag_operation(organization_id, instant)
            return True
        except rag_usage.RagQuotaExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: attempt_reservation(), range(12)))

    assert sum(results) == 3


def test_metrics_and_request_logs_exclude_query_values_and_identity(
    document_client, caplog
) -> None:
    caplog.set_level("INFO", logger="app.request")
    response = document_client.get("/health?email=private@example.com&secret=not-a-secret")
    metric_response = document_client.get("/metrics")

    assert response.status_code == 200
    assert metric_response.status_code == 200
    assert 'route="/health"' in metric_response.text
    assert "private@example.com" not in metric_response.text
    assert "not-a-secret" not in metric_response.text
    assert all(
        "private@example.com" not in record.message
        and "not-a-secret" not in record.message
        for record in caplog.records
        if record.name == "app.request"
    )


def test_explicit_index_rejects_documents_over_the_fragment_work_limit(
    document_client, monkeypatch
) -> None:
    from app.api import documents

    register(document_client, "large-index@example.com")
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("long.txt", b"x" * 2000, "text/plain")},
    )
    monkeypatch.setattr(documents, "RAG_MAX_INDEX_CHUNKS", 1)
    monkeypatch.setattr(rag, "is_configured", lambda: True)
    monkeypatch.setattr(
        rag,
        "create_embeddings",
        lambda _texts: pytest.fail("No embeddings should be sent for oversized work"),
    )

    indexed = document_client.post(
        f"/organizations/me/documents/{uploaded.json()['id']}/index", headers=ORIGIN
    )
    listed = document_client.get("/organizations/me/documents")

    assert indexed.status_code == 413
    assert listed.json()[0]["rag_status"] == "failed"


def test_documents_are_scoped_to_membership_and_organization(document_client) -> None:
    owner = register(document_client, "owner@example.com")
    invitation = document_client.post("/organizations/me/invitations", headers=ORIGIN)
    member_client = TestClient(app)
    member = member_client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": "member@example.com",
            "full_name": "Integrante",
            "password": PASSWORD,
            "invitation_code": invitation.json()["code"],
        },
    )
    assert member.status_code == 201
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("shared.txt", b"visible in the organization", "text/plain")},
    )
    document_id = upload.json()["id"]

    other_client = TestClient(app)
    other = register(other_client, "other@example.com")

    assert member_client.get("/organizations/me/documents").json()[0]["id"] == document_id
    assert member_client.get(
        f"/organizations/me/documents/{document_id}/download"
    ).content == b"visible in the organization"
    assert member_client.delete(
        f"/organizations/me/documents/{document_id}", headers=ORIGIN
    ).status_code == 204
    assert document_client.get("/organizations/me/documents").json() == []
    assert other["organization_id"] != owner["organization_id"]
    assert other_client.get("/organizations/me/documents").json() == []
    assert other_client.get(
        f"/organizations/me/documents/{document_id}/download"
    ).status_code == 404
    assert other_client.delete(
        f"/organizations/me/documents/{document_id}", headers=ORIGIN
    ).status_code == 404


def test_document_writes_require_authentication_and_same_origin(document_client) -> None:
    unauthenticated = document_client.get("/organizations/me/documents")
    assert unauthenticated.status_code == 401

    register(document_client, "owner@example.com")
    no_origin = document_client.post(
        "/organizations/me/documents",
        files={"file": ("manual.txt", b"content", "text/plain")},
    )
    assert no_origin.status_code == 403
    assert document_client.get("/organizations/me/documents").json() == []


def test_upload_cleans_private_file_when_database_commit_fails(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")

    def fail_commit(_session):
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"content", "text/plain")},
    )

    assert response.status_code == 500
    assert document_client.get("/organizations/me/documents").json() == []
    assert list(document_storage.DOCUMENT_STORAGE_DIR.iterdir()) == []


def test_delete_restores_file_when_database_commit_fails(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"content", "text/plain")},
    )
    document = upload.json()

    def fail_commit(_session):
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = document_client.delete(
        f"/organizations/me/documents/{document['id']}", headers=ORIGIN
    )

    assert response.status_code == 500
    assert document_client.get("/organizations/me/documents").json()[0]["id"] == document["id"]
    assert len(list(document_storage.DOCUMENT_STORAGE_DIR.iterdir())) == 1


def test_upload_rejects_excessive_multipart_overhead_before_parsing(document_client) -> None:
    register(document_client, "owner@example.com")
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"x" * (10 * 1024 * 1024), "text/plain")},
        data={"extra": "x" * (64 * 1024 + 1)},
    )

    assert response.status_code == 413
    assert document_client.get("/organizations/me/documents").json() == []
