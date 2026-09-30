import pytest
from app.services.chunker import chunker_service
from app.services.document_parser import ParsedElement

def test_title_based_chunking():
    elements = [
        ParsedElement(
            element_id="el_1",
            category="Title",
            text="1. Introduction to Attention Mechanism",
            metadata={"page_number": 1}
        ),
        ParsedElement(
            element_id="el_2",
            category="NarrativeText",
            text="The Transformer relies entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned RNNs or convolution.",
            metadata={"page_number": 1}
        ),
        ParsedElement(
            element_id="el_3",
            category="Title",
            text="2. Model Architecture",
            metadata={"page_number": 2}
        ),
        ParsedElement(
            element_id="el_4",
            category="NarrativeText",
            text="Most competitive neural sequence transduction models have an encoder-decoder structure.",
            metadata={"page_number": 2}
        ),
        ParsedElement(
            element_id="el_5",
            category="Table",
            text="BLEU Scores on WMT 2014 English-to-German",
            metadata={"page_number": 3},
            table_html="<table><tr><th>Model</th><th>BLEU</th></tr><tr><td>Transformer (big)</td><td>28.4</td></tr></table>"
        ),
        ParsedElement(
            element_id="el_6",
            category="Image",
            text="Figure 1: The Transformer - model architecture.",
            metadata={"page_number": 3},
            image_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
    ]

    chunks = chunker_service.chunk_elements(
        document_id="doc_test_1",
        filename="test_paper.pdf",
        parsed_elements=elements,
        max_characters=200,
        new_after_n_chars=100
    )

    assert len(chunks) >= 2
    for c in chunks:
        assert c.chunk_id.startswith("doc_test_1_chunk_")
        assert c.document_id == "doc_test_1"
        assert len(c.content_types) > 0

    # Ensure table and image were preserved in the multimodal chunk
    multimodal_chunk = next((c for c in chunks if "table" in c.content_types or "image" in c.content_types), None)
    assert multimodal_chunk is not None
    assert len(multimodal_chunk.tables) > 0 or len(multimodal_chunk.images) > 0
