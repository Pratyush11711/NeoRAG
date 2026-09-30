import pytest
from app.services.rrf_service import rrf_service
from app.models.responses import DocumentChunkModel

def test_rrf_scoring_single_list():
    chunk1 = DocumentChunkModel(chunk_id="chunk_1", document_id="doc_1", page_content="c1", raw_text="c1")
    chunk2 = DocumentChunkModel(chunk_id="chunk_2", document_id="doc_1", page_content="c2", raw_text="c2")

    ranked_lists = {
        "query_1": [
            (chunk1, 0.9, 1),
            (chunk2, 0.8, 2)
        ]
    }

    fused, contributions = rrf_service.fuse(ranked_lists, k=60)

    # For rank 1: 1 / (60 + 1) = 1 / 61 = 0.016393
    # For rank 2: 1 / (60 + 2) = 1 / 62 = 0.016129
    assert len(fused) == 2
    assert fused[0][0].chunk_id == "chunk_1"
    assert fused[1][0].chunk_id == "chunk_2"
    assert round(fused[0][1], 5) == round(1.0 / 61.0, 5)
    assert round(fused[1][1], 5) == round(1.0 / 62.0, 5)

    assert contributions[0].chunk_id == "chunk_1"
    assert contributions[0].ranks["query_1"] == 1
    assert round(contributions[0].contributions["query_1"], 5) == round(1.0 / 61.0, 5)

def test_rrf_scoring_multiple_queries():
    # chunk_A appears in both query_1 (rank 2) and query_2 (rank 1)
    # chunk_B appears only in query_1 (rank 1)
    chunk_a = DocumentChunkModel(chunk_id="chunk_A", document_id="doc_1", page_content="ca", raw_text="ca")
    chunk_b = DocumentChunkModel(chunk_id="chunk_B", document_id="doc_1", page_content="cb", raw_text="cb")

    ranked_lists = {
        "query_1": [(chunk_b, 0.9, 1), (chunk_a, 0.8, 2)],
        "query_2": [(chunk_a, 0.95, 1)]
    }

    fused, contributions = rrf_service.fuse(ranked_lists, k=60)

    # chunk_A score = 1/(60+2) + 1/(60+1) = 0.016129 + 0.016393 = 0.032522
    # chunk_B score = 1/(60+1) = 0.016393
    # chunk_A should be rank 1 due to multi-list reinforcement!
    assert fused[0][0].chunk_id == "chunk_A"
    assert fused[0][2] == 1
    assert fused[1][0].chunk_id == "chunk_B"
    assert fused[1][2] == 2

    # Check contributions map
    c_a_contrib = next(c for c in contributions if c.chunk_id == "chunk_A")
    assert c_a_contrib.ranks == {"query_1": 2, "query_2": 1}
    assert "query_1" in c_a_contrib.contributions
    assert "query_2" in c_a_contrib.contributions
