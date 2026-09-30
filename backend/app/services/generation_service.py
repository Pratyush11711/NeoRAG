import logging
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from app.core.config import get_settings
from app.models.responses import DocumentChunkModel, SourceCitation

logger = logging.getLogger(__name__)

class GenerationService:
    """
    Final answer generation service using Gemini with multimodal context
    (text, tables, and images) and exact source citation mapping.
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[DocumentChunkModel],
        strategy: str,
        include_images: bool = True
    ) -> Tuple[str, List[SourceCitation], Optional[Dict[str, int]]]:
        """
        Generates an evidence-grounded answer with source citations.
        """
        if not context_chunks:
            return (
                "No relevant documents were found in the knowledge base to answer your question.",
                [],
                None
            )

        # 1. Build source citations
        citations: List[SourceCitation] = []
        for rank, chunk in enumerate(context_chunks, start=1):
            source_file = str(chunk.metadata.get("source") or chunk.document_id)
            page_no = chunk.metadata.get("page_number")
            citations.append(SourceCitation(
                source_id=chunk.chunk_id,
                document=source_file,
                page=page_no,
                chunk_id=chunk.chunk_id,
                source_path=str(chunk.metadata.get("source_path", "")),
                retrieval_rank=chunk.metadata.get("retrieval_rank", rank),
                retrieval_method=strategy,
                reranker_rank=rank
            ))

        if not self.settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set. Generating mock synthesis from retrieved chunks.")
            preview_texts = [f"[{c.chunk_id}] {c.raw_text[:200]}..." for c in context_chunks[:3]]
            synthesis = (
                f"Synthesized response (Offline Mode):\nBased on the retrieved documents:\n"
                + "\n\n".join(preview_texts)
            )
            return synthesis, citations, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model=self.settings.GEMINI_CHAT_MODEL,
                google_api_key=self.settings.GOOGLE_API_KEY,
                temperature=0.2,
                max_retries=self.settings.GEMINI_MAX_RETRIES
            )

            # Build context presentation
            context_blocks = []
            image_parts = []

            for idx, chunk in enumerate(context_chunks, start=1):
                source_name = str(chunk.metadata.get("source") or chunk.document_id)
                page_num = chunk.metadata.get("page_number")
                page_info = f", Page {page_num}" if page_num else ""
                block = f"--- [Source {idx}]: {source_name}{page_info} (ID: {chunk.chunk_id}) ---\n"
                block += f"{chunk.page_content}\n"

                if chunk.tables:
                    for t_idx, tbl in enumerate(chunk.tables, start=1):
                        block += f"\n[Table {t_idx} HTML]:\n{tbl.html}\n"

                context_blocks.append(block)

                if include_images and chunk.images:
                    for img in chunk.images:
                        if img.base64:
                            b64_data = img.base64
                            if "," in b64_data:
                                b64_data = b64_data.split(",")[1]
                            image_parts.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:{img.mime_type};base64,{b64_data}"}
                            })

            full_context_text = "\n\n".join(context_blocks)

            system_instruction = (
                "You are an expert AI technical assistant providing clean, clear, well-structured, and authoritative answers grounded strictly in the provided documentation.\n\n"
                "CRITICAL FORMATTING & CITATION RULES:\n"
                "1. Clean Footnote Citations: Cite sources using concise numbered brackets corresponding to the source numbers: e.g. [1], [2], or [1, 2]. NEVER write raw chunk IDs, hash keys, or file paths in the text.\n"
                "2. Mathematical Formulas: Format math and formulas legibly using standard clean notation or code blocks (e.g. `Attention(Q, K, V) = softmax((Q · Kᵀ) / √d_k) · V`). Do NOT output verbose raw LaTeX commands like \\text{...}, \\left(, \\right), \\frac{...} when clean readable notation is clearer.\n"
                "3. Direct & Articulate: Do NOT start with robotic filler like 'Based on the provided documents...' or 'According to the context...'. Answer directly and naturally.\n"
                "4. Clean Markdown: Structure your answer with clear bold headings, clean bullet points (using standard '-' list items), and concise paragraphs. Avoid clutter and wall-of-text formatting.\n"
                "5. Strict Factuality: Base every claim solely on the provided context. If the answer cannot be determined, state: 'The provided documents do not contain sufficient information to answer this question.'"
            )

            user_prompt_text = (
                f"Question: {query}\n\n"
                f"Retrieved Context:\n{full_context_text}\n\n"
                f"Provide a clean, elegant, and well-structured answer with concise footnote citations [1], [2] referencing the source numbers."
            )

            message_contents = [{"type": "text", "text": user_prompt_text}]
            # Append images for multimodal reasoning
            message_contents.extend(image_parts[:4]) # Limit images to avoid exceeding payload

            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content=message_contents)
            ]

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: llm.invoke(messages))
            
            if hasattr(response, "content"):
                if isinstance(response.content, str):
                    answer_text = response.content
                elif isinstance(response.content, list):
                    texts = []
                    for item in response.content:
                        if isinstance(item, str):
                            texts.append(item)
                        elif isinstance(item, dict) and "text" in item:
                            texts.append(item["text"])
                    answer_text = "".join(texts) if texts else str(response.content)
                else:
                    answer_text = str(response.content)
            else:
                answer_text = str(response)
            
            # Extract token usage if available
            token_usage = None
            if hasattr(response, "response_metadata") and "usage_metadata" in response.response_metadata:
                usage = response.response_metadata["usage_metadata"]
                token_usage = {
                    "prompt_tokens": usage.get("prompt_token_count", 0),
                    "completion_tokens": usage.get("candidates_token_count", 0),
                    "total_tokens": usage.get("total_token_count", 0)
                }

            return answer_text, citations, token_usage

        except Exception as e:
            logger.error(f"Error generating answer via Gemini: {e}")
            raise e

generation_service = GenerationService()
