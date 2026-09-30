# Multimodal RAG Architectural Guide & Retrieval Math

## 1. Overview of the Pipeline
Retrieval-Augmented Generation (RAG) grounds language model generations in verified documents.
When dealing with complex technical reports, the pipeline processes multimodal information:
- Text paragraphs
- Structured tables (represented in HTML)
- Architectural diagrams and flowcharts (represented in base64)

## 2. Reciprocal Rank Fusion (RRF) Formula
Reciprocal Rank Fusion merges ranked lists from disparate retrieval mechanisms without requiring score calibration.
For any document `d` retrieved across multiple candidate lists `L`:
Score(d) = Sum_{m in L} 1 / (k + Rank_m(d))
Where:
- `k` is a smoothing constant, typically set to 60.
- `Rank_m(d)` is the 1-based position of document `d` in list `m`.

When a document appears at rank 1 in both Vector Search and BM25 Search:
- Vector contribution = 1 / (60 + 1) = 0.016393
- BM25 contribution = 1 / (60 + 1) = 0.016393
- Total Fused RRF Score = 0.032786

## 3. Maximum Marginal Relevance (MMR)
MMR optimizes for both query relevance and candidate diversity:
MMR = ArgMax_{d_i in R \ S} [ lambda * Sim(d_i, Query) - (1 - lambda) * Max_{d_j in S} Sim(d_i, d_j) ]
Where:
- `lambda` balances relevance vs diversity (0.5 balances both equally).
- `S` is the set of already selected documents.
- `R` is the candidate pool.

## 4. Gemini Neural Reranking
While vector search retrieves fast approximate nearest neighbors, Gemini LLM evaluates fine-grained context and logical alignment to re-order the top candidate documents before final context injection.
