import logging
import re
from typing import List, Tuple, Optional, Dict
from rank_bm25 import BM25Okapi
from app.models.responses import DocumentChunkModel
from app.services.db_service import db_service

logger = logging.getLogger(__name__)

class BM25Service:
    """
    Local BM25 keyword retrieval service using rank_bm25.
    Operates without API calls and indexes document chunks.
    """

    def __init__(self):
        self._bm25: Optional[BM25Okapi] = None
        self._indexed_chunks: List[DocumentChunkModel] = []
        self._chunk_id_to_index: Dict[str, int] = {}

    def _tokenize(self, text: str) -> List[str]:
        # Fast lowercase alphanumeric tokenization
        return re.findall(r'\b\w+\b', text.lower())

    def ensure_indexed(self):
        """Builds index from DB chunks if index is empty."""
        if self._bm25 is None or not self._indexed_chunks:
            all_chunks = db_service.get_all_chunks()
            if all_chunks:
                self.index_chunks(all_chunks)

    def index_chunks(self, chunks: List[DocumentChunkModel]) -> None:
        """
        Indexes chunks for fast BM25 retrieval.
        """
        if not chunks:
            self._bm25 = None
            self._indexed_chunks = []
            self._chunk_id_to_index = {}
            return

        tokenized_corpus = [self._tokenize(c.page_content) for c in chunks]
        self._bm25 = BM25Okapi(tokenized_corpus)
        self._indexed_chunks = list(chunks)
        self._chunk_id_to_index = {c.chunk_id: i for i, c in enumerate(chunks)}
        logger.info(f"BM25 index built with {len(chunks)} chunks.")

    def search(
        self,
        query: str,
        k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Tuple[DocumentChunkModel, float, int]]:
        """
        Performs BM25 search.
        Returns: List of (DocumentChunkModel, score, rank)
        """
        self.ensure_indexed()

        if self._bm25 is None or not self._indexed_chunks:
            logger.info("BM25 index is empty. No documents returned.")
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        doc_scores = self._bm25.get_scores(query_tokens)
        
        # Pair with chunks
        scored_pairs = []
        for idx, score in enumerate(doc_scores):
            chunk = self._indexed_chunks[idx]
            if document_ids and chunk.document_id not in document_ids:
                continue
            # Handle BM25 negative IDF edge case on very small corpora (N <= 2)
            has_keyword_match = any(token in chunk.page_content.lower() for token in query_tokens)
            if score > 0.0 or has_keyword_match:
                effective_score = max(0.1, float(score)) if has_keyword_match else float(score)
                scored_pairs.append((chunk, effective_score))

        # Sort descending by score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        top_k_pairs = scored_pairs[:k]

        if not top_k_pairs:
            return []

        # Min-max normalize scores for fair comparison
        max_score = top_k_pairs[0][1]
        min_score = top_k_pairs[-1][1] if len(top_k_pairs) > 1 else 0.0

        results: List[Tuple[DocumentChunkModel, float, int]] = []
        for rank, (chunk, raw_score) in enumerate(top_k_pairs, start=1):
            if max_score > min_score:
                norm_score = (raw_score - min_score) / (max_score - min_score)
            else:
                norm_score = 1.0 if raw_score > 0 else 0.0
            
            # Keep raw_score in chunk metadata
            chunk.metadata["bm25_raw_score"] = round(raw_score, 4)
            results.append((chunk, round(norm_score, 4), rank))

        return results

bm25_service = BM25Service()
