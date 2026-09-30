import logging
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.utils.ids import generate_chunk_id
from app.models.responses import DocumentChunkModel, TableContent, ImageContent
from app.services.document_parser import ParsedElement

logger = logging.getLogger(__name__)

class ChunkerService:
    """
    Implements title-based chunking preserving text, tables, images, and metadata.
    """

    def __init__(self):
        self.settings = get_settings()

    def chunk_elements(
        self,
        document_id: str,
        filename: str,
        raw_elements: Optional[List[Any]] = None,
        parsed_elements: Optional[List[ParsedElement]] = None,
        max_characters: Optional[int] = None,
        new_after_n_chars: Optional[int] = None,
        combine_text_under_n_chars: Optional[int] = None
    ) -> List[DocumentChunkModel]:
        """
        Chunks elements using Unstructured's chunk_by_title when raw elements are available,
        or title-boundary grouping on ParsedElements.
        """
        max_chars = max_characters or self.settings.CHUNK_MAX_CHARACTERS
        new_after = new_after_n_chars or self.settings.CHUNK_NEW_AFTER_N_CHARS
        combine_under = combine_text_under_n_chars or self.settings.CHUNK_COMBINE_UNDER_N_CHARS

        chunks: List[DocumentChunkModel] = []

        # Attempt unstructured chunk_by_title first if raw elements present
        if raw_elements:
            try:
                from unstructured.chunking.title import chunk_by_title
                logger.info(f"Running chunk_by_title on {len(raw_elements)} raw elements (max_chars={max_chars}, new_after={new_after})")
                composite_elements = chunk_by_title(
                    raw_elements,
                    max_characters=max_chars,
                    new_after_n_chars=new_after,
                    combine_text_under_n_chars=combine_under
                )
                logger.info(f"Generated {len(composite_elements)} composite chunks using chunk_by_title.")
                return self._composite_to_chunks(document_id, filename, composite_elements)
            except Exception as e:
                logger.warning(f"chunk_by_title failed with: {e}. Using title-based fallback algorithm.")

        # Fallback to structured title-based chunking on parsed elements
        if parsed_elements:
            return self._custom_title_chunking(
                document_id=document_id,
                filename=filename,
                elements=parsed_elements,
                max_chars=max_chars,
                new_after=new_after,
                combine_under=combine_under
            )

        return chunks

    def _composite_to_chunks(
        self,
        document_id: str,
        filename: str,
        composite_elements: List[Any]
    ) -> List[DocumentChunkModel]:
        chunks: List[DocumentChunkModel] = []

        for idx, comp in enumerate(composite_elements):
            chunk_id = generate_chunk_id(document_id, idx + 1)
            raw_text = str(comp.text) if hasattr(comp, "text") and comp.text else str(comp)
            meta = comp.metadata.to_dict() if hasattr(comp, "metadata") and hasattr(comp.metadata, "to_dict") else {}
            
            page_number = meta.get("page_number")
            tables: List[TableContent] = []
            images: List[ImageContent] = []
            content_types = ["text"]

            # Inspect orig_elements if available
            orig_elements = getattr(comp.metadata, "orig_elements", []) or []
            
            # Check main element for table
            if meta.get("text_as_html"):
                tables.append(TableContent(
                    table_id=f"{chunk_id}_tbl_0",
                    html=meta["text_as_html"],
                    text=raw_text,
                    page_number=page_number
                ))
                content_types.append("table")

            # Check orig_elements for tables and images
            for o_idx, o_el in enumerate(orig_elements):
                o_category = getattr(o_el, "category", type(o_el).__name__)
                o_meta = o_el.metadata.to_dict() if hasattr(o_el, "metadata") and hasattr(o_el.metadata, "to_dict") else {}
                
                # Check for table in sub-element
                if o_category.lower() == "table" or "table" in type(o_el).__name__.lower():
                    t_html = o_meta.get("text_as_html") or (f"<table><tr><td>{o_el.text}</td></tr></table>" if hasattr(o_el, "text") else "")
                    t_id = f"{chunk_id}_tbl_{len(tables)}"
                    tables.append(TableContent(
                        table_id=t_id,
                        html=t_html,
                        text=str(getattr(o_el, "text", "")),
                        page_number=o_meta.get("page_number", page_number)
                    ))
                    if "table" not in content_types:
                        content_types.append("table")

                # Check for image
                if o_category.lower() == "image" or "image" in type(o_el).__name__.lower():
                    img_b64 = o_meta.get("image_base64")
                    if img_b64:
                        img_id = f"{chunk_id}_img_{len(images)}"
                        images.append(ImageContent(
                            image_id=img_id,
                            mime_type="image/jpeg",
                            base64=img_b64,
                            page_number=o_meta.get("page_number", page_number),
                            caption=str(getattr(o_el, "text", ""))
                        ))
                        if "image" not in content_types:
                            content_types.append("image")

            chunk_meta = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source": filename,
                "page_number": page_number,
                "content_types": content_types,
                "has_tables": len(tables) > 0,
                "has_images": len(images) > 0,
                "character_count": len(raw_text)
            }

            chunks.append(DocumentChunkModel(
                chunk_id=chunk_id,
                document_id=document_id,
                page_content=raw_text, # Will be updated with enhanced representation if enabled
                raw_text=raw_text,
                tables=tables,
                images=images,
                content_types=list(set(content_types)),
                metadata=chunk_meta
            ))

        return chunks

    def _custom_title_chunking(
        self,
        document_id: str,
        filename: str,
        elements: List[ParsedElement],
        max_chars: int,
        new_after: int,
        combine_under: int
    ) -> List[DocumentChunkModel]:
        """
        Title-boundary chunker fallback grouping parsed elements.
        """
        chunks: List[DocumentChunkModel] = []
        current_elements: List[ParsedElement] = []
        current_len = 0

        def flush_chunk():
            nonlocal current_elements, current_len
            if not current_elements:
                return
            idx = len(chunks) + 1
            chunk_id = generate_chunk_id(document_id, idx)
            combined_text = "\n\n".join(e.text for e in current_elements if e.text).strip()
            
            tables: List[TableContent] = []
            images: List[ImageContent] = []
            content_types = ["text"]
            pages = set()

            for e_idx, e in enumerate(current_elements):
                if e.metadata.get("page_number"):
                    pages.add(e.metadata["page_number"])
                if e.table_html:
                    tables.append(TableContent(
                        table_id=f"{chunk_id}_tbl_{len(tables)}",
                        html=e.table_html,
                        text=e.text,
                        page_number=e.metadata.get("page_number")
                    ))
                    if "table" not in content_types:
                        content_types.append("table")
                if e.image_base64:
                    images.append(ImageContent(
                        image_id=f"{chunk_id}_img_{len(images)}",
                        mime_type="image/jpeg",
                        base64=e.image_base64,
                        page_number=e.metadata.get("page_number"),
                        caption=e.text
                    ))
                    if "image" not in content_types:
                        content_types.append("image")

            page_number = min(pages) if pages else None
            chunk_meta = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source": filename,
                "page_number": page_number,
                "content_types": list(set(content_types)),
                "has_tables": len(tables) > 0,
                "has_images": len(images) > 0,
                "character_count": len(combined_text)
            }

            chunks.append(DocumentChunkModel(
                chunk_id=chunk_id,
                document_id=document_id,
                page_content=combined_text,
                raw_text=combined_text,
                tables=tables,
                images=images,
                content_types=list(set(content_types)),
                metadata=chunk_meta
            ))
            current_elements = []
            current_len = 0

        for el in elements:
            el_len = len(el.text)
            is_title = el.category.lower() in ["title", "header", "headline"]

            # If element is a Title and current length exceeds new_after_n_chars, start new chunk
            if is_title and current_len >= new_after:
                flush_chunk()
            # If adding this element exceeds max_chars, flush
            elif (current_len + el_len) > max_chars and current_len > combine_under:
                flush_chunk()

            current_elements.append(el)
            current_len += el_len

        flush_chunk()
        return chunks

chunker_service = ChunkerService()
