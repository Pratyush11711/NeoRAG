import logging
import os
from typing import List, Tuple, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.core.config import get_settings
from app.services.embedding_service import embedding_service
from app.models.responses import DocumentChunkModel
from app.services.db_service import db_service

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Manages persistent ChromaDB vector store for multimodal chunks.
    Supports similarity search, threshold search, and MMR.
    """

    def __init__(self):
        self.settings = get_settings()
        self._vector_store = None

    def get_vector_store(self) -> Chroma:
        if self._vector_store is not None:
            return self._vector_store

        embeddings = embedding_service.get_embeddings()
        persist_dir = self.settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(persist_dir, exist_ok=True)

        logger.info(f"Connecting to ChromaDB at: {persist_dir} (collection: {self.settings.CHROMA_COLLECTION_NAME})")
        self._vector_store = Chroma(
            collection_name=self.settings.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        return self._vector_store

    def add_chunks(self, chunks: List[DocumentChunkModel]) -> None:
        """
        Embeds and stores document chunks in ChromaDB.
        Uses enhanced page_content for embedding while attaching chunk metadata.
        """
        if not chunks:
            return

        vector_store = self.get_vector_store()
        documents: List[Document] = []
        ids: List[str] = []

        for c in chunks:
            # Flatten metadata for Chroma compatibility (primitives only)
            flat_meta = {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "source": str(c.metadata.get("source", "")),
                "page_number": int(c.metadata.get("page_number") or 1),
                "has_tables": bool(len(c.tables) > 0),
                "has_images": bool(len(c.images) > 0),
                "content_types": ",".join(c.content_types)
            }
            doc = Document(page_content=c.page_content, metadata=flat_meta)
            documents.append(doc)
            ids.append(c.chunk_id)

        logger.info(f"Adding {len(documents)} chunks to ChromaDB...")
        vector_store.add_documents(documents=documents, ids=ids)
        logger.info("Chunks successfully indexed in ChromaDB.")

    def delete_document(self, document_id: str) -> None:
        """Deletes all chunks associated with a document_id."""
        vector_store = self.get_vector_store()
        try:
            # Chroma allows where clause deletion
            vector_store.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document_id: {document_id}")
        except Exception as e:
            logger.warning(f"Chroma delete error for {document_id}: {e}")

    def similarity_search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[DocumentChunkModel, float, int]]:
        """
        Performs standard similarity search.
        Returns: list of (DocumentChunkModel, normalized_score, rank)
        """
        vector_store = self.get_vector_store()
        results = vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )

        ranked_results: List[Tuple[DocumentChunkModel, float, int]] = []
        for rank, (doc, distance) in enumerate(results, start=1):
            # Chroma default L2/cosine distance to similarity score
            # Score normalization: 1.0 / (1.0 + distance) or max(0, 1 - distance)
            similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            chunk_id = doc.metadata.get("chunk_id")
            
            # Fetch rich chunk from DB or construct from doc
            chunk_model = db_service.get_chunk(chunk_id) if chunk_id else None
            if not chunk_model:
                chunk_model = DocumentChunkModel(
                    chunk_id=chunk_id or f"chunk_{rank}",
                    document_id=doc.metadata.get("document_id", "unknown"),
                    page_content=doc.page_content,
                    raw_text=doc.page_content,
                    metadata=doc.metadata
                )
            ranked_results.append((chunk_model, round(similarity_score, 4), rank))

        return ranked_results

    def similarity_threshold_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Tuple[DocumentChunkModel, float, int]], List[Tuple[DocumentChunkModel, float, int]]]:
        """
        Retrieves top-k candidates and filters them against score_threshold.
        Returns: (accepted_candidates, discarded_candidates)
        """
        all_candidates = self.similarity_search_with_scores(query=query, k=k * 2, filter_dict=filter_dict)
        accepted = []
        discarded = []

        for chunk_model, score, _ in all_candidates:
            if score >= score_threshold and len(accepted) < k:
                accepted.append((chunk_model, score, len(accepted) + 1))
            else:
                discarded.append((chunk_model, score, len(discarded) + 1))

        return accepted, discarded

    def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 10,
        lambda_mult: float = 0.5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[DocumentChunkModel, float, int]]:
        """
        Performs Maximum Marginal Relevance search for high diversity and relevance.
        """
        vector_store = self.get_vector_store()
        try:
            docs = vector_store.max_marginal_relevance_search(
                query=query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                filter=filter_dict
            )
        except Exception as e:
            logger.warning(f"MMR direct search failed ({e}). Falling back to similarity.")
            docs = vector_store.similarity_search(query=query, k=k, filter=filter_dict)

        results: List[Tuple[DocumentChunkModel, float, int]] = []
        for rank, doc in enumerate(docs, start=1):
            chunk_id = doc.metadata.get("chunk_id")
            chunk_model = db_service.get_chunk(chunk_id) if chunk_id else None
            if not chunk_model:
                chunk_model = DocumentChunkModel(
                    chunk_id=chunk_id or f"chunk_{rank}",
                    document_id=doc.metadata.get("document_id", "unknown"),
                    page_content=doc.page_content,
                    raw_text=doc.page_content,
                    metadata=doc.metadata
                )
            # Default MMR score placeholder if not exposed directly by Chroma
            results.append((chunk_model, round(1.0 - (rank * 0.05), 4), rank))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection stats."""
        try:
            vs = self.get_vector_store()
            col = vs._collection
            count = col.count() if col else 0
            return {
                "collection_name": self.settings.CHROMA_COLLECTION_NAME,
                "total_chunks": count
            }
        except Exception as e:
            logger.error(f"Error fetching vector store stats: {e}")
            return {
                "collection_name": self.settings.CHROMA_COLLECTION_NAME,
                "total_chunks": 0
            }

vector_store_service = VectorStoreService()
