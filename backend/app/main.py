import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router
from app.api.routes_retrieval import router as retrieval_router
from app.api.routes_chat import router as chat_router
from app.services.db_service import db_service
from app.services.bm25_service import bm25_service

setup_logging()
logger = logging.getLogger("rag_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Multimodal RAG Backend...")
    # Initialize SQLite database schema
    db_service.init_db()
    # Pre-index existing chunks in BM25
    bm25_service.ensure_indexed()
    logger.info("Multimodal RAG Backend startup complete.")
    yield
    logger.info("Shutting down Multimodal RAG Backend.")

app = FastAPI(
    title="Multimodal RAG Backend",
    description=(
        "Production-grade backend for Multimodal RAG with Gemini, ChromaDB, BM25, "
        "Reciprocal Rank Fusion (RRF), MMR, Hybrid Search, and Gemini LLM Reranker. "
        "Exposes full intermediate pipeline telemetry for frontend visualization."
    ),
    version="1.0.0",
    lifespan=lifespan
)

from app.core.security import SecurityHeadersMiddleware, RateLimiterMiddleware, verify_api_key
from fastapi import Depends

# Security & CORS Setup
settings = get_settings()
allowed_origins_list = [
    origin.strip() 
    for origin in settings.ALLOWED_ORIGINS.split(",") 
    if origin.strip()
] or ["http://localhost:5173", "http://127.0.0.1:5173"]

# Middleware execution is reverse of addition order:
# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]
)

# 2. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Rate Limiter Middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimiterMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Custom Exception Handler to guarantee structured error format
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "stage": "api_request"
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "stage": "server"
            }
        }
    )

# Include Routers
app.include_router(health_router)
app.include_router(documents_router, dependencies=[Depends(verify_api_key)])
app.include_router(retrieval_router, dependencies=[Depends(verify_api_key)])
app.include_router(chat_router, dependencies=[Depends(verify_api_key)])

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
