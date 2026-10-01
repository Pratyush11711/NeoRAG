import React, { useState } from 'react';
import {
  Search, Sliders, Layers, Sparkles, Filter, Clock, BookOpen, Eye, Download, Check, FileText
} from 'lucide-react';
import {
  NeoButton, NeoCard, NeoInput, NeoSelect, NeoSlider, NeoBadge, NeoAlert
} from '../components/neobrutalism';
import { PipelineVisualizer } from '../components/rag/PipelineVisualizer';
import { RRFBreakdownTable } from '../components/rag/RRFBreakdownTable';
import { MultimodalChunkCard } from '../components/rag/MultimodalChunkCard';
import { DocumentViewerModal } from '../components/rag/DocumentViewerModal';
import { QuickDocumentUploader } from '../components/rag/QuickDocumentUploader';
import { executeSearch, getReferenceDocumentUrl } from '../services/api';

const ATTENTION_PAPER_FILENAME = 'attention-is-all-you-need.pdf';

const BENCHMARK_PRESETS = [
  "attention is all you need",
  "multi-head self-attention mechanism",
  "position-wise feed-forward networks",
  "BLEU score comparison Table 2"
];

export const RetrievalPlaygroundView = () => {
  const [query, setQuery] = useState('attention is all you need');
  const [strategy, setStrategy] = useState('hybrid_rrf');
  const [k, setK] = useState(5);
  const [fetchK, setFetchK] = useState(10);
  const [lambdaMult, setLambdaMult] = useState(0.5);
  const [vectorWeight, setVectorWeight] = useState(0.7);
  const [bm25Weight, setBm25Weight] = useState(0.3);
  const [rrfK, setRrfK] = useState(60);
  const [rerankTopN, setRerankTopN] = useState(10);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Active uploaded document focus & filtering
  const [activeDocument, setActiveDocument] = useState(null);
  const [filterToActiveDoc, setFilterToActiveDoc] = useState(false);

  // Document Viewer Modal State
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerDoc, setViewerDoc] = useState(null);
  const [viewerReference, setViewerReference] = useState(null);

  const openViewerForReference = (filename = ATTENTION_PAPER_FILENAME) => {
    setViewerDoc(null);
    setViewerReference(filename);
    setViewerOpen(true);
  };

  const openViewerForDoc = (doc) => {
    setViewerReference(null);
    setViewerDoc(doc);
    setViewerOpen(true);
  };

  const handleDocumentIngested = (docData) => {
    setActiveDocument(docData);
    setFilterToActiveDoc(true);
    setQuery(`Key architecture and findings in ${docData.filename}`);
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const payload = {
        query,
        strategy,
        k,
        fetch_k: fetchK,
        lambda_mult: lambdaMult,
        vector_weight: vectorWeight,
        bm25_weight: bm25Weight,
        rrf_k: rrfK,
        rerank_top_n: rerankTopN,
        debug: true
      };

      if (filterToActiveDoc && activeDocument?.document_id) {
        payload.document_ids = [activeDocument.document_id];
      }

      const data = await executeSearch(payload);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Search execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Reference Paper & Upload Widget */}
      <NeoCard headerColor="#ffd731" title="Visualizer Knowledge Reference & Document Ingestion">
        <div className="space-y-5">
          {/* Reference Paper Strip */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 bg-[#fff9db] border-2 border-black rounded-xl shadow-[3px_3px_0px_0px_#000]">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2.5 bg-[#ffd731] border-2 border-black rounded-lg shadow-[2px_2px_0px_0px_#000] shrink-0">
                <BookOpen className="w-5 h-5 text-black" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-sm text-black uppercase tracking-tight truncate">
                    Reference Document: Attention Is All You Need
                  </span>
                  <span className="hidden sm:inline-block font-mono text-[10px] font-black uppercase bg-[#55db9c] text-black px-1.5 py-0.2 border border-black rounded">
                    Vaswani et al.
                  </span>
                </div>
                <p className="text-xs text-neutral-700 font-medium mt-0.5 truncate">
                  Compare how different retrieval algorithms (Vector, BM25, RRF, MMR, Reranker) rank the Attention paper.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => openViewerForReference(ATTENTION_PAPER_FILENAME)}
                className="inline-flex items-center gap-1.5 h-[36px] px-3 text-xs font-black uppercase tracking-wider bg-white text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
                title="Preview Attention Is All You Need paper"
              >
                <Eye size={14} className="text-black" />
                <span>Preview Paper</span>
              </button>

              <a
                href={getReferenceDocumentUrl(ATTENTION_PAPER_FILENAME, true)}
                download={ATTENTION_PAPER_FILENAME}
                className="inline-flex items-center gap-1.5 h-[36px] px-3 text-xs font-black uppercase tracking-wider bg-[#55db9c] text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
                title="Download Attention Is All You Need PDF"
              >
                <Download size={14} className="text-black" />
                <span>Download PDF</span>
              </a>
            </div>
          </div>

          {/* Quick Document Uploader for Visualizer Page */}
          <QuickDocumentUploader
            activeDocument={activeDocument}
            onDocumentIngested={handleDocumentIngested}
            onClearActiveDocument={() => {
              setActiveDocument(null);
              setFilterToActiveDoc(false);
            }}
            onPreviewDocument={(doc) => openViewerForDoc(doc)}
          />
        </div>
      </NeoCard>

      {/* Main Search Controls */}
      <NeoCard headerColor="#4da2ff" title="Retrieval Strategy Laboratory & Benchmark">
        <div className="space-y-6">
          {/* Active Document Filter Badge */}
          {activeDocument && (
            <div className="flex items-center gap-3 p-2.5 bg-neutral-100 border-2 border-black rounded-lg text-xs font-mono">
              <span className="font-extrabold uppercase text-neutral-700">Benchmark Target:</span>
              <button
                type="button"
                onClick={() => setFilterToActiveDoc(true)}
                className={`
                  px-2.5 py-1 rounded border-2 border-black font-bold transition-all cursor-pointer flex items-center gap-1
                  ${filterToActiveDoc ? 'bg-[#55db9c] text-black shadow-[2px_2px_0px_0px_#000]' : 'bg-white text-neutral-600'}
                `}
              >
                {filterToActiveDoc && <Check size={12} />}
                <span>Only Uploaded Doc ({activeDocument.filename})</span>
              </button>
              <button
                type="button"
                onClick={() => setFilterToActiveDoc(false)}
                className={`
                  px-2.5 py-1 rounded border-2 border-black font-bold transition-all cursor-pointer flex items-center gap-1
                  ${!filterToActiveDoc ? 'bg-[#ffd731] text-black shadow-[2px_2px_0px_0px_#000]' : 'bg-white text-neutral-600'}
                `}
              >
                {!filterToActiveDoc && <Check size={12} />}
                <span>All Ingested Documents</span>
              </button>
            </div>
          )}

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <NeoInput
                label="Search Query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter query to test retrieval..."
              />
            </div>
            <div className="w-full lg:w-72">
              <NeoSelect
                label="Strategy Selection"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                options={[
                  { value: 'hybrid_rrf', label: 'Hybrid + RRF Fusion' },
                  { value: 'hybrid', label: 'Weighted Hybrid (Vector + BM25)' },
                  { value: 'hybrid_rerank', label: 'Hybrid + Gemini Reranking' },
                  { value: 'mmr', label: 'Max Marginal Relevance (MMR)' },
                  { value: 'multi_query_rrf', label: 'Multi-Query + RRF' },
                  { value: 'multi_query', label: 'Multi-Query Expansion' },
                  { value: 'similarity', label: 'Pure Vector Similarity' },
                  { value: 'similarity_threshold', label: 'Similarity Threshold' },
                  { value: 'bm25', label: 'BM25 Keyword Search' },
                  { value: 'full_pipeline', label: 'Full Production Pipeline' }
                ]}
              />
            </div>
            <div className="flex items-end w-full lg:w-auto">
              <NeoButton
                variant="main"
                size="md"
                onClick={handleSearch}
                disabled={loading}
                icon={Search}
                className="w-full lg:w-auto"
              >
                {loading ? 'Searching...' : 'Run Search'}
              </NeoButton>
            </div>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-2 pt-2 pb-1 border-t-2 border-neutral-200">
            <span className="text-xs font-mono font-bold text-neutral-600 uppercase shrink-0">
              Benchmark Queries:
            </span>
            {BENCHMARK_PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(preset);
                }}
                className="text-xs font-mono font-semibold px-2.5 py-1 bg-white border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none transition-all duration-150 cursor-pointer"
              >
                "{preset}"
              </button>
            ))}
          </div>

          {/* Strategy-Specific Tuners */}
          <div className="p-5 bg-white border-2 border-black rounded-[12px] shadow-[2px_2px_0px_0px_#000]">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-black block mb-4 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-black" />
              Strategy Parameters & Knobs:
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <NeoSlider
                label="Top-K Results"
                value={k}
                onChange={setK}
                min={1}
                max={20}
                step={1}
                formatValue={(v) => `k = ${v}`}
              />

              {strategy === 'mmr' && (
                <>
                  <NeoSlider
                    label="Fetch-K (Candidate Pool)"
                    value={fetchK}
                    onChange={setFetchK}
                    min={k}
                    max={50}
                    step={1}
                    formatValue={(v) => `fetch = ${v}`}
                  />
                  <NeoSlider
                    label="Lambda (Diversity)"
                    value={lambdaMult}
                    onChange={setLambdaMult}
                    min={0}
                    max={1}
                    step={0.05}
                    formatValue={(v) => `λ = ${v.toFixed(2)}`}
                    helperText="0: Maximum Diversity, 1: Pure Relevance"
                  />
                </>
              )}

              {strategy === 'hybrid' && (
                <>
                  <NeoSlider
                    label="Vector Weight"
                    value={vectorWeight}
                    onChange={(v) => {
                      setVectorWeight(v);
                      setBm25Weight(parseFloat((1 - v).toFixed(2)));
                    }}
                    min={0}
                    max={1}
                    step={0.05}
                    formatValue={(v) => `Vec: ${v.toFixed(2)}`}
                  />
                  <NeoSlider
                    label="BM25 Weight"
                    value={bm25Weight}
                    onChange={(v) => {
                      setBm25Weight(v);
                      setVectorWeight(parseFloat((1 - v).toFixed(2)));
                    }}
                    min={0}
                    max={1}
                    step={0.05}
                    formatValue={(v) => `BM25: ${v.toFixed(2)}`}
                  />
                </>
              )}

              {(strategy.includes('rrf') || strategy === 'full_pipeline') && (
                <NeoSlider
                  label="RRF Constant (k)"
                  value={rrfK}
                  onChange={setRrfK}
                  min={10}
                  max={120}
                  step={5}
                  formatValue={(v) => `k = ${v}`}
                  helperText="Formula: 1 / (k + rank)"
                />
              )}

              {(strategy.includes('rerank') || strategy === 'full_pipeline') && (
                <NeoSlider
                  label="Rerank Candidate Pool"
                  value={rerankTopN}
                  onChange={setRerankTopN}
                  min={k}
                  max={25}
                  step={1}
                  formatValue={(v) => `Top ${v}`}
                />
              )}
            </div>
          </div>
        </div>
      </NeoCard>

      {error && (
        <NeoAlert type="error" title="Search Error" onClose={() => setError(null)}>
          {error}
        </NeoAlert>
      )}

      {results && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Telemetry Trace */}
          <NeoCard headerColor="#ffd731" title="Execution Timing Breakdown">
            <PipelineVisualizer
              trace={results.pipeline_trace}
              totalDurationMs={results.total_duration_ms}
              strategy={results.strategy}
            />
          </NeoCard>

          {/* MMR Metadata Card */}
          {results.mmr_meta && (
            <NeoCard headerColor="#55db9c" title="Maximum Marginal Relevance (MMR) Telemetry">
              <div className="grid grid-cols-3 gap-3 font-mono text-center">
                <div className="p-3 bg-white border-2 border-black rounded">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold block">Candidate Pool</span>
                  <span className="text-xl font-extrabold">{results.mmr_meta.candidate_pool_size} Chunks</span>
                </div>
                <div className="p-3 bg-white border-2 border-black rounded">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold block">MMR Selected</span>
                  <span className="text-xl font-extrabold text-[#55db9c] font-black">{results.mmr_meta.final_selected_count} Chunks</span>
                </div>
                <div className="p-3 bg-white border-2 border-black rounded">
                  <span className="text-[10px] text-neutral-500 uppercase font-bold block">Diversity Lambda</span>
                  <span className="text-xl font-extrabold">{results.mmr_meta.lambda_mult}</span>
                </div>
              </div>
            </NeoCard>
          )}

          {/* RRF Breakdown Table */}
          {results.rrf_results && results.rrf_results.length > 0 && (
            <NeoCard headerColor="#e9ccff" title="RRF Rank & Contribution Matrix">
              <RRFBreakdownTable rrfResults={results.rrf_results} rrfK={rrfK} />
            </NeoCard>
          )}

          {/* Retrieved Document Cards */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-base uppercase tracking-wider text-black">
                Retrieved Ranked Documents ({results.documents?.length || 0})
              </h3>
              <NeoBadge variant="cyan" size="sm">
                Strategy: {results.strategy}
              </NeoBadge>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {results.documents?.map((chunk, idx) => (
                <MultimodalChunkCard
                  key={chunk.chunk_id || idx}
                  chunk={chunk}
                  rank={chunk.rank || idx + 1}
                  score={chunk.score}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Document Viewer Modal */}
      <DocumentViewerModal
        isOpen={viewerOpen}
        onClose={() => setViewerOpen(false)}
        document={viewerDoc}
        referenceFilename={viewerReference}
      />
    </div>
  );
};
