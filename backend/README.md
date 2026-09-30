# Multimodal RAG Backend with Gemini, ChromaDB & Observability

A complete, production-grade backend for an advanced **Multimodal Retrieval-Augmented Generation (RAG)** system built with **FastAPI**, **LangChain**, **ChromaDB**, **Gemini**, **Unstructured**, and **BM25**.

The backend exposes all intermediate RAG steps, candidate pools, Reciprocal Rank Fusion (RRF) contributions, hybrid scoring weights, Gemini LLM reranking order, table HTML, image payloads, source citations, and stage timings so a future React frontend can visualize the entire pipeline.

---

## 🌟 Key Features

1. **Multimodal Document Ingestion**:
   - PDF partitioning via `Unstructured` (hi_res / fast / fallback).
   - Extraction of text, titles, table structures (as HTML), and diagrams/images (as base64 payloads).
   - Configurable title-based chunking (`chunk_by_title`).
   - Optional Gemini multimodal summary augmentation (`ENABLE_MULTIMODAL_SUMMARY`).

2. **Unified Retrieval Strategies**:
   - `similarity`: Standard cosine similarity search over Gemini embeddings.
   - `similarity_threshold`: Distance filtering with accepted & discarded candidate pools.
   - `mmr`: Maximum Marginal Relevance search with configurable `fetch_k` and `lambda_mult`.
   - `multi_query`: Multi-angle query expansion using Gemini structured outputs.
   - `multi_query_rrf`: Multi-query expansion fused with explicit Reciprocal Rank Fusion.
   - `bm25`: Fast, local in-memory keyword retrieval with Okapi BM25.
   - `hybrid`: Linear weighted combination of Vector + BM25 (`vector_weight` + `bm25_weight`).
   - `hybrid_rrf`: Explicit Reciprocal Rank Fusion combining Vector and BM25 ranked candidate lists.
   - `hybrid_rerank`: Hybrid search followed by Gemini LLM reranking.
   - `full_pipeline`: Complete production pipeline: Query Expansion → Vector + BM25 → RRF Fusion → Candidate Pool → Gemini LLM Reranking → Context Selection → Gemini Answer Generation.

3. **Explicit Reciprocal Rank Fusion (RRF)**:
   - Formula: $\text{contribution} = \frac{1}{k + \text{rank}}$ (default $k = 60$).
   - Exposes exact per-query and per-retriever rank and score contribution for every chunk.

4. **Gemini LLM Reranker**:
   - Zero-shot neural reranking with explanation rationale directly from Gemini.
   - Preserves original and reranked positions.

5. **Full Pipeline Observability & Frontend Visualization**:
   - Execution traces with millisecond durations for each stage (`query_processing`, `query_generation`, `vector_retrieval`, `bm25_retrieval`, `rrf_fusion`, `gemini_reranking`, `generation`).
   - SQLite persistence of all runs and documents for "Run History" views.

---

## 🏗️ Architecture Overview

```
                      User Query
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌───────────────────┐             ┌───────────────────┐
│  Vector Search    │             │   BM25 Keyword    │
│ (Gemini Embeds +  │             │   Search (Local)  │
│    ChromaDB)      │             │                   │
└────────┬──────────┘             └────────┬──────────┘
         │                                 │
         │   Ranked List A     Ranked List B
         └────────────────┬────────────────┘
                          ▼
            ┌───────────────────────────┐
            │ Reciprocal Rank Fusion    │
            │ score = Σ 1/(k + rank)    │
            └─────────────┬─────────────┘
                          ▼
            ┌───────────────────────────┐
            │    Gemini LLM Reranker    │
            │    (Context Ordering)     │
            └─────────────┬─────────────┘
                          ▼
            ┌───────────────────────────┐
            │   Final Answer Generator  │
            │   (Gemini Flash + Context │
            │   + Tables + Base64 Imgs) │
            └─────────────┬─────────────┘
                          ▼
            Answer + Citations + Pipeline Trace
```

---

## 🚀 Quickstart & Setup (Windows PowerShell)

### 1. Prerequisites
- Python 3.12+ installed.
- Valid Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/).

### 2. Setup Virtual Environment

Open Windows PowerShell and navigate to the project directory:

```powershell
cd F:\RAG-project
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r backend\requirements.txt
```

### 4. Configure Environment Variables

Edit `backend\.env` (or copy from `backend\.env.example`):

```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

CHROMA_PERSIST_DIRECTORY=data/chroma
CHROMA_COLLECTION_NAME=multimodal_rag_collection
SQLITE_DB_PATH=data/metadata.db
UPLOADS_DIRECTORY=data/uploads
PROCESSED_DIRECTORY=data/processed

ENABLE_MULTIMODAL_SUMMARY=true
ENABLE_QUERY_EXPANSION=true
ENABLE_RERANKING=true
RETRIEVAL_K=5
RERANK_TOP_N=10
FINAL_CONTEXT_K=5
DEFAULT_RRF_K=60
DEFAULT_VECTOR_WEIGHT=0.7
DEFAULT_BM25_WEIGHT=0.3
```

*(Note: If `GOOGLE_API_KEY` is not provided, the backend automatically operates in an offline demonstration mode with deterministic mock embeddings and syntheses).*

---

## 🏃 Running the Application

### Start Backend Server

