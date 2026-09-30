import logging
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.models.responses import DocumentChunkModel, RRFContribution
from app.services.vector_store import vector_store_service
from app.services.rrf_service import rrf_service

logger = logging.getLogger(__name__)

class QueryVariations(BaseModel):
    variations: List[str] = Field(
        ...,
        description="A list of 3 diverse, semantically distinct query formulations or sub-questions"
    )

class MultiQueryService:
    """
    Generates diverse query variations using Gemini with structured output,
    retrieves candidates for each variation, and provides fusion options.
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate_query_variations(
        self,
        query: str,
        count: int = 3
    ) -> List[str]:
        """
        Uses Gemini Chat model with structured Pydantic output to produce alternative search queries.
        """
        if not self.settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set. Using rule-based fallback query variations.")
            return [
                f"{query} overview and details",
                f"key concepts of {query}",
                f"{query} architectural components and specifications"
            ][:count]

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model=self.settings.GEMINI_CHAT_MODEL,
                google_api_key=self.settings.GOOGLE_API_KEY,
                temperature=0.7,
                max_retries=self.settings.GEMINI_MAX_RETRIES
            )

            # Use LangChain structured output
            structured_llm = llm.with_structured_output(QueryVariations)

            prompt = (
                f"You are an AI search query optimizer. Given the following user question, "
                f"generate exactly {count} distinct search queries that explore different perspectives, "
                f"synonyms, technical terms, and component breakdowns.\n\n"
                f"User Query: {query}"
            )

            loop = asyncio.get_event_loop()
            result: QueryVariations = await loop.run_in_executor(
                None,
                lambda: structured_llm.invoke([HumanMessage(content=prompt)])
            )

            if result and hasattr(result, "variations") and result.variations:
                logger.info(f"Generated {len(result.variations)} query variations via Gemini.")
                return result.variations[:count]

        except Exception as e:
            logger.warning(f"Structured query generation failed ({e}). Falling back to standard query variations.")

        return [
            f"{query} technical analysis",
            f"{query} key findings and components",
            f"detailed explanation of {query}"
        ][:count]

    async def search_multi_query(
        self,
        query: str,
        k: int = 5,
        variations_count: int = 3,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[str]]:
        """
        Retrieves documents for original query + all variations, deduplicating candidates.
        """
        variations = await self.generate_query_variations(query, count=variations_count)
        all_queries = [query] + variations

        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        seen_chunk_ids = set()
        deduped_results: List[Tuple[DocumentChunkModel, float, int]] = []

        for q in all_queries:
            sub_results = vector_store_service.similarity_search_with_scores(
                query=q,
                k=k,
                filter_dict=filter_dict
            )
            for chunk, score, _ in sub_results:
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    deduped_results.append((chunk, score, len(deduped_results) + 1))
                if len(deduped_results) >= k:
                    break
            if len(deduped_results) >= k:
                break

        return deduped_results[:k], variations

    async def search_multi_query_rrf(
        self,
        query: str,
        k: int = 5,
        variations_count: int = 3,
        rrf_k: int = 60,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[str], List[RRFContribution]]:
        """
        Retrieves documents for original query and all variations, then applies explicit RRF.
        Returns:
            fused_candidates: List of (chunk, score, rank)
            variations: List of generated query variations
            rrf_contributions: Full RRF contribution trace per query variation
        """
        variations = await self.generate_query_variations(query, count=variations_count)
        
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        ranked_lists: Dict[str, List[Tuple[DocumentChunkModel, float, int]]] = {}

        # 1. Original query
        orig_results = vector_store_service.similarity_search_with_scores(
            query=query,
            k=k * 2,
            filter_dict=filter_dict
        )
        ranked_lists["original_query"] = orig_results

        # 2. Each variation
        for idx, var in enumerate(variations, start=1):
            var_results = vector_store_service.similarity_search_with_scores(
                query=var,
                k=k * 2,
                filter_dict=filter_dict
            )
            ranked_lists[f"query_variation_{idx}"] = var_results

        # Explicit RRF fusion across queries
        fused_results, rrf_contributions = rrf_service.fuse(ranked_lists, k=rrf_k)
        return fused_results[:k], variations, rrf_contributions[:k]

multi_query_service = MultiQueryService()
