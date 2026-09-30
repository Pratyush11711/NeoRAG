from typing import Optional, List
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    force_reprocess: bool = Field(False, description="Whether to reprocess an already ingested document")
    enable_multimodal_summary: Optional[bool] = Field(None, description="Override multimodal summary enhancement")
    max_characters: Optional[int] = Field(None, description="Max characters for title chunking")
    new_after_n_chars: Optional[int] = Field(None, description="Soft max characters for title chunking")
    combine_text_under_n_chars: Optional[int] = Field(None, description="Combine text under n chars threshold")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    strategy: str = Field(
        "similarity", 
        description="Retrieval strategy: similarity | similarity_threshold | mmr | multi_query | multi_query_rrf | bm25 | hybrid | hybrid_rrf | hybrid_rerank | full_pipeline"
    )
    k: int = Field(5, ge=1, le=50, description="Number of documents to return")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score threshold")
    fetch_k: Optional[int] = Field(10, ge=1, le=100, description="Number of candidates to fetch for MMR")
    lambda_mult: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="MMR diversity vs relevance balance (0 for max diversity, 1 for min)")
    query_variations_count: Optional[int] = Field(3, ge=1, le=5, description="Number of query variations for multi_query")
    vector_weight: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Weight for vector search in hybrid retrieval")
    bm25_weight: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="Weight for BM25 in hybrid retrieval")
    rrf_k: Optional[int] = Field(60, ge=1, le=200, description="Constant k for Reciprocal Rank Fusion formula: 1 / (k + rank)")
    rerank_top_n: Optional[int] = Field(10, ge=1, le=50, description="Number of retrieved candidates to pass to Gemini reranker")
    document_ids: Optional[List[str]] = Field(None, description="Optional filter to retrieve only from specific document IDs")
    debug: bool = Field(True, description="When true, returns full intermediate traces and pipeline metrics")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query / question")
    strategy: str = Field(
        "full_pipeline",
        description="Retrieval strategy: similarity | similarity_threshold | mmr | multi_query | multi_query_rrf | bm25 | hybrid | hybrid_rrf | hybrid_rerank | full_pipeline"
    )
    k: Optional[int] = Field(5, ge=1, le=50, description="Retrieved candidate count")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score threshold for threshold search")
    fetch_k: Optional[int] = Field(10, ge=1, le=100, description="Fetch candidates for MMR")
    lambda_mult: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="MMR lambda multiplier")
    query_variations_count: Optional[int] = Field(3, ge=1, le=5, description="Number of query variations to generate")
    vector_weight: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Vector search weight in hybrid")
    bm25_weight: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="BM25 search weight in hybrid")
    rrf_k: Optional[int] = Field(60, ge=1, le=200, description="RRF constant k")
    rerank_top_n: Optional[int] = Field(10, ge=1, le=50, description="Number of candidates to rerank")
    final_context_k: Optional[int] = Field(5, ge=1, le=20, description="Top N context chunks to pass into final answer generator")
    include_images: bool = Field(True, description="Whether to include relevant images in the multimodal LLM prompt")
    document_ids: Optional[List[str]] = Field(None, description="Optional document filter")
    debug: bool = Field(True, description="Return intermediate pipeline details for visualization")
