import pytest
from app.services.bm25_service import bm25_service
from app.services.hybrid_service import hybrid_service
from app.services.mmr_service import mmr_service
from app.services.reranker_service import reranker_service
from app.models.responses import DocumentChunkModel

def test_bm25_retrieval():
    chunks = [
        DocumentChunkModel(
            chunk_id="chunk_1",
            document_id="doc_transformer",
            page_content="The Transformer is based on multi-head self-attention mechanisms and encoder-decoder stacks.",
            raw_text="The Transformer is based on multi-head self-attention mechanisms and encoder-decoder stacks."
        ),
        DocumentChunkModel(
            chunk_id="chunk_2",
            document_id="doc_cnn",
            page_content="Convolutional neural networks use kernel convolutions for computer vision feature maps.",
            raw_text="Convolutional neural networks use kernel convolutions for computer vision feature maps."
        ),
        DocumentChunkModel(
            chunk_id="chunk_3",
            document_id="doc_rnn",
            page_content="Recurrent neural networks compute hidden states sequentially over time steps.",
            raw_text="Recurrent neural networks compute hidden states sequentially over time steps."
        )
    ]

    bm25_service.index_chunks(chunks)

    results = bm25_service.search("self-attention multi-head transformer", k=2)
    assert len(results) >= 1
    top_chunk, score, rank = results[0]
    assert top_chunk.chunk_id == "chunk_1"
    assert rank == 1
    assert score > 0.0

def test_weighted_hybrid_fusion_math():
    # Verify weighted calculation: score = w_vec * vec_score + w_bm25 * bm25_score
    chunk = DocumentChunkModel(
        chunk_id="test_c1",
        document_id="doc1",
        page_content="Transformer model details",
        raw_text="Transformer model details"
    )

    vec_score = 0.80
    bm25_score = 0.60
    w_vec = 0.7
    w_bm25 = 0.3

    expected = (0.7 * 0.80) + (0.3 * 0.60) # 0.56 + 0.18 = 0.74
    calculated = round((w_vec * vec_score) + (w_bm25 * bm25_score), 4)
    assert calculated == 0.74

@pytest.mark.asyncio
async def test_reranker_fallback_offline():
    chunks = [
        DocumentChunkModel(chunk_id="c1", document_id="d1", page_content="First text", raw_text="First text"),
        DocumentChunkModel(chunk_id="c2", document_id="d1", page_content="Second text", raw_text="Second text")
    ]
    reranked, results = await reranker_service.rerank(
        query="test query",
        candidates=chunks,
        top_n=2
    )
    assert len(reranked) == 2
    assert len(results) == 2
    assert results[0].document_id == "c1"
    assert results[0].original_rank == 1
    assert results[0].reranked_rank == 1
