import os
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.models.requests import IngestRequest
from app.models.responses import (
    UploadResponse, IngestResponse, DocumentInfo, DocumentListResponse,
    DocumentChunkModel
)
from app.utils.ids import generate_document_id
from app.services.db_service import db_service
from app.services.document_parser import document_parser
from app.services.chunker import chunker_service
from app.services.multimodal_processor import multimodal_processor
from app.services.vector_store import vector_store_service
from app.services.bm25_service import bm25_service

from app.core.security import sanitize_filename, safe_join, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    settings = get_settings()
    raw_filename = file.filename or "uploaded_document.pdf"
    filename = sanitize_filename(raw_filename)
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE_TYPE", "message": f"Only PDF, TXT, or MD documents are supported. Received '{ext}'", "stage": "upload"}}
        )

    document_id = generate_document_id(filename)
    dest_path = safe_join(settings.UPLOADS_DIRECTORY, f"{document_id}_{filename}")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    try:
        total_size = 0
        with open(dest_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks to check size
                total_size += len(chunk)
                if total_size > max_bytes:
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(
                        status_code=413,
                        detail={"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.", "stage": "upload"}}
                    )
                buffer.write(chunk)
        file_size = total_size
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "UPLOAD_FAILED", "message": f"Could not save file: {str(e)}", "stage": "upload"}}
        )

    # Record in SQLite
    db_service.insert_document(
        document_id=document_id,
        filename=filename,
        file_path=dest_path,
        metadata={"file_size_bytes": file_size, "original_filename": filename}
    )

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        file_size_bytes=file_size,
        status="uploaded",
        message="Document uploaded successfully. Ready for ingestion."
    )

def get_media_type(filename: str) -> str:
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return "application/pdf"
    elif fn.endswith(".md"):
        return "text/markdown; charset=utf-8"
    elif fn.endswith(".txt"):
        return "text/plain; charset=utf-8"
    elif fn.endswith(".png"):
        return "image/png"
    elif fn.endswith(".jpg") or fn.endswith(".jpeg"):
        return "image/jpeg"
    return "application/octet-stream"

def resolve_document_file_path(doc_info: DocumentInfo) -> Optional[str]:
    # 1. Direct file_path property
    if getattr(doc_info, "file_path", None) and os.path.exists(doc_info.file_path):
        return doc_info.file_path

    # 2. In metadata
    if doc_info.metadata and doc_info.metadata.get("file_path"):
        p = doc_info.metadata["file_path"]
        if os.path.exists(p):
            return p

    # 3. Direct DB lookup
    db_path = db_service.get_document_file_path(doc_info.document_id)
    if db_path and os.path.exists(db_path):
        return db_path

    # 4. Standard uploads directory path
    settings = get_settings()
    dest = os.path.join(settings.UPLOADS_DIRECTORY, f"{doc_info.document_id}_{doc_info.filename}")
    if os.path.exists(dest):
        return dest

    # 5. Search in uploads directory for matching document_id or filename
    if os.path.exists(settings.UPLOADS_DIRECTORY):
        for f in os.listdir(settings.UPLOADS_DIRECTORY):
            if f.startswith(doc_info.document_id) or f.endswith(doc_info.filename):
                candidate = os.path.join(settings.UPLOADS_DIRECTORY, f)
                if os.path.isfile(candidate):
                    return candidate

    # 6. Search in docs directories (for sample files like attention-is-all-you-need.pdf)
    search_dirs = [
        settings.DOCS_DIRECTORY,
        os.path.join(os.path.dirname(settings.DOCS_DIRECTORY), "docs"),
        os.path.join(os.path.dirname(settings.DOCS_DIRECTORY), "backend", "docs")
    ]
    for d in search_dirs:
        candidate = os.path.join(d, doc_info.filename)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return candidate

    return None

