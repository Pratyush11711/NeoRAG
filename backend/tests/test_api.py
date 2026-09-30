import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.bm25_service import bm25_service
from app.models.responses import DocumentChunkModel

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "gemini_chat_model" in data
    assert "gemini_embedding_model" in data

def test_documents_list_endpoint():
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

def test_upload_invalid_file_type():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.exe", b"binarycontent", "application/octet-stream")}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_FILE_TYPE"

def test_search_empty_query():
    response = client.post(
        "/api/retrieval/search",
        json={"query": "  ", "strategy": "similarity"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "EMPTY_QUERY"

def test_search_invalid_strategy():
    response = client.post(
        "/api/retrieval/search",
        json={"query": "transformer", "strategy": "non_existent_strategy"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_STRATEGY"

def test_search_bm25_endpoint():
    # Pre-index dummy chunk
    c = DocumentChunkModel(
        chunk_id="test_api_chunk_1",
        document_id="test_doc",
        page_content="The Transformer utilizes multi-head attention.",
        raw_text="The Transformer utilizes multi-head attention."
    )
    bm25_service.index_chunks([c])

    response = client.post(
        "/api/retrieval/search",
        json={"query": "attention", "strategy": "bm25", "k": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "bm25"
    assert "pipeline_trace" in data
    assert len(data["pipeline_trace"]) > 0
    assert len(data["documents"]) > 0
    assert data["documents"][0]["chunk_id"] == "test_api_chunk_1"

def test_chat_endpoint_execution():
    response = client.post(
        "/api/chat",
        json={
            "query": "What is the Transformer architecture?",
            "strategy": "bm25",
            "debug": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "pipeline_trace" in data
    assert "total_duration_ms" in data
    assert data["strategy"] == "bm25"

def test_reference_document_download_and_view():
    # Test reference inline view
    response_view = client.get("/api/documents/reference/attention-is-all-you-need.pdf")
    assert response_view.status_code == 200
    assert response_view.headers["content-type"] == "application/pdf"
    assert "inline" in response_view.headers.get("content-disposition", "")
    assert len(response_view.content) > 0

    # Test reference attachment download
    response_dl = client.get("/api/documents/reference/attention-is-all-you-need.pdf?download=true")
    assert response_dl.status_code == 200
    assert response_dl.headers["content-type"] == "application/pdf"
    assert "attachment" in response_dl.headers.get("content-disposition", "")
    assert len(response_dl.content) > 0

def test_upload_and_download_document():
    # Upload a small text file
    sample_content = b"# Attention Mechanisms\n\nTransformers use attention mechanisms to connect tokens."
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("test_doc.md", sample_content, "text/markdown")}
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["document_id"]

    # Test download endpoint
    dl_res = client.get(f"/api/documents/{doc_id}/download")
    assert dl_res.status_code == 200
    assert "attachment" in dl_res.headers.get("content-disposition", "")
    assert dl_res.content == sample_content

    # Test view endpoint
    view_res = client.get(f"/api/documents/{doc_id}/view")
    assert view_res.status_code == 200
    assert "inline" in view_res.headers.get("content-disposition", "")
    assert view_res.content == sample_content

    # Test raw content endpoint
    content_res = client.get(f"/api/documents/{doc_id}/content")
    assert content_res.status_code == 200
    assert "Attention Mechanisms" in content_res.json()["content"]

    # Test ingestion of text/markdown document
    ingest_res = client.post(f"/api/documents/{doc_id}/ingest")
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "ingested"
    assert ingest_res.json()["chunk_count"] > 0
