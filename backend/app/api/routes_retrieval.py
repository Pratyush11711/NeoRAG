import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models.requests import SearchRequest
from app.models.responses import SearchResponse, RunHistoryResponse
from app.services.retrieval_service import retrieval_service
from app.services.db_service import db_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/retrieval", tags=["Retrieval"])

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "EMPTY_QUERY", "message": "Query string cannot be empty.", "stage": "retrieval"}}
        )

    valid_strategies = {
        "similarity", "similarity_threshold", "mmr", "multi_query",
        "multi_query_rrf", "bm25", "hybrid", "hybrid_rrf",
        "hybrid_rerank", "full_pipeline"
    }

    if req.strategy.lower().strip() not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_STRATEGY",
                    "message": f"Strategy '{req.strategy}' is invalid. Allowed: {sorted(list(valid_strategies))}",
                    "stage": "retrieval"
                }
            }
        )

    try:
        response = await retrieval_service.execute_search(req)
        return response
    except Exception as e:
        logger.error(f"Search execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RETRIEVAL_ERROR", "message": str(e), "stage": "retrieval"}}
        )

@router.get("/runs", response_model=RunHistoryResponse)
def get_run_history(limit: int = 50):
    runs = db_service.get_runs(limit=limit)
    return RunHistoryResponse(runs=runs, total=len(runs))

@router.get("/runs/{run_id}")
def get_run_details(run_id: str):
    detail = db_service.get_run_detail(run_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RUN_NOT_FOUND", "message": f"Run '{run_id}' not found.", "stage": "history"}}
        )
    return detail
