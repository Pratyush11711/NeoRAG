import logging
from fastapi import APIRouter, HTTPException
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services.pipeline_service import pipeline_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "EMPTY_QUERY", "message": "Query cannot be empty.", "stage": "chat"}}
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
                    "stage": "chat"
                }
            }
        )

    try:
        response = await pipeline_service.execute_chat(req)
        return response
    except Exception as e:
        logger.error(f"Chat generation error: {e}", exc_info=True)
        error_msg = str(e)
        code = "CHAT_GENERATION_ERROR"
        if "503" in error_msg or "unavailable" in error_msg.lower():
            code = "GEMINI_UNAVAILABLE"
            error_msg = "Gemini is temporarily unavailable."
        elif "api_key" in error_msg.lower() or "unauthenticated" in error_msg.lower():
            code = "INVALID_API_KEY"
            error_msg = "Google API key is missing or invalid."

        raise HTTPException(
            status_code=500,
            detail={"error": {"code": code, "message": error_msg, "stage": "generation"}}
        )