```powershell
cd F:\RAG-project\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Interactive Swagger Documentation
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Running the Demo Script & Tests

### Run Automated Test Suite (Pytest)
```powershell
cd F:\RAG-project
.\.venv\Scripts\pytest.exe backend\tests -v
```

### Run End-to-End Demo Script
Generates sample `attention-is-all-you-need.pdf` with tables & diagrams, uploads it, ingests it, and runs retrieval + chat benchmarks:
```powershell
cd F:\RAG-project
.\.venv\Scripts\python.exe backend\scripts\run_demo.py
```

---

## 📡 REST API Reference

### 1. Health Check
`GET /health`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "gemini_chat_model": "gemini-1.5-flash",
  "gemini_embedding_model": "models/text-embedding-004",
  "chroma_collection": "multimodal_rag_collection",
  "total_documents": 1,
  "total_chunks": 4
}
```

### 2. Document Upload
`POST /api/documents/upload` (Form Data: `file`)
```json
{
  "document_id": "doc_attention-is-all-you-need.pdf_e427e470",
  "filename": "attention-is-all-you-need.pdf",
  "file_size_bytes": 11598,
  "status": "uploaded",
  "message": "Document uploaded successfully. Ready for ingestion."
}
```

### 3. Document Ingest
`POST /api/documents/{document_id}/ingest`
```json
{
  "force_reprocess": false,
  "max_characters": 3000,
  "new_after_n_chars": 2400
}
```
**Response**:
```json
{
  "document_id": "doc_attention-is-all-you-need.pdf_e427e470",
  "status": "ingested",
  "chunk_count": 3,
  "element_count": 8,
  "tables_count": 1,
  "images_count": 1,
  "message": "Document ingestion, multimodal extraction, and vector indexing completed successfully."
}
```

### 4. Advanced Retrieval Search
`POST /api/retrieval/search`
```json
{
  "query": "What are the two main components of the Transformer architecture?",
  "strategy": "hybrid_rrf",
  "k": 5,
  "rrf_k": 60,
  "debug": true
}
```
**Response includes**:
- `documents`: List of chunks with raw text, table HTML, image base64, scores, and ranks.
- `rrf_results`: Exact breakdown of ranks and score contribution per retriever:
```json
{
  "chunk_id": "doc_attention_chunk_0001",
  "rrf_score": 0.032787,
  "ranks": { "vector": 1, "bm25": 1 },
  "contributions": { "vector": 0.016393, "bm25": 0.016393 }
}
```
- `pipeline_trace`: Stage durations in milliseconds.

### 5. Chat Generation Endpoint
`POST /api/chat`
```json
{
  "query": "What are the two main components of the Transformer architecture?",
  "strategy": "full_pipeline",
  "k": 5,
  "final_context_k": 3,
  "include_images": true,
  "debug": true
}
```
**Response**:
```json
{
  "run_id": "run_a1b2c3d4e5f6",
  "query": "What are the two main components of the Transformer architecture?",
  "answer": "The two main components of the Transformer architecture are the Encoder and the Decoder [chunk_0001]. The encoder maps an input sequence to continuous representations, while the decoder generates an output sequence one element at a time.",
  "sources": [
    {
      "source_id": "chunk_0001",
      "document": "attention-is-all-you-need.pdf",
      "page": 2,
      "chunk_id": "doc_attention_chunk_0001",
      "retrieval_rank": 1,
      "retrieval_method": "full_pipeline",
      "reranker_rank": 1
    }
  ],
  "pipeline_trace": [
    { "stage": "query_processing", "duration_ms": 0.05 },
    { "stage": "query_generation", "duration_ms": 320.12 },
    { "stage": "vector_retrieval", "duration_ms": 45.2 },
    { "stage": "bm25_retrieval", "duration_ms": 3.4 },
    { "stage": "rrf_fusion", "duration_ms": 0.8 },
    { "stage": "gemini_reranking", "duration_ms": 612.4 },
    { "stage": "generation", "duration_ms": 940.8 }
  ],
  "strategy": "full_pipeline",
  "total_duration_ms": 1922.77,
  "model_name": "gemini-1.5-flash"
}
```

### 6. Run History
`GET /api/retrieval/runs`
Lists all historical queries, strategies, durations, candidate counts, and answers.

---

## 🎨 Guidance for Future React Frontend

The backend API was designed to directly empower rich frontend visualizations:

1. **Pipeline Execution DAG**:
   - Use `pipeline_trace` to render animated flowchart nodes (Query $\to$ Vector/BM25 $\to$ RRF $\to$ Rerank $\to$ Gen).
   - Display each node's latency badge (e.g. `duration_ms`).

2. **RRF Visualization Table**:
   - Use `rrf_results` to show a breakdown table of how documents moved up/down due to query variations or multi-retriever fusion (`contributions.vector` vs `contributions.bm25`).

3. **MMR Exploration**:
   - Use `mmr_meta` to display the ratio of `final_selected_count` to `candidate_pool_size` alongside the `lambda_mult` slider.

4. **Multimodal Context Display**:
   - Render `tables[].html` inside sanitized HTML containers.
   - Render `images[].base64` directly using `<img src="data:image/jpeg;base64,..." />`.

5. **Source Citation Badges**:
   - Render interactive citation badges `[chunk_id]` in the generated answer that highlight corresponding source chunks upon click.