@router.post("/{document_id}/ingest", response_model=IngestResponse)
async def ingest_document(document_id: str, req: IngestRequest = IngestRequest()):
    doc_info = db_service.get_document(document_id)
    if not doc_info:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "ingestion"}}
        )

    # Check if already ingested and not force_reprocess
    if doc_info.status == "ingested" and not req.force_reprocess:
        return IngestResponse(
            document_id=document_id,
            status="ingested",
            chunk_count=doc_info.chunk_count,
            element_count=doc_info.element_count,
            tables_count=doc_info.tables_count,
            images_count=doc_info.images_count,
            message="Document already ingested. Use force_reprocess=true to re-ingest."
        )

    file_path = resolve_document_file_path(doc_info)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": f"File on disk for document '{document_id}' not found.", "stage": "ingestion"}}
        )

    try:
        db_service.update_document_status(document_id, status="ingesting")

        # 1. Partitioning (supports PDF, TXT, MD)
        logger.info(f"Starting partitioning for {document_id} from {file_path}")
        if doc_info.filename.lower().endswith(".pdf"):
            raw_elements = document_parser.parse_pdf(file_path)
            parsed_elements = document_parser.extract_structured_elements(raw_elements)
        else:
            raw_elements = []
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            from app.services.document_parser import ParsedElement
            sections = [s.strip() for s in content.split("\n\n") if s.strip()]
            parsed_elements = [
                ParsedElement(
                    element_id=f"{document_id}_el_{i}",
                    category="Title" if (len(s.split("\n")[0]) < 80 and s.startswith("#")) else "NarrativeText",
                    text=s,
                    metadata={"page_number": 1}
                )
                for i, s in enumerate(sections)
            ] or [
                ParsedElement(
                    element_id=f"{document_id}_el_0",
                    category="NarrativeText",
                    text=content,
                    metadata={"page_number": 1}
                )
            ]

        # 2. Title-based chunking
        logger.info(f"Starting title-based chunking for {document_id}")
        chunks = chunker_service.chunk_elements(
            document_id=document_id,
            filename=doc_info.filename,
            raw_elements=raw_elements if raw_elements else None,
            parsed_elements=parsed_elements,
            max_characters=req.max_characters,
            new_after_n_chars=req.new_after_n_chars,
            combine_text_under_n_chars=req.combine_text_under_n_chars
        )

        # 3. Multimodal enhancement
        logger.info(f"Starting multimodal summary enhancement for {document_id}")
        enhanced_chunks = await multimodal_processor.enhance_chunks(
            chunks=chunks,
            enable_summary=req.enable_multimodal_summary
        )

        # 4. Count tables & images
        total_tables = sum(len(c.tables) for c in enhanced_chunks)
        total_images = sum(len(c.images) for c in enhanced_chunks)

        # 5. Persist chunks in SQLite
        db_service.insert_chunks(enhanced_chunks)

        # 6. Add to ChromaDB vector store
        vector_store_service.add_chunks(enhanced_chunks)

        # 7. Update BM25 index
        all_chunks = db_service.get_all_chunks()
        bm25_service.index_chunks(all_chunks)

        # 8. Update Document record
        db_service.update_document_status(
            document_id=document_id,
            status="ingested",
            element_count=len(parsed_elements),
            chunk_count=len(enhanced_chunks),
            tables_count=total_tables,
            images_count=total_images
        )

        return IngestResponse(
            document_id=document_id,
            status="ingested",
            chunk_count=len(enhanced_chunks),
            element_count=len(parsed_elements),
            tables_count=total_tables,
            images_count=total_images,
            message="Document ingestion, multimodal extraction, and vector indexing completed successfully."
        )

    except Exception as e:
        logger.error(f"Ingestion failed for {document_id}: {e}", exc_info=True)
        db_service.update_document_status(document_id, status="failed")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INGESTION_ERROR", "message": str(e), "stage": "ingestion"}}
        )

@router.get("", response_model=DocumentListResponse)
def list_documents():
    docs = db_service.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))

@router.get("/reference/{filename}")
async def get_reference_document(filename: str, download: bool = False):
    """
    Directly views or downloads reference files such as 'attention-is-all-you-need.pdf'
    from docs/ or uploads directories with path traversal protection.
    """
    settings = get_settings()
    clean_filename = sanitize_filename(filename)
    search_dirs = [
        settings.DOCS_DIRECTORY,
        os.path.join(os.path.dirname(settings.DOCS_DIRECTORY), "docs"),
        os.path.join(os.path.dirname(settings.DOCS_DIRECTORY), "backend", "docs"),
        settings.UPLOADS_DIRECTORY
    ]
    found_path = None
    for d in search_dirs:
        try:
            candidate = safe_join(d, clean_filename)
            if os.path.exists(candidate) and os.path.isfile(candidate):
                found_path = candidate
                break
        except HTTPException:
            continue
        # Also check with prefix in uploads
        if os.path.exists(d):
            try:
                for item in os.listdir(d):
                    if item.endswith(clean_filename):
                        c = safe_join(d, item)
                        if os.path.isfile(c):
                            found_path = c
                            break
            except Exception:
                pass
        if found_path:
            break

    if not found_path:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "REFERENCE_DOC_NOT_FOUND", "message": f"Reference document '{clean_filename}' not found.", "stage": "reference_lookup"}}
        )

    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=found_path,
        media_type=get_media_type(filename),
        filename=filename,
        content_disposition_type=disposition
    )

