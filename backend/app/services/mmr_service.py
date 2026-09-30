import logging
from typing import List, Tuple, Dict, Any, Optional
from app.models.responses import DocumentChunkModel, MMRMetadata
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class MMRService:
    """
    Maximum Marginal Relevance (MMR) retrieval service.
    Exposes candidate pool size, lambda parameter, and final selected subset.
    """

    def search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 10,
        lambda_mult: float = 0.5,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], MMRMetadata, List[DocumentChunkModel]]:
        """
        Executes MMR retrieval and tracks intermediate candidate pool.
        """
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        
        # 1. Fetch larger candidate pool for visualization
        candidate_pool_results = vector_store_service.similarity_search_with_scores(
            query=query,
            k=fetch_k,
            filter_dict=filter_dict
        )
        candidate_pool = [c for c, _, _ in candidate_pool_results]

        # 2. Run MMR selection
        selected_results = vector_store_service.mmr_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
            filter_dict=filter_dict
        )

        mmr_meta = MMRMetadata(
            candidate_pool_size=len(candidate_pool),
            final_selected_count=len(selected_results),
            lambda_mult=lambda_mult
        )

        return selected_results, mmr_meta, candidate_pool

mmr_service = MMRService()
