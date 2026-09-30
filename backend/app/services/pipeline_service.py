import logging
import time
from typing import List, Tuple, Dict, Any, Optional
from app.core.config import get_settings
from app.models.requests import SearchRequest, ChatRequest
from app.models.responses import (
    SearchResponse, ChatResponse, RetrievedDocument, RRFContribution,
    HybridFusionResult, RerankResult, PipelineStageTrace, SourceCitation
)
from app.services.vector_store import vector_store_service
from app.services.bm25_service import bm25_service
from app.services.multi_query_service import multi_query_service
from app.services.rrf_service import rrf_service
from app.services.hybrid_service import hybrid_service
from app.services.reranker_service import reranker_service
from app.services.generation_service import generation_service
from app.services.retrieval_service import retrieval_service
from app.services.db_service import db_service
from app.utils.ids import generate_run_id

logger = logging.getLogger(__name__)

class PipelineService:
    """
    Orchestrates the entire MultiModal RAG pipeline and manages intermediate
    trace observability for the future frontend visualizer.
    """

    def __init__(self):
        self.settings = get_settings()

    async def execute_full_retrieval(self, req: SearchRequest) -> SearchResponse:
        """
        Executes the multi-stage full pipeline retrieval:
        Query Expansion -> Vector + BM25 -> RRF Fusion -> Gemini Reranker
        """
        run_id = generate_run_id()
        start_overall = time.perf_counter()
        pipeline_trace: List[PipelineStageTrace] = []

        # Stage 1: Query processing
        t_stage = time.perf_counter()
        cleaned_query = req.query.strip()
        pipeline_trace.append(PipelineStageTrace(
            stage="query_processing",
            duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
            input_count=1,
            output_count=1,
            metadata={"query": cleaned_query}
        ))

        # Stage 2: Query expansion
        query_variations = []
        if self.settings.ENABLE_QUERY_EXPANSION:
            t_stage = time.perf_counter()
            query_variations = await multi_query_service.generate_query_variations(
                cleaned_query,
                count=req.query_variations_count or 3
            )
            pipeline_trace.append(PipelineStageTrace(
                stage="query_generation",
                duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
                input_count=1,
                output_count=len(query_variations),
                metadata={"variations": query_variations}
            ))

        # Stage 3: Vector retrieval (across original query + variations)
        t_stage = time.perf_counter()
        all_queries = [cleaned_query] + query_variations
        filter_dict = {"document_id": {"$in": req.document_ids}} if req.document_ids else None
        
        vector_ranked_lists = {}
        for q_idx, q in enumerate(all_queries):
            q_label = "original" if q_idx == 0 else f"variation_{q_idx}"
            results = vector_store_service.similarity_search_with_scores(
                query=q,
                k=req.fetch_k or 10,
                filter_dict=filter_dict
            )
            vector_ranked_lists[q_label] = results

        # Primary vector candidates from original query
        primary_vector_res = vector_ranked_lists["original"]
        pipeline_trace.append(PipelineStageTrace(
            stage="vector_retrieval",
            duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
            input_count=len(all_queries),
            output_count=sum(len(v) for v in vector_ranked_lists.values()),
            metadata={"primary_candidates": len(primary_vector_res)}
        ))

        # Stage 4: BM25 retrieval
        t_stage = time.perf_counter()
        bm25_res = bm25_service.search(
            query=cleaned_query,
            k=req.fetch_k or 10,
            document_ids=req.document_ids
        )
        pipeline_trace.append(PipelineStageTrace(
            stage="bm25_retrieval",
            duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
            input_count=1,
            output_count=len(bm25_res),
            metadata={"bm25_candidates": len(bm25_res)}
        ))

        # Stage 5: Hybrid Fusion via RRF
        t_stage = time.perf_counter()
        fusion_input_lists = {"vector": primary_vector_res, "bm25": bm25_res}
        # Add query variations if present
        for q_lbl, res in vector_ranked_lists.items():
            if q_lbl != "original" and res:
                fusion_input_lists[q_lbl] = res

        fused_candidates, rrf_contributions = rrf_service.fuse(
            ranked_lists=fusion_input_lists,
            k=req.rrf_k or self.settings.DEFAULT_RRF_K
        )
        pipeline_trace.append(PipelineStageTrace(
            stage="rrf_fusion",
            duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
            input_count=sum(len(l) for l in fusion_input_lists.values()),
            output_count=len(fused_candidates),
            metadata={"rrf_k": req.rrf_k or self.settings.DEFAULT_RRF_K}
        ))

        # Stage 6: Candidate pool selection for Reranking
        rerank_limit = req.rerank_top_n or self.settings.RERANK_TOP_N
        candidate_pool = [c for c, _, _ in fused_candidates[:rerank_limit]]

        # Stage 7: Gemini Reranking
        t_stage = time.perf_counter()
        reranked_chunks, rerank_results = await reranker_service.rerank(
            query=cleaned_query,
            candidates=candidate_pool,
            top_n=req.k
        )
        pipeline_trace.append(PipelineStageTrace(
            stage="gemini_reranking",
            duration_ms=round((time.perf_counter() - t_stage) * 1000, 2),
            input_count=len(candidate_pool),
            output_count=len(reranked_chunks),
            metadata={"model": self.settings.GEMINI_CHAT_MODEL}
        ))

        final_chunks = reranked_chunks[:req.k]
        final_docs = [
            RetrievedDocument(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                content=c.page_content,
                raw_text=c.raw_text,
                source=str(c.metadata.get("source", c.document_id)),
                page=c.metadata.get("page_number"),
                rank=idx + 1,
                score=None,
                tables=c.tables,
                images=c.images,
                content_types=c.content_types,
                metadata=c.metadata
            )
            for idx, c in enumerate(final_chunks)
        ]

        total_duration_ms = (time.perf_counter() - start_overall) * 1000

        return SearchResponse(
            run_id=run_id,
            query=cleaned_query,
            strategy="full_pipeline",
            total_duration_ms=round(total_duration_ms, 2),
            documents=final_docs,
            query_variations=query_variations,
            rrf_results=rrf_contributions[:req.k],
            hybrid_results=[],
            rerank_results=rerank_results,
            pipeline_trace=pipeline_trace
        )

    async def execute_chat(self, req: ChatRequest) -> ChatResponse:
        """
        Executes end-to-end chat generation with complete observability trace.
        """
        run_id = generate_run_id()
        start_overall = time.perf_counter()
        pipeline_trace: List[PipelineStageTrace] = []

        query = req.query.strip()
        strategy = req.strategy.lower().strip()
        context_k = req.final_context_k or self.settings.FINAL_CONTEXT_K

        retrieved_documents: List[RetrievedDocument] = []
        query_variations: List[str] = []
        fusion_results: List[Dict[str, Any]] = []
        reranking_results: List[RerankResult] = []
        context_chunks: List[Any] = []

        if strategy == "full_pipeline":
            # Execute full pipeline retrieval
            search_req = SearchRequest(
                query=query,
                strategy="full_pipeline",
                k=context_k,
                fetch_k=req.fetch_k or 10,
                query_variations_count=req.query_variations_count or 3,
                rrf_k=req.rrf_k or 60,
                rerank_top_n=req.rerank_top_n or 10,
                document_ids=req.document_ids,
                debug=req.debug
            )
            search_res = await self.execute_full_retrieval(search_req)
            pipeline_trace.extend(search_res.pipeline_trace)
            retrieved_documents = search_res.documents
            query_variations = search_res.query_variations
            fusion_results = [r.model_dump() for r in search_res.rrf_results]
            reranking_results = search_res.rerank_results

            # Convert to DocumentChunkModel for generation
            for doc in retrieved_documents[:context_k]:
                chunk_obj = db_service.get_chunk(doc.chunk_id)
                if chunk_obj:
                    context_chunks.append(chunk_obj)
        else:
            # Execute specified retrieval strategy
            search_req = SearchRequest(
                query=query,
                strategy=strategy,
                k=context_k,
                score_threshold=req.score_threshold,
                fetch_k=req.fetch_k,
                lambda_mult=req.lambda_mult,
                query_variations_count=req.query_variations_count,
                vector_weight=req.vector_weight,
                bm25_weight=req.bm25_weight,
                rrf_k=req.rrf_k,
                rerank_top_n=req.rerank_top_n,
                document_ids=req.document_ids,
                debug=req.debug
            )
            search_res = await retrieval_service.execute_search(search_req, run_id=run_id)
            pipeline_trace.extend(search_res.pipeline_trace)
            retrieved_documents = search_res.documents
            query_variations = search_res.query_variations
            if search_res.rrf_results:
                fusion_results = [r.model_dump() for r in search_res.rrf_results]
            elif search_res.hybrid_results:
                fusion_results = [h.model_dump() for h in search_res.hybrid_results]
            reranking_results = search_res.rerank_results

            for doc in retrieved_documents[:context_k]:
                chunk_obj = db_service.get_chunk(doc.chunk_id)
                if chunk_obj:
                    context_chunks.append(chunk_obj)

        # Stage: Answer generation via Gemini
        t_gen = time.perf_counter()
        answer, sources, token_usage = await generation_service.generate_answer(
            query=query,
            context_chunks=context_chunks,
            strategy=strategy,
            include_images=req.include_images
        )
        gen_duration_ms = (time.perf_counter() - t_gen) * 1000
        pipeline_trace.append(PipelineStageTrace(
            stage="generation",
            duration_ms=round(gen_duration_ms, 2),
            input_count=len(context_chunks),
            output_count=1,
            metadata={
                "model": self.settings.GEMINI_CHAT_MODEL,
                "token_usage": token_usage
            }
        ))

        total_duration_ms = (time.perf_counter() - start_overall) * 1000

        # Persist run history in SQLite
        db_service.record_run(
            run_id=run_id,
            query=query,
            strategy=strategy,
            duration_ms=round(total_duration_ms, 2),
            number_of_candidates=len(retrieved_documents),
            final_answer=answer,
            sources=[s.model_dump() for s in sources],
            trace=[t.model_dump() for t in pipeline_trace],
            debug={"token_usage": token_usage, "context_chunks_count": len(context_chunks)}
        )

        # Filter fields if debug=False
        if not req.debug:
            retrieved_documents = []
            query_variations = []
            fusion_results = []
            reranking_results = []

        return ChatResponse(
            run_id=run_id,
            query=query,
            answer=answer,
            sources=sources,
            retrieved_documents=retrieved_documents,
            query_variations=query_variations,
            fusion_results=fusion_results,
            reranking_results=reranking_results,
            pipeline_trace=pipeline_trace,
            strategy=strategy,
            total_duration_ms=round(total_duration_ms, 2),
            model_name=self.settings.GEMINI_CHAT_MODEL,
            token_usage=token_usage,
            debug_info={"debug_enabled": req.debug, "context_k": context_k} if req.debug else None
        )

pipeline_service = PipelineService()
