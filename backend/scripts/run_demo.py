import os
import sys
import json
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

def run_demo():
    print("=" * 60)
    print("STARTING MULTIMODAL RAG BACKEND DEMO")
    print("=" * 60)

    client = TestClient(app)

    # 1. Health Check
    health_res = client.get("/health")
    print(f"\n[1] Health Check: {health_res.status_code}")
    print(json.dumps(health_res.json(), indent=2))

    # 2. Upload attention-is-all-you-need.pdf
    pdf_path = backend_dir / "docs" / "attention-is-all-you-need.pdf"
    if not pdf_path.exists():
        pdf_path = backend_dir.parent / "docs" / "attention-is-all-you-need.pdf"

    print(f"\n[2] Uploading: {pdf_path}")
    with open(pdf_path, "rb") as f:
        upload_res = client.post(
            "/api/documents/upload",
            files={"file": ("attention-is-all-you-need.pdf", f, "application/pdf")}
        )

    print(f"Upload Response: {upload_res.status_code}")
    upload_data = upload_res.json()
    print(json.dumps(upload_data, indent=2))
    doc_id = upload_data["document_id"]

    # 3. Ingest Document
    print(f"\n[3] Ingesting Document: {doc_id}...")
    ingest_res = client.post(f"/api/documents/{doc_id}/ingest", json={"force_reprocess": True})
    print(f"Ingest Response: {ingest_res.status_code}")
    print(json.dumps(ingest_res.json(), indent=2))

    # 4. Search query: "attention is all you need" with MMR
    query_1 = "attention is all you need"
    print(f"\n[4] Executing Search: '{query_1}' (Strategy: mmr)")
    search_res = client.post(
        "/api/retrieval/search",
        json={"query": query_1, "strategy": "mmr", "k": 3, "fetch_k": 5}
    )
    print(f"Search Response: {search_res.status_code}")
    s_data = search_res.json()
    print(f"Retrieved {len(s_data.get('documents', []))} documents in {s_data.get('total_duration_ms')} ms")
    print("Pipeline Trace:")
    for stage in s_data.get("pipeline_trace", []):
        print(f"  - Stage: {stage['stage']}, Duration: {stage['duration_ms']} ms")

    # 5. Search query: "What are the two main components of the Transformer architecture?" with hybrid_rrf
    query_2 = "What are the two main components of the Transformer architecture?"
    print(f"\n[5] Executing Search: '{query_2}' (Strategy: hybrid_rrf)")
    hybrid_res = client.post(
        "/api/retrieval/search",
        json={"query": query_2, "strategy": "hybrid_rrf", "k": 3, "rrf_k": 60}
    )
    print(f"Hybrid RRF Response: {hybrid_res.status_code}")
    h_data = hybrid_res.json()
    print("RRF Contributions:")
    for rrf in h_data.get("rrf_results", []):
        print(f"  - Chunk: {rrf['chunk_id']}, Score: {rrf['rrf_score']}, Ranks: {rrf['ranks']}")

    # 6. Chat query with full_pipeline
    print(f"\n[6] Executing RAG Chat: '{query_2}' (Strategy: full_pipeline)")
    chat_res = client.post(
        "/api/chat",
        json={"query": query_2, "strategy": "full_pipeline", "debug": True}
    )
    print(f"Chat Response: {chat_res.status_code}")
    c_data = chat_res.json()
    print(f"\nGenerated Answer:\n{c_data.get('answer')}")
    print("\nSources:")
    for src in c_data.get("sources", []):
        print(f"  - Source ID: {src['source_id']}, Document: {src['document']}, Page: {src.get('page')}")
    print("\nFull Pipeline Trace:")
    for stage in c_data.get("pipeline_trace", []):
        print(f"  - Stage: {stage['stage']}, Duration: {stage['duration_ms']} ms")

    print("\n" + "=" * 60)
    print("DEMO RUN COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
