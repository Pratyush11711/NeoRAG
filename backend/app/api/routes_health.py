from fastapi import APIRouter
from app.core.config import get_settings
from app.models.responses import HealthResponse
from app.services.db_service import db_service
from app.services.vector_store import vector_store_service

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    settings = get_settings()
    docs = db_service.list_documents()
    stats = vector_store_service.get_stats()
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        gemini_chat_model=settings.GEMINI_CHAT_MODEL,
        gemini_embedding_model=settings.GEMINI_EMBEDDING_MODEL,
        chroma_collection=settings.CHROMA_COLLECTION_NAME,
        total_documents=len(docs),
        total_chunks=stats.get("total_chunks", 0),
        security={
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "requests_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            "api_key_required": bool(settings.API_KEY.strip()) if settings.API_KEY else False,
            "allowed_file_types": [".pdf", ".txt", ".md"],
            "security_headers": True,
            "path_traversal_protection": True
        }
    )
