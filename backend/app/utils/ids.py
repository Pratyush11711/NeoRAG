import uuid
import re

def sanitize_filename(filename: str) -> str:
    """Removes special characters and spaces from filenames."""
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return clean

def generate_document_id(filename: str) -> str:
    """Generates a stable, recognizable document ID based on sanitized name + short hash."""
    clean = sanitize_filename(filename)
    short_hash = uuid.uuid4().hex[:8]
    return f"doc_{clean}_{short_hash}"

def generate_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generates a structured, deterministic chunk ID for a document."""
    return f"{document_id}_chunk_{chunk_index:04d}"

def generate_run_id() -> str:
    """Generates a unique request/run ID for pipeline tracing."""
    return f"run_{uuid.uuid4().hex[:12]}"
