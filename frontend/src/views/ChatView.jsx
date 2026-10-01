import React, { useState } from 'react';
import {
  Send, Sparkles, BookOpen, Layers, Clock, Cpu, CheckCircle, AlertCircle, FileSearch, ArrowRight, Download, Eye, FileText, Filter, Check
} from 'lucide-react';
import {
  NeoButton, NeoCard, NeoInput, NeoBadge, NeoSelect, NeoAlert
} from '../components/neobrutalism';
import { PipelineVisualizer } from '../components/rag/PipelineVisualizer';
import { RRFBreakdownTable } from '../components/rag/RRFBreakdownTable';
import { MultimodalChunkCard } from '../components/rag/MultimodalChunkCard';
import { DocumentViewerModal } from '../components/rag/DocumentViewerModal';
import { QuickDocumentUploader } from '../components/rag/QuickDocumentUploader';
import { CleanAnswerRenderer } from '../components/rag/CleanAnswerRenderer';
import {
  executeChat,
  loadSampleDocuments,
  getReferenceDocumentUrl,
  getDocumentDownloadUrl
} from '../services/api';

const ATTENTION_PAPER_FILENAME = 'attention-is-all-you-need.pdf';

const PRESET_QUERIES = [
  "What are the two main components of the Transformer architecture?",
  "Explain the multi-head self-attention mechanism in the encoder stack.",
  "What BLEU score did Transformer (big model) achieve on WMT 2014 English-to-German?",
  "Why is Positional Encoding necessary in Transformers?"
];

