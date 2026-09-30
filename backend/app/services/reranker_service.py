import logging
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.models.responses import DocumentChunkModel, RerankResult

logger = logging.getLogger(__name__)

class RerankItem(BaseModel):
    candidate_index: int = Field(..., description="The 1-based index of the candidate document")
    relevance_explanation: Optional[str] = Field(None, description="Brief explanation of why this chunk is relevant")

class RerankOutput(BaseModel):
    ranking: List[RerankItem] = Field(..., description="Ordered list of candidates from most to least relevant")

class RerankerService:
    """
    LLM-based reranker using Gemini.
    Reranks candidate chunks based on semantic relevance to the query.
    """

    def __init__(self):
        self.settings = get_settings()

    async def rerank(
        self,
        query: str,
        candidates: List[DocumentChunkModel],
        top_n: Optional[int] = None
    ) -> Tuple[List[DocumentChunkModel], List[RerankResult]]:
        """
        Reranks candidates using Gemini LLM.
        """
        limit = top_n or self.settings.RERANK_TOP_N
        pool = candidates[:limit]

        if not pool:
            return [], []

        if len(pool) == 1:
            res = [RerankResult(
                document_id=pool[0].chunk_id,
                original_rank=1,
                reranked_rank=1,
                relevance_explanation="Single candidate retained."
            )]
            return pool, res

        if not self.settings.ENABLE_RERANKING or not self.settings.GOOGLE_API_KEY:
            logger.info("Reranking disabled or GOOGLE_API_KEY missing. Preserving original retrieval ranking.")
            results = [
                RerankResult(
                    document_id=chunk.chunk_id,
                    original_rank=idx + 1,
                    reranked_rank=idx + 1,
                    relevance_explanation="Reranking bypassed; original rank preserved."
                )
                for idx, chunk in enumerate(pool)
            ]
            return pool, results

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(
                model=self.settings.GEMINI_CHAT_MODEL,
                google_api_key=self.settings.GOOGLE_API_KEY,
                temperature=0.0,
                max_retries=self.settings.GEMINI_MAX_RETRIES
            )
            structured_llm = llm.with_structured_output(RerankOutput)

            # Build candidates list prompt
            doc_descriptions = []
            for i, chunk in enumerate(pool, start=1):
                preview = chunk.raw_text[:350].replace("\n", " ")
                has_multimodal = ""
                if chunk.tables:
                    has_multimodal += f" [Contains {len(chunk.tables)} Table(s)]"
                if chunk.images:
                    has_multimodal += f" [Contains {len(chunk.images)} Image(s)]"
                doc_descriptions.append(f"[{i}] ID: {chunk.chunk_id}{has_multimodal}\nContent: {preview}")

            candidates_text = "\n\n".join(doc_descriptions)

            prompt = (
                f"You are an expert search reranker. Evaluate the following candidate document chunks "
                f"for their direct relevance to answering the user query.\n\n"
                f"Query: \"{query}\"\n\n"
                f"Candidate Documents:\n{candidates_text}\n\n"
                f"Task: Return ALL candidate indices ordered from MOST relevant to LEAST relevant. "
                f"Provide a brief 1-sentence relevance explanation for each."
            )

            loop = asyncio.get_event_loop()
            result: RerankOutput = await loop.run_in_executor(
                None,
                lambda: structured_llm.invoke([HumanMessage(content=prompt)])
            )

            if result and hasattr(result, "ranking") and result.ranking:
                reranked_chunks: List[DocumentChunkModel] = []
                rerank_results: List[RerankResult] = []
                seen_indices = set()

                for new_rank, item in enumerate(result.ranking, start=1):
                    c_idx = item.candidate_index - 1
                    if 0 <= c_idx < len(pool) and c_idx not in seen_indices:
                        seen_indices.add(c_idx)
                        chunk = pool[c_idx]
                        orig_rank = c_idx + 1
                        reranked_chunks.append(chunk)
                        rerank_results.append(RerankResult(
                            document_id=chunk.chunk_id,
                            original_rank=orig_rank,
                            reranked_rank=new_rank,
                            relevance_explanation=item.relevance_explanation
                        ))

                # Append any candidates missed by LLM to maintain complete set
                for orig_idx, chunk in enumerate(pool):
                    if orig_idx not in seen_indices:
                        new_rank = len(reranked_chunks) + 1
                        reranked_chunks.append(chunk)
                        rerank_results.append(RerankResult(
                            document_id=chunk.chunk_id,
                            original_rank=orig_idx + 1,
                            reranked_rank=new_rank,
                            relevance_explanation="Appended at tail (unranked by model)."
                        ))

                logger.info(f"Successfully reranked {len(reranked_chunks)} documents via Gemini.")
                return reranked_chunks, rerank_results

        except Exception as e:
            logger.error(f"Gemini reranking failed ({e}). Falling back to original retrieval order.")

        fallback_results = [
            RerankResult(
                document_id=chunk.chunk_id,
                original_rank=idx + 1,
                reranked_rank=idx + 1,
                relevance_explanation="Reranking fallback; original rank preserved."
            )
            for idx, chunk in enumerate(pool)
        ]
        return pool, fallback_results

reranker_service = RerankerService()
