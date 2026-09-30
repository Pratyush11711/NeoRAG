import logging
import asyncio
from typing import List, Optional
from app.core.config import get_settings
from app.models.responses import DocumentChunkModel

logger = logging.getLogger(__name__)

class MultimodalProcessor:
    """
    Enhances chunks containing tables or images with rich searchable Gemini descriptions.
    Preserves original raw_text while augmenting page_content.
    """

    def __init__(self):
        self.settings = get_settings()

    async def enhance_chunks(
        self,
        chunks: List[DocumentChunkModel],
        enable_summary: Optional[bool] = None
    ) -> List[DocumentChunkModel]:
        should_enhance = enable_summary if enable_summary is not None else self.settings.ENABLE_MULTIMODAL_SUMMARY
        
        if not should_enhance:
            logger.info("Multimodal summary enhancement is disabled via config.")
            return chunks

        if not self.settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set. Skipping multimodal summary generation.")
            return chunks

        enhanced_count = 0
        for chunk in chunks:
            # Check if chunk contains tables or images
            if chunk.tables or chunk.images:
                try:
                    summary = await self._generate_gemini_summary(chunk)
                    if summary:
                        chunk.metadata["enhanced_summary"] = summary
                        # Searchable representation combines original text + enhanced summary
                        table_context = ""
                        for idx, t in enumerate(chunk.tables):
                            table_context += f"\n[Table {idx+1} HTML]:\n{t.html}"
                        
                        chunk.page_content = (
                            f"{chunk.raw_text}\n\n"
                            f"{table_context}\n\n"
                            f"[Multimodal Analysis & Searchable Summary]:\n{summary}"
                        )
                        enhanced_count += 1
                except Exception as e:
                    logger.error(f"Failed to enhance chunk {chunk.chunk_id}: {e}")
                    # Retain raw text as page_content
                    chunk.page_content = chunk.raw_text

        logger.info(f"Enhanced {enhanced_count} multimodal chunks with Gemini summaries.")
        return chunks

    async def _generate_gemini_summary(self, chunk: DocumentChunkModel) -> Optional[str]:
        """
        Calls Gemini to create a dense factual description of tables and images.
        """
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model=self.settings.GEMINI_CHAT_MODEL,
            google_api_key=self.settings.GOOGLE_API_KEY,
            temperature=0.2,
            max_retries=self.settings.GEMINI_MAX_RETRIES
        )

        content_parts = []
        
        prompt_text = (
            "You are an expert technical document analyst. Analyze this document chunk containing multimodal elements.\n"
            "Generate a highly detailed, searchable factual summary covering:\n"
            "1. Important facts, numbers, metrics, and relationships.\n"
            "2. Table contents, headers, rows, and key insights.\n"
            "3. Diagram/image structures, flows, visual components, and meanings.\n"
            "4. Domain-specific terminology, synonyms, and alternative search keywords.\n\n"
            f"Chunk Text:\n{chunk.raw_text}\n\n"
        )

        for idx, table in enumerate(chunk.tables):
            prompt_text += f"Table {idx+1} (HTML):\n{table.html}\n\n"

        content_parts.append({"type": "text", "text": prompt_text})

        # Append images if available (base64)
        for idx, img in enumerate(chunk.images):
            if img.base64:
                # Prepare data url or base64 format for Gemini
                b64_data = img.base64
                if "," in b64_data:
                    b64_data = b64_data.split(",")[1]
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{img.mime_type};base64,{b64_data}"}
                })

        message = HumanMessage(content=content_parts)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: llm.invoke([message]))
        return response.content if hasattr(response, "content") else str(response)

multimodal_processor = MultimodalProcessor()