@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    Downloads the original document file as an attachment.
    """
    doc_info = db_service.get_document(document_id)
    if not doc_info:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "download"}}
        )
    file_path = resolve_document_file_path(doc_info)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": f"File on disk for '{doc_info.filename}' not found.", "stage": "download"}}
        )

    return FileResponse(
        path=file_path,
        media_type=get_media_type(doc_info.filename),
        filename=doc_info.filename,
        content_disposition_type="attachment"
    )

@router.get("/{document_id}/view")
async def view_document(document_id: str):
    """
    Renders/streams the document inline for browser preview or iframe display.
    """
    doc_info = db_service.get_document(document_id)
    if not doc_info:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "view"}}
        )
    file_path = resolve_document_file_path(doc_info)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": f"File on disk for '{doc_info.filename}' not found.", "stage": "view"}}
        )

    return FileResponse(
        path=file_path,
        media_type=get_media_type(doc_info.filename),
        filename=doc_info.filename,
        content_disposition_type="inline"
    )

@router.get("/{document_id}/content")
async def get_document_raw_content(document_id: str):
    """
    Returns text content preview for text/markdown files or chunks summary.
    """
    doc_info = db_service.get_document(document_id)
    if not doc_info:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "content"}}
        )
    file_path = resolve_document_file_path(doc_info)
    is_text = not doc_info.filename.lower().endswith(".pdf")
    content = ""
    if file_path and os.path.exists(file_path) and is_text:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            content = ""

    chunks = db_service.get_chunks_for_document(document_id)
    return {
        "document_id": document_id,
        "filename": doc_info.filename,
        "is_text": is_text,
        "content": content,
        "chunk_count": len(chunks),
        "chunks": chunks
    }

@router.get("/{document_id}")
def get_document_details(document_id: str):
    doc = db_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "document_lookup"}}
        )
    chunks = db_service.get_chunks_for_document(document_id)
    return {
        "document": doc,
        "chunks": chunks
    }

@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc = db_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": f"Document '{document_id}' not found.", "stage": "delete"}}
        )
    # Remove from Chroma
    vector_store_service.delete_document(document_id)
    # Remove from SQLite
    db_service.delete_document(document_id)
    # Rebuild BM25 index with remaining chunks
    bm25_service.index_chunks(db_service.get_all_chunks())

    return {"status": "deleted", "document_id": document_id}

@router.post("/load-sample")
async def load_sample_documents():
    """
    Automatically copies sample documents (attention-is-all-you-need.pdf, cheatsheet, guide)
    and runs ingestion so users can test immediately without uploading.
    """
    settings = get_settings()
    sample_files = [
        "attention-is-all-you-need.pdf",
        "transformer_architecture_cheatsheet.txt",
        "multimodal_rag_system_guide.md"
    ]
    
    loaded = []
    
    # Check both docs directories
    search_dirs = [settings.DOCS_DIRECTORY, os.path.join(os.path.dirname(settings.DOCS_DIRECTORY), "docs")]
    
    for filename in sample_files:
        src = None
        for d in search_dirs:
            candidate = os.path.join(d, filename)
            if os.path.exists(candidate):
                src = candidate
                break
        
        if not src:
            continue
            
        doc_id = f"sample_{filename.replace('.', '_')}"
        dest = os.path.join(settings.UPLOADS_DIRECTORY, f"{doc_id}_{filename}")
        shutil.copyfile(src, dest)
        file_size = os.path.getsize(dest)
        
        db_service.insert_document(
            document_id=doc_id,
            filename=filename,
            file_path=dest,
            metadata={"file_size_bytes": file_size, "is_sample": True}
        )
        
        # Ingest document
        try:
            raw_elements = document_parser.parse_pdf(dest) if filename.endswith(".pdf") else []
            if not raw_elements:
                with open(dest, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                from app.services.document_parser import ParsedElement
                parsed_elements = [ParsedElement(
                    element_id=f"{doc_id}_el_0",
                    category="NarrativeText",
                    text=content,
                    metadata={"page_number": 1}
                )]
            else:
                parsed_elements = document_parser.extract_structured_elements(raw_elements)
                
            chunks = chunker_service.chunk_elements(
                document_id=doc_id,
                filename=filename,
                raw_elements=raw_elements if raw_elements else None,
                parsed_elements=parsed_elements
            )
            
            enhanced_chunks = await multimodal_processor.enhance_chunks(chunks)
            total_tables = sum(len(c.tables) for c in enhanced_chunks)
            total_images = sum(len(c.images) for c in enhanced_chunks)
            
            db_service.insert_chunks(enhanced_chunks)
            vector_store_service.add_chunks(enhanced_chunks)
            
            db_service.update_document_status(
                document_id=doc_id,
                status="ingested",
                element_count=len(parsed_elements),
                chunk_count=len(enhanced_chunks),
                tables_count=total_tables,
                images_count=total_images
            )
            loaded.append({"filename": filename, "chunks": len(enhanced_chunks)})
        except Exception as e:
            logger.error(f"Error loading sample file {filename}: {e}")
            
    # Refresh BM25
    bm25_service.index_chunks(db_service.get_all_chunks())
    
    return {
        "status": "success",
        "message": f"Loaded {len(loaded)} sample document(s) successfully!",
        "loaded_documents": loaded,
        "total_chunks": len(db_service.get_all_chunks())
    }

