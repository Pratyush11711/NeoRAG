import os
import re
import time
import secrets
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import get_settings

logger = logging.getLogger("rag_security")

# Define allowed extensions and MIME types
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/octet-stream"  # Some browsers send octet-stream for .md / .txt
}

# API Key header definition for OpenAPI docs
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize untrusted filename to prevent path traversal, null byte injections,
    or dangerous filesystem characters.
    """
    if not filename:
        return "uploaded_document.pdf"

    # Strip any directory components (/ or \)
    base = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes and control chars
    base = re.sub(r"[\x00-\x1f\x7f]", "", base)
    # Remove relative path traversal dots
    base = re.sub(r"^\.+", "", base)
    # Replace unsafe characters with underscore (keep letters, numbers, dots, dashes, underscores)
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    # Limit length
    if len(base) > 200:
        name, ext = os.path.splitext(base)
        base = name[: 200 - len(ext)] + ext

    return base or "document.pdf"


def safe_join(base_directory: str, *paths: str) -> str:
    """
    Safely joins path components ensuring the target remains strictly
    within base_directory, guarding against path traversal attacks.
    """
    resolved_base = os.path.abspath(base_directory)
    # Sanitize each component
    cleaned_paths = [re.sub(r"\.\.+[\\/]", "", p) for p in paths]
    resolved_target = os.path.abspath(os.path.join(resolved_base, *cleaned_paths))

    try:
        common = os.path.commonpath([resolved_base, resolved_target])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "PATH_TRAVERSAL_DETECTED", "message": "Invalid file path traversal.", "stage": "security"}}
        )

    if common != resolved_base:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "PATH_TRAVERSAL_DETECTED", "message": "Attempted path traversal outside allowed directory.", "stage": "security"}}
        )

    return resolved_target


async def verify_api_key(request: Request) -> Optional[str]:
    """
    Dependency to verify API Key.
    If settings.API_KEY is configured, checks X-API-Key or Bearer token.
    If settings.API_KEY is empty, passes through (local development mode).
    """
    settings = get_settings()
    configured_key = (settings.API_KEY or "").strip()
    if not configured_key:
        return None  # Open access mode

    # Check X-API-Key header
    provided_key = request.headers.get("X-API-Key")
    # Also support Authorization: Bearer <key>
    if not provided_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()

    if not provided_key or not secrets.compare_digest(provided_key, configured_key):
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Missing or invalid API key.", "stage": "authentication"}},
            headers={"WWW-Authenticate": "Bearer"}
        )

    return provided_key


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies production security headers to all responses.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        # Prevent caching sensitive API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window in-memory rate limiter per IP address to protect against DoS,
    LLM quota exhaustion, and aggressive automated scraping.
    """
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Dict mapping IP -> list of timestamp floats
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.last_cleanup = time.time()

    def _cleanup_old_records(self, now: float):
        # Run cleanup every 2 minutes
        if now - self.last_cleanup > 120:
            threshold = now - 60
            stale_ips = []
            for ip, timestamps in self.requests.items():
                self.requests[ip] = [t for t in timestamps if t > threshold]
                if not self.requests[ip]:
                    stale_ips.append(ip)
            for ip in stale_ips:
                del self.requests[ip]
            self.last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED or request.url.path == "/health":
            return await call_next(request)

        # Get client IP (support X-Forwarded-For if behind a proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        self._cleanup_old_records(now)

        window_start = now - 60
        timestamps = self.requests[client_ip]
        # Keep only timestamps in current window
        valid_timestamps = [t for t in timestamps if t > window_start]
        self.requests[client_ip] = valid_timestamps

        # Strict limit for heavy endpoints (chat generation & file upload)
        limit = self.requests_per_minute
        path = request.url.path
        if path.startswith("/api/chat"):
            limit = min(limit, 40)
        elif path.endswith("/upload"):
            limit = min(limit, 20)

        if len(valid_timestamps) >= limit:
            retry_after = int(60 - (now - valid_timestamps[0])) + 1
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}. Retry after {retry_after}s")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Please retry in {retry_after} seconds.",
                        "stage": "security"
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        remaining = max(0, limit - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
