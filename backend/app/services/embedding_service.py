import logging
from typing import List, Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Manages Gemini embeddings via LangChain's GoogleGenerativeAIEmbeddings.
    Ensures identical model configuration across ingestion and retrieval.
    """

    def __init__(self):
        self.settings = get_settings()
        self._embeddings_instance = None

    def get_embeddings(self):
        """
        Returns cached GoogleGenerativeAIEmbeddings instance.
        """
        if self._embeddings_instance is not None:
            return self._embeddings_instance

        api_key = self.settings.GOOGLE_API_KEY
        model_name = self.settings.GEMINI_EMBEDDING_MODEL

        # Ensure correct model name format (e.g. "models/text-embedding-004" or "models/embedding-001")
        if not model_name.startswith("models/") and "/" not in model_name:
            # Langchain Google GenAI typically expects "models/<model_name>"
            formatted_model = f"models/{model_name}"
        else:
            formatted_model = model_name

        if not api_key:
            logger.warning("GOOGLE_API_KEY is not set. Generating fallback pseudo-embeddings for offline testing.")
            from langchain_core.embeddings import Embeddings
            class FakeEmbeddings(Embeddings):
                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    return [[float(len(t) % 10) * 0.1] * 768 for t in texts]
                def embed_query(self, text: str) -> List[float]:
                    return [float(len(text) % 10) * 0.1] * 768
            self._embeddings_instance = FakeEmbeddings()
            return self._embeddings_instance

        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            logger.info(f"Initializing GoogleGenerativeAIEmbeddings with model: {formatted_model}")
            self._embeddings_instance = GoogleGenerativeAIEmbeddings(
                model=formatted_model,
                google_api_key=api_key,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            return self._embeddings_instance
        except Exception as e:
            logger.error(f"Error initializing GoogleGenerativeAIEmbeddings with {formatted_model}: {e}. Retrying without prefix...")
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            self._embeddings_instance = GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=api_key,
                output_dimensionality=768
            )
            return self._embeddings_instance

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        embeddings = self.get_embeddings()
        return embeddings.embed_query(query)

embedding_service = EmbeddingService()
