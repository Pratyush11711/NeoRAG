import logging
import time
from typing import List, Tuple, Dict, Any, Optional
from app.models.requests import SearchRequest
from app.models.responses import (
    SearchResponse, RetrievedDocument, RRFContribution,
    HybridFusionResult, RerankResult, MMRMetadata, PipelineStageTrace
)
from app.services.vector_store import vector_store_service
from app.services.bm25_service import bm25_service
from app.services.mmr_service import mmr_service
from app.services.multi_query_service import multi_query_service
from app.services.hybrid_service import hybrid_service
from app.services.reranker_service import reranker_service
from app.services.db_service import db_service
from app.utils.ids import generate_run_id

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Central router and executor for all retrieval strategies:
    - similarity
    - similarity_threshold
    - mmr
    - multi_query
    - multi_query_rrf
    - bm25
    - hybrid
    - hybrid_rrf
    - hybrid_rerank
    - full_pipeline
    """

    async def execute_search(self, req: SearchRequest, run_id: Optional[str] = None) -> SearchResponse:
        active_run_id = run_id or generate_run_id()
        start_overall = time.perf_counter()

        pipeline_trace: List[PipelineStageTrace] = []
        documents: List[RetrievedDocument] = []
        query_variations: List[str] = []
        rrf_results: List[RRFContribution] = []
        hybrid_results: List[HybridFusionResult] = []
        rerank_results: List[RerankResult] = []
        mmr_meta: Optional[MMRMetadata] = None

        strategy = req.strategy.lower().strip()
        k = req.k

        filter_dict = {"document_id": {"$in": req.document_ids}} if req.document_ids else None

        # 1. Similarity Search
        if strategy == "similarity":
            t0 = time.perf_counter()
            candidates = vector_store_service.similarity_search_with_scores(
                query=req.query,
                k=k,
                filter_dict=filter_dict
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="vector_retrieval",
                duration_ms=round(d_ms, 2),
                input_count=1,
                output_count=len(candidates),
                metadata={"strategy": "similarity", "k": k}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 2. Similarity Threshold
        elif strategy == "similarity_threshold":
            t0 = time.perf_counter()
            threshold = req.score_threshold if req.score_threshold is not None else 0.5
            accepted, discarded = vector_store_service.similarity_threshold_search(
                query=req.query,
                k=k,
                score_threshold=threshold,
                filter_dict=filter_dict
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="vector_retrieval",
                duration_ms=round(d_ms, 2),
                input_count=1,
                output_count=len(accepted),
                metadata={"score_threshold": threshold, "discarded_count": len(discarded)}
            ))
            documents = self._to_retrieved_documents(accepted)

        # 3. Maximum Marginal Relevance (MMR)
        elif strategy == "mmr":
            t0 = time.perf_counter()
            fetch_k = req.fetch_k or 10
            lambda_mult = req.lambda_mult if req.lambda_mult is not None else 0.5
            candidates, mmr_meta, pool = mmr_service.search(
                query=req.query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="mmr_selection",
                duration_ms=round(d_ms, 2),
                input_count=len(pool),
                output_count=len(candidates),
                metadata={"candidate_pool_size": mmr_meta.candidate_pool_size, "lambda_mult": lambda_mult}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 4. Multi-Query
        elif strategy == "multi_query":
            t0 = time.perf_counter()
            candidates, query_variations = await multi_query_service.search_multi_query(
                query=req.query,
                k=k,
                variations_count=req.query_variations_count or 3,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="multi_query_retrieval",
                duration_ms=round(d_ms, 2),
                input_count=1,
                output_count=len(candidates),
                metadata={"variations_count": len(query_variations), "variations": query_variations}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 5. Multi-Query + RRF
        elif strategy == "multi_query_rrf":
            t0 = time.perf_counter()
            candidates, query_variations, rrf_results = await multi_query_service.search_multi_query_rrf(
                query=req.query,
                k=k,
                variations_count=req.query_variations_count or 3,
                rrf_k=req.rrf_k or 60,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="multi_query_rrf_retrieval",
                duration_ms=round(d_ms, 2),
                input_count=len(query_variations) + 1,
                output_count=len(candidates),
                metadata={"rrf_k": req.rrf_k or 60, "variations_count": len(query_variations)}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 6. BM25 Keyword Search
        elif strategy == "bm25":
            t0 = time.perf_counter()
            candidates = bm25_service.search(
                query=req.query,
                k=k,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="bm25_retrieval",
                duration_ms=round(d_ms, 2),
                input_count=1,
                output_count=len(candidates),
                metadata={"k": k}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 7. Weighted Hybrid Search
        elif strategy == "hybrid":
            t0 = time.perf_counter()
            vec_w = req.vector_weight if req.vector_weight is not None else 0.7
            b_w = req.bm25_weight if req.bm25_weight is not None else 0.3
            candidates, hybrid_results = hybrid_service.weighted_hybrid_search(
                query=req.query,
                k=k,
                vector_weight=vec_w,
                bm25_weight=b_w,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="weighted_hybrid_fusion",
                duration_ms=round(d_ms, 2),
                input_count=len(hybrid_results),
                output_count=len(candidates),
                metadata={"vector_weight": vec_w, "bm25_weight": b_w}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 8. Hybrid + RRF
        elif strategy == "hybrid_rrf":
            t0 = time.perf_counter()
            candidates, rrf_results, hybrid_results = hybrid_service.rrf_hybrid_search(
                query=req.query,
                k=k,
                rrf_k=req.rrf_k or 60,
                document_ids=req.document_ids
            )
            d_ms = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="hybrid_rrf_fusion",
                duration_ms=round(d_ms, 2),
                input_count=len(rrf_results),
                output_count=len(candidates),
                metadata={"rrf_k": req.rrf_k or 60}
            ))
            documents = self._to_retrieved_documents(candidates)

        # 9. Hybrid + Rerank
        elif strategy == "hybrid_rerank":
            t0 = time.perf_counter()
            candidates, hybrid_results = hybrid_service.weighted_hybrid_search(
                query=req.query,
                k=req.rerank_top_n or 10,
                vector_weight=req.vector_weight or 0.7,
                bm25_weight=req.bm25_weight or 0.3,
                document_ids=req.document_ids
            )
            d_ms1 = (time.perf_counter() - t0) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="hybrid_retrieval",
                duration_ms=round(d_ms1, 2),
                input_count=len(hybrid_results),
                output_count=len(candidates)
            ))

            t1 = time.perf_counter()
            chunk_models = [c for c, _, _ in candidates]
            reranked_chunks, rerank_results = await reranker_service.rerank(
                query=req.query,
                candidates=chunk_models,
                top_n=k
            )
            d_ms2 = (time.perf_counter() - t1) * 1000
            pipeline_trace.append(PipelineStageTrace(
                stage="gemini_reranking",
                duration_ms=round(d_ms2, 2),
                input_count=len(chunk_models),
                output_count=len(reranked_chunks)
            ))

            reranked_tuples = [(c, None, idx + 1) for idx, c in enumerate(reranked_chunks[:k])]
            documents = self._to_retrieved_documents(reranked_tuples)

        # 10. Full Pipeline (as search)
        elif strategy == "full_pipeline":
            from app.services.pipeline_service import pipeline_service
            pipe_res = await pipeline_service.execute_full_retrieval(req)
            return pipe_res

        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")

        total_duration_ms = (time.perf_counter() - start_overall) * 1000

        try:
            db_service.save_run(
                run_id=active_run_id,
                query=req.query,
                strategy=strategy,
                duration_ms=round(total_duration_ms, 2),
                number_of_candidates=len(documents),
                final_answer="",
                sources=[doc.model_dump() for doc in documents],
                trace=[tr.model_dump() for tr in pipeline_trace],
                debug={"k": req.k, "document_ids": req.document_ids}
            )
        except Exception as e:
            logger.warning(f"Failed to record run telemetry for {active_run_id}: {e}")

        return SearchResponse(
            run_id=active_run_id,
            query=req.query,
            strategy=strategy,
            total_duration_ms=round(total_duration_ms, 2),
            documents=documents,
            query_variations=query_variations,
            rrf_results=rrf_results,
            hybrid_results=hybrid_results,
            rerank_results=rerank_results,
            mmr_meta=mmr_meta,
            pipeline_trace=pipeline_trace
        )

    def _to_retrieved_documents(self, items: List[Tuple[Any, Optional[float], int]]) -> List[RetrievedDocument]:
        docs: List[RetrievedDocument] = []
        for chunk, score, rank in items:
            source = str(chunk.metadata.get("source", chunk.document_id))
            page = chunk.metadata.get("page_number")
            docs.append(RetrievedDocument(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.page_content,
                raw_text=chunk.raw_text,
                source=source,
                page=page,
                rank=rank,
                score=score,
                tables=chunk.tables,
                images=chunk.images,
                content_types=chunk.content_types,
                metadata=chunk.metadata
            ))
        return docs

retrieval_service = RetrievalService()
