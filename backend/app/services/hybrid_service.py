import logging
from typing import List, Tuple, Dict, Any, Optional
from app.models.responses import DocumentChunkModel, HybridFusionResult, RRFContribution
from app.services.vector_store import vector_store_service
from app.services.bm25_service import bm25_service
from app.services.rrf_service import rrf_service

logger = logging.getLogger(__name__)

class HybridService:
    """
    Implements:
    1. Weighted Hybrid Retrieval (Linear weighted score combination of Vector + BM25)
    2. Hybrid + RRF (Reciprocal Rank Fusion combination of Vector + BM25)
    """

    def weighted_hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[HybridFusionResult]]:
        """
        Combines vector search and BM25 keyword search using configurable weights.
        """
        # Fetch vector results
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        vector_results = vector_store_service.similarity_search_with_scores(
            query=query,
            k=k * 2,
            filter_dict=filter_dict
        )

        # Fetch BM25 results
        bm25_results = bm25_service.search(
            query=query,
            k=k * 2,
            document_ids=document_ids
        )

        # Build lookups
        all_chunks: Dict[str, DocumentChunkModel] = {}
        vector_data: Dict[str, Tuple[float, int]] = {} # chunk_id -> (score, rank)
        bm25_data: Dict[str, Tuple[float, int]] = {}   # chunk_id -> (score, rank)

        for chunk, score, rank in vector_results:
            all_chunks[chunk.chunk_id] = chunk
            vector_data[chunk.chunk_id] = (score, rank)

        for chunk, score, rank in bm25_results:
            all_chunks[chunk.chunk_id] = chunk
            bm25_data[chunk.chunk_id] = (score, rank)

        # Normalize weights so they sum to 1.0
        total_weight = vector_weight + bm25_weight
        w_vec = vector_weight / total_weight if total_weight > 0 else 0.5
        w_bm25 = bm25_weight / total_weight if total_weight > 0 else 0.5

        combined_scores: Dict[str, float] = {}
        fusion_details: List[HybridFusionResult] = []

        for chunk_id, chunk in all_chunks.items():
            vec_score, vec_rank = vector_data.get(chunk_id, (0.0, None))
            b_score, b_rank = bm25_data.get(chunk_id, (0.0, None))

            final_score = (w_vec * vec_score) + (w_bm25 * b_score)
            combined_scores[chunk_id] = final_score

            fusion_details.append(HybridFusionResult(
                chunk_id=chunk_id,
                vector_score=round(vec_score, 4) if vec_rank is not None else None,
                bm25_score=round(b_score, 4) if b_rank is not None else None,
                vector_rank=vec_rank,
                bm25_rank=b_rank,
                final_score=round(final_score, 4),
                vector_weight=round(w_vec, 2),
                bm25_weight=round(w_bm25, 2),
                method="linear_weighted"
            ))

        # Sort descending by final combined score
        sorted_ids = sorted(combined_scores.keys(), key=lambda cid: combined_scores[cid], reverse=True)[:k]
        
        # Sort fusion_details to match rank order
        fusion_lookup = {f.chunk_id: f for f in fusion_details}
        ordered_fusion_details = [fusion_lookup[cid] for cid in sorted_ids]

        results: List[Tuple[DocumentChunkModel, float, int]] = []
        for rank, cid in enumerate(sorted_ids, start=1):
            results.append((all_chunks[cid], round(combined_scores[cid], 4), rank))

        return results, ordered_fusion_details

    def rrf_hybrid_search(
        self,
        query: str,
        k: int = 5,
        rrf_k: int = 60,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[RRFContribution], List[HybridFusionResult]]:
        """
        Combines vector search and BM25 search using explicit Reciprocal Rank Fusion.
        """
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        vector_results = vector_store_service.similarity_search_with_scores(
            query=query,
            k=k * 2,
            filter_dict=filter_dict
        )

        bm25_results = bm25_service.search(
            query=query,
            k=k * 2,
            document_ids=document_ids
        )

        ranked_lists = {
            "vector": vector_results,
            "bm25": bm25_results
        }

        fused_results, rrf_contributions = rrf_service.fuse(ranked_lists, k=rrf_k)
        top_k_fused = fused_results[:k]
        
        # Build hybrid results models for UI consistency
        hybrid_results: List[HybridFusionResult] = []
        for chunk, score, rank in top_k_fused:
            vec_rank = next((r for c, s, r in vector_results if c.chunk_id == chunk.chunk_id), None)
            vec_score = next((s for c, s, r in vector_results if c.chunk_id == chunk.chunk_id), None)
            b_rank = next((r for c, s, r in bm25_results if c.chunk_id == chunk.chunk_id), None)
            b_score = next((s for c, s, r in bm25_results if c.chunk_id == chunk.chunk_id), None)

            hybrid_results.append(HybridFusionResult(
                chunk_id=chunk.chunk_id,
                vector_score=vec_score,
                bm25_score=b_score,
                vector_rank=vec_rank,
                bm25_rank=b_rank,
                final_score=score,
                vector_weight=1.0,
                bm25_weight=1.0,
                method="rrf"
            ))

        return top_k_fused, rrf_contributions[:k], hybrid_results

hybrid_service = HybridService()
