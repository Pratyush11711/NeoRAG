import logging
from typing import Dict, List, Tuple
from app.models.responses import DocumentChunkModel, RRFContribution

logger = logging.getLogger(__name__)

class RRFService:
    """
    Implements explicit Reciprocal Rank Fusion (RRF).
    Formula: contribution = 1 / (k + rank)
    Default k = 60.
    """

    @staticmethod
    def fuse(
        ranked_lists: Dict[str, List[Tuple[DocumentChunkModel, float, int]]],
        k: int = 60
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[RRFContribution]]:
        """
        Combines multiple ranked lists into a single fused ranking.
        
        Args:
            ranked_lists: Map of source name (e.g. "query_1", "vector") to list of (chunk, score, rank)
            k: RRF constant (default 60)

        Returns:
            fused_chunks: List of (DocumentChunkModel, final_rrf_score, rank)
            rrf_contributions: Detailed RRFContribution models showing exact contributions per source
        """
        chunk_map: Dict[str, DocumentChunkModel] = {}
        rrf_scores: Dict[str, float] = {}
        ranks_map: Dict[str, Dict[str, int]] = {}
        contributions_map: Dict[str, Dict[str, float]] = {}

        for source_name, items in ranked_lists.items():
            for chunk, score, rank in items:
                chunk_id = chunk.chunk_id
                chunk_map[chunk_id] = chunk

                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = 0.0
                    ranks_map[chunk_id] = {}
                    contributions_map[chunk_id] = {}

                # Calculate RRF contribution: 1 / (k + rank)
                contribution = 1.0 / (k + rank)
                rrf_scores[chunk_id] += contribution
                ranks_map[chunk_id][source_name] = rank
                contributions_map[chunk_id][source_name] = round(contribution, 6)

        # Sort chunks by final RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused_results: List[Tuple[DocumentChunkModel, float, int]] = []
        rrf_contributions: List[RRFContribution] = []

        for final_rank, cid in enumerate(sorted_chunk_ids, start=1):
            chunk = chunk_map[cid]
            final_score = round(rrf_scores[cid], 6)
            fused_results.append((chunk, final_score, final_rank))

            rrf_contributions.append(RRFContribution(
                chunk_id=cid,
                rrf_score=final_score,
                ranks=ranks_map[cid],
                contributions=contributions_map[cid]
            ))

        return fused_results, rrf_contributions

rrf_service = RRFService()