export const ChatView = ({ onSelectDocument }) => {
  const [query, setQuery] = useState(PRESET_QUERIES[0]);
  const [strategy, setStrategy] = useState('full_pipeline');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [highlightedSource, setHighlightedSource] = useState(null);

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
    // Set an insightful query tailored to the uploaded document
    setQuery(`Summarize the main points and key takeaways from ${docData.filename}`);
  };

  const handleSend = async (queryToSend = query) => {
    if (!queryToSend.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const payload = {
        query: queryToSend,
        strategy: strategy,
        final_context_k: 5,
        include_images: true,
        debug: true
      };

      // If filtering to the active uploaded document
      if (filterToActiveDoc && activeDocument?.document_id) {
        payload.document_ids = [activeDocument.document_id];
      }

      const data = await executeChat(payload);
      setResponse(data);
    } catch (err) {
      setError(err.message || 'Chat generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleSourceSelect = (chunkId) => {
    setHighlightedSource(chunkId);
    const el = document.getElementById(chunkId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <div className="space-y-6">
      {/* Reference Paper & Quick Document Uploader Banner */}
      <NeoCard headerColor="#ffd731" title="Knowledge Base Reference & Document Query Engine">
        <div className="space-y-5">
          {/* Flagship Paper Reference Strip */}
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
                  Inspect the seminal Transformer architecture paper while asking questions or testing retrieval.
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

              <button
                type="button"
                onClick={() => {
                  setQuery("What are the two main components of the Transformer architecture?");
                  handleSend("What are the two main components of the Transformer architecture?");
                }}
                className="inline-flex items-center gap-1.5 h-[36px] px-3 text-xs font-bold font-mono bg-[#4da2ff] text-white border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
                title="Ask sample question on Attention paper"
              >
                <Sparkles size={14} />
                <span>Test Question</span>
              </button>
            </div>
          </div>

          {/* Quick Document Uploader (User can upload their own document and query it) */}
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

      {/* Search & Query Bar */}
      <NeoCard headerColor="#4da2ff" title="Ask Questions / Interactive RAG Generation">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="space-y-5"
        >
          {/* Target Filter Toggle */}
          {activeDocument && (
            <div className="flex items-center gap-3 p-2.5 bg-neutral-100 border-2 border-black rounded-lg text-xs font-mono">
              <span className="font-extrabold uppercase text-neutral-700">Scope:</span>
              <button
                type="button"
                onClick={() => setFilterToActiveDoc(true)}
                className={`
                  px-2.5 py-1 rounded border-2 border-black font-bold transition-all cursor-pointer flex items-center gap-1
                  ${filterToActiveDoc ? 'bg-[#55db9c] text-black shadow-[2px_2px_0px_0px_#000]' : 'bg-white text-neutral-600'}
                `}
              >
                {filterToActiveDoc && <Check size={12} />}
                <span>Only Ingested File ({activeDocument.filename})</span>
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
                <span>All Documents in Index</span>
              </button>
            </div>
          )}

          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <NeoInput
                label="Your Question"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  activeDocument
                    ? `Ask anything about ${activeDocument.filename}...`
                    : "Ask anything about the ingested documents or Attention paper..."
                }
                required
              />
            </div>
            <div className="w-full lg:w-72">
              <NeoSelect
                label="Retrieval Strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                options={[
                  { value: 'full_pipeline', label: 'Full Pipeline (RRF + Reranker)' },
                  { value: 'hybrid_rrf', label: 'Hybrid + RRF Fusion' },
                  { value: 'hybrid_rerank', label: 'Hybrid + Gemini Reranker' },
                  { value: 'hybrid', label: 'Weighted Hybrid' },
                  { value: 'mmr', label: 'MMR (Max Diversity)' },
                  { value: 'multi_query_rrf', label: 'Multi-Query + RRF' },
                  { value: 'similarity', label: 'Vector Similarity' },
                  { value: 'bm25', label: 'BM25 Keyword Only' }
                ]}
              />
            </div>
            <div className="flex items-end w-full lg:w-auto">
              <NeoButton
                type="submit"
                variant="main"
                size="md"
                disabled={loading}
                icon={loading ? Clock : Send}
                className="w-full lg:w-auto"
              >
                {loading ? 'Executing Pipeline...' : 'Generate Answer'}
              </NeoButton>
            </div>
          </div>

          {/* Quick Presets & Sample Loader */}
          <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 pt-4 pb-2 border-t-2 border-neutral-200">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono font-bold text-neutral-600 uppercase shrink-0">
                {activeDocument ? 'Suggested Questions:' : 'Try Preset:'}
              </span>
              {(activeDocument ? [
                `What are the key points in ${activeDocument.filename}?`,
                `What methodology or main idea is presented in ${activeDocument.filename}?`,
                `List the conclusions and results in ${activeDocument.filename}`
              ] : PRESET_QUERIES).map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuery(preset);
                    handleSend(preset);
                  }}
                  className="text-xs font-mono font-semibold px-3 py-1.5 bg-white border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none transition-all duration-150 cursor-pointer"
                >
                  "{preset.slice(0, 36)}..."
                </button>
              ))}
            </div>

            <div className="shrink-0 flex items-center">
              <NeoButton
                variant="lime"
                size="md"
                icon={Sparkles}
                onClick={async () => {
                  setLoading(true);
                  try {
                    const res = await loadSampleDocuments();
                    alert(`${res.message} Total chunks available: ${res.total_chunks}`);
                  } catch (e) {
                    alert(e.message);
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                ⚡ Load Sample Docs
              </NeoButton>
            </div>
          </div>
        </form>
      </NeoCard>

      {/* Error Alert */}
      {error && (
        <NeoAlert type="error" title="Pipeline Error" onClose={() => setError(null)}>
          {error}
        </NeoAlert>
      )}

      {/* Response Panel */}
      {response && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Answer Card */}
          <NeoCard
            headerColor="#55db9c"
            title="Evidence-Grounded Answer"
            badge="Gemini Flash"
            actions={
              <NeoBadge variant="dark" size="sm">
                Latency: {response.total_duration_ms} ms
              </NeoBadge>
            }
          >
            <div className="p-4 bg-white border-2 border-black rounded-lg">
              <CleanAnswerRenderer
                text={response.answer}
                sources={response.sources}
                highlightedSource={highlightedSource}
                onSourceClick={handleSourceSelect}
              />
            </div>

            {/* Source Citation Pills with View & Download */}
            {response.sources && response.sources.length > 0 && (
              <div className="mt-4 pt-3 border-t-2 border-black">
                <span className="text-xs font-mono font-extrabold uppercase tracking-wider block mb-2">
                  Grounding Sources & Citations ({response.sources.length}):
                </span>
                <div className="flex flex-wrap gap-2">
                  {response.sources.map((src, i) => (
                    <div
                      key={src.source_id || i}
                      className={`
                        flex items-center gap-2 p-1.5 px-3 border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] text-xs font-mono transition-all duration-150
                        ${highlightedSource === src.chunk_id ? 'bg-[#ffd731] scale-102 ring-2 ring-black' : 'bg-white'}
                      `}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setHighlightedSource(src.chunk_id);
                          const el = document.getElementById(src.chunk_id);
                          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }}
                        className="flex items-center gap-1.5 font-bold hover:underline cursor-pointer"
                        title="Click to scroll to evidence chunk"
                      >
                        <BookOpen className="w-3.5 h-3.5 text-black shrink-0" />
                        <span className="font-extrabold truncate max-w-[140px]">{src.document}</span>
                        {src.page && <span className="text-neutral-600 font-bold">— P.{src.page}</span>}
                      </button>

                      {/* Quick Document Viewer / Download Buttons */}
                      <button
                        type="button"
                        onClick={() => {
                          if (src.document_id) {
                            openViewerForDoc({ document_id: src.document_id, filename: src.document });
                          } else {
                            openViewerForReference(src.document);
                          }
                        }}
                        className="p-1 hover:bg-neutral-200 border border-black rounded cursor-pointer"
                        title={`View ${src.document}`}
                      >
                        <Eye size={12} />
                      </button>

                      <a
                        href={
                          src.document_id
                            ? getDocumentDownloadUrl(src.document_id)
                            : getReferenceDocumentUrl(src.document, true)
                        }
                        download={src.document}
                        className="p-1 hover:bg-neutral-200 border border-black rounded cursor-pointer"
                        title={`Download ${src.document}`}
                      >
                        <Download size={12} />
                      </a>

                      <span className="text-[10px] bg-black text-white px-1.5 py-0.2 rounded font-bold shrink-0">
                        #{src.reranker_rank || src.retrieval_rank}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </NeoCard>

          {/* Visual Pipeline Telemetry */}
          <NeoCard headerColor="#4da2ff" title="Pipeline Stage Execution Telemetry">
            <PipelineVisualizer
              trace={response.pipeline_trace}
              totalDurationMs={response.total_duration_ms}
              strategy={response.strategy}
            />
          </NeoCard>

          {/* Reciprocal Rank Fusion Breakdown */}
          {response.fusion_results && response.fusion_results.length > 0 && (
            <NeoCard headerColor="#e9ccff" title="Reciprocal Rank Fusion (RRF) Analysis">
              <RRFBreakdownTable rrfResults={response.fusion_results} rrfK={60} />
            </NeoCard>
          )}

          {/* Retrieved Multimodal Context Evidence */}
          {response.retrieved_documents && response.retrieved_documents.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold text-base uppercase tracking-wider text-black flex items-center gap-2">
                  <FileSearch className="w-5 h-5 text-black" />
                  Retrieved Multimodal Evidence Chunks ({response.retrieved_documents.length})
                </h3>
                <span className="text-xs font-mono text-neutral-600">
                  Passed to Gemini Context
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {response.retrieved_documents.map((chunk, idx) => (
                  <div key={chunk.chunk_id || idx} id={chunk.chunk_id}>
                    <MultimodalChunkCard
                      chunk={chunk}
                      rank={chunk.rank || idx + 1}
                      score={chunk.score}
                      isCitationTarget={highlightedSource === chunk.chunk_id}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
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
