from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ImageContent(BaseModel):
    image_id: str
    mime_type: str = "image/jpeg"
    base64: str
    page_number: Optional[int] = None
    caption: Optional[str] = None

class TableContent(BaseModel):
    table_id: str
    html: str
    text: Optional[str] = None
    page_number: Optional[int] = None

class DocumentChunkModel(BaseModel):
    chunk_id: str
    document_id: str
    page_content: str
    raw_text: str
    tables: List[TableContent] = Field(default_factory=list)
    images: List[ImageContent] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list) # e.g. ["text", "table", "image"]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    gemini_chat_model: str
    gemini_embedding_model: str
    chroma_collection: str
    total_documents: int
    total_chunks: int
    security: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size_bytes: int
    status: str
    message: str

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    upload_date: str
    status: str # "uploaded", "ingesting", "ingested", "failed"
    element_count: int = 0
    chunk_count: int = 0
    tables_count: int = 0
    images_count: int = 0
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int

class IngestResponse(BaseModel):
    document_id: str
    status: str
    chunk_count: int
    element_count: int
    tables_count: int
    images_count: int
    message: str

class RetrievedDocument(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    raw_text: Optional[str] = None
    source: str
    page: Optional[int] = None
    rank: int
    score: Optional[float] = None
    tables: List[TableContent] = Field(default_factory=list)
    images: List[ImageContent] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RRFContribution(BaseModel):
    chunk_id: str
    rrf_score: float
    ranks: Dict[str, int] = Field(default_factory=dict)
    contributions: Dict[str, float] = Field(default_factory=dict)

class HybridFusionResult(BaseModel):
    chunk_id: str
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    final_score: float
    vector_weight: float
    bm25_weight: float
    method: str

class RerankResult(BaseModel):
    document_id: str # chunk_id
    original_rank: int
    reranked_rank: int
    relevance_explanation: Optional[str] = None

class PipelineStageTrace(BaseModel):
    stage: str
    duration_ms: float
    input_count: Optional[int] = None
    output_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SourceCitation(BaseModel):
    source_id: str
    document: str
    page: Optional[int] = None
    chunk_id: str
    source_path: Optional[str] = None
    retrieval_rank: Optional[int] = None
    retrieval_method: Optional[str] = None
    reranker_rank: Optional[int] = None

class MMRMetadata(BaseModel):
    candidate_pool_size: int
    final_selected_count: int
    lambda_mult: float

class SearchResponse(BaseModel):
    run_id: str
    query: str
    strategy: str
    total_duration_ms: float
    documents: List[RetrievedDocument] = Field(default_factory=list)
    query_variations: List[str] = Field(default_factory=list)
    rrf_results: List[RRFContribution] = Field(default_factory=list)
    hybrid_results: List[HybridFusionResult] = Field(default_factory=list)
    rerank_results: List[RerankResult] = Field(default_factory=list)
    mmr_meta: Optional[MMRMetadata] = None
    pipeline_trace: List[PipelineStageTrace] = Field(default_factory=list)

class ChatResponse(BaseModel):
    run_id: str
    query: str
    answer: str
    sources: List[SourceCitation] = Field(default_factory=list)
    retrieved_documents: List[RetrievedDocument] = Field(default_factory=list)
    query_variations: List[str] = Field(default_factory=list)
    fusion_results: List[Dict[str, Any]] = Field(default_factory=list)
    reranking_results: List[RerankResult] = Field(default_factory=list)
    pipeline_trace: List[PipelineStageTrace] = Field(default_factory=list)
    strategy: str
    total_duration_ms: float
    model_name: str
    token_usage: Optional[Dict[str, int]] = None
    debug_info: Optional[Dict[str, Any]] = None

class RunHistoryItem(BaseModel):
    run_id: str
    query: str
    strategy: str
    created_at: str
    duration_ms: float
    number_of_candidates: int
    final_answer: Optional[str] = None
    sources_count: int = 0

class RunHistoryResponse(BaseModel):
    runs: List[RunHistoryItem]
    total: int

class StructuredErrorDetail(BaseModel):
    code: str
    message: str
    stage: str
    details: Optional[Dict[str, Any]] = None

class StructuredErrorResponse(BaseModel):
    error: StructuredErrorDetail
