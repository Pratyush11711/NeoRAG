import React, { useState, useEffect } from 'react';
import {
  Upload, FileText, Trash2, RefreshCw, Table, Image as ImageIcon, CheckCircle, Clock, AlertTriangle, Layers, Eye, Sparkles, Download, BookOpen, ExternalLink
} from 'lucide-react';
import {
  NeoButton, NeoCard, NeoBadge, NeoAlert
} from '../components/neobrutalism';
import { DocumentViewerModal } from '../components/rag/DocumentViewerModal';
import {
  fetchDocuments,
  uploadDocument,
  ingestDocument,
  deleteDocument,
  loadSampleDocuments,
  getDocumentDownloadUrl,
  getReferenceDocumentUrl
} from '../services/api';

const ATTENTION_PAPER_FILENAME = 'attention-is-all-you-need.pdf';

export const DocumentsView = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ingestingId, setIngestingId] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

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

  const loadDocs = async () => {
    setLoading(true);
    try {
      const res = await fetchDocuments();
      setDocuments(res.documents || []);
    } catch (err) {
      setError('Failed to load documents list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const res = await uploadDocument(file);
      setSuccess(`Uploaded '${res.filename}' successfully! Ready for ingestion.`);
      await loadDocs();
    } catch (err) {
      setError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleIngest = async (docId, forceReprocess = false) => {
    setIngestingId(docId);
    setError(null);
    try {
      const res = await ingestDocument(docId, {
        force_reprocess: forceReprocess,
        max_characters: 3000,
        new_after_n_chars: 2400
      });
      setSuccess(`Ingested document! Produced ${res.chunk_count} chunks, ${res.tables_count} tables, ${res.images_count} images.`);
      await loadDocs();
    } catch (err) {
      setError(err.message || 'Ingestion failed.');
    } finally {
      setIngestingId(null);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Delete this document and all its indexed chunks?')) return;
    try {
      await deleteDocument(docId);
      setSuccess('Document deleted.');
      await loadDocs();
    } catch (err) {
      setError(err.message || 'Delete failed.');
    }
  };

  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await loadSampleDocuments();
      setSuccess(`${res.message} Total chunks in index: ${res.total_chunks}`);
      await loadDocs();
    } catch (err) {
      setError(err.message || 'Failed to load sample documents.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload & Sample Docs Banner */}
      <NeoCard headerColor="#e9ccff" title="Multimodal Ingestion Pipeline (Unstructured + Gemini)">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 p-6 border-2 border-dashed border-black rounded-[14px] bg-white">
          <div className="flex items-center gap-4">
            <div className="p-3.5 border-2 border-black bg-white rounded-xl shadow-[3px_3px_0px_0px_#000]">
              <Upload className="w-6 h-6 text-black" />
            </div>
            <div>
              <h4 className="font-extrabold text-sm uppercase">Upload or Test Sample Documents</h4>
              <p className="text-xs text-neutral-600 font-medium mt-0.5">
                Supports hi_res Unstructured extraction of text, tables (HTML), and images (base64).
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <NeoButton
              variant="lime"
              size="md"
              onClick={handleLoadSample}
              disabled={loading || uploading}
              icon={Sparkles}
            >
              {loading ? 'Loading Samples...' : '⚡ Load Sample Documents'}
            </NeoButton>

            <label className="cursor-pointer">
              <input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
              <span className="inline-flex items-center justify-center gap-2.5 h-[44px] px-5 text-sm font-bold bg-[#ffd731] text-black border-2 border-black rounded-lg shadow-[4px_4px_0px_0px_#000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none transition-all duration-150 cursor-pointer select-none">
                <Upload size={18} className="w-[18px] h-[18px] text-black shrink-0" />
                {uploading ? 'Uploading...' : 'Upload File'}
              </span>
            </label>
            <NeoButton variant="neutral" size="md" onClick={loadDocs} disabled={loading} icon={RefreshCw}>
              Refresh
            </NeoButton>
          </div>
        </div>
      </NeoCard>

      {/* Featured Reference Paper Card */}
      <NeoCard headerColor="#ffd731" title="Flagship Reference Document: Attention Is All You Need">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white border-2 border-black rounded-[12px] shadow-[3px_3px_0px_0px_#000]">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-[#ffd731] border-2 border-black rounded-xl shadow-[2px_2px_0px_0px_#000] shrink-0">
              <BookOpen className="w-6 h-6 text-black" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-black text-sm sm:text-base text-black uppercase">
                  Attention Is All You Need (Vaswani et al., 2017)
                </h4>
                <NeoBadge variant="lime" size="sm">
                  Primary Benchmark Paper
                </NeoBadge>
              </div>
              <p className="text-xs text-neutral-600 font-medium mt-1">
                The foundational Transformer paper introducing Multi-Head Self-Attention, Positional Encoding, and Feed-Forward Networks. Use this paper as ground truth reference when testing RAG retrieval and citation grounding.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={() => openViewerForReference(ATTENTION_PAPER_FILENAME)}
              className="inline-flex items-center gap-1.5 h-[40px] px-4 text-xs font-black uppercase tracking-wider bg-white text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
              title="Preview paper inside modal"
            >
              <Eye size={15} className="text-black" />
              <span>Preview Paper</span>
            </button>

            <a
              href={getReferenceDocumentUrl(ATTENTION_PAPER_FILENAME, true)}
              download={ATTENTION_PAPER_FILENAME}
              className="inline-flex items-center gap-1.5 h-[40px] px-4 text-xs font-black uppercase tracking-wider bg-[#55db9c] text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
              title="Download Attention Is All You Need PDF"
            >
              <Download size={15} className="text-black" />
              <span>Download PDF</span>
            </a>
          </div>
        </div>
      </NeoCard>

      {error && (
        <NeoAlert type="error" title="Action Error" onClose={() => setError(null)}>
          {error}
        </NeoAlert>
      )}

      {success && (
        <NeoAlert type="success" title="Success" onClose={() => setSuccess(null)}>
          {success}
        </NeoAlert>
      )}

      {/* Documents List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-extrabold text-base uppercase tracking-wider text-black flex items-center gap-2">
            <FileText className="w-5 h-5 text-black" />
            Knowledge Base Documents ({documents.length})
          </h3>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 border-3 border-black rounded-2xl bg-white shadow-[4px_4px_0px_0px_#000] text-center font-mono text-sm text-neutral-600">
            No documents uploaded yet. Upload a PDF or click '⚡ Load Sample Documents' above to begin.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {documents.map((doc) => {
              const isIngesting = ingestingId === doc.document_id;
              const isIngested = doc.status === 'ingested';

              return (
                <NeoCard
                  key={doc.document_id}
                  headerColor={isIngested ? '#55db9c' : '#ffd731'}
                  title={
                    <span className="truncate max-w-[220px] block" title={doc.filename}>
                      {doc.filename}
                    </span>
                  }
                  actions={
                    <NeoBadge
                      variant={isIngested ? 'lime' : doc.status === 'failed' ? 'danger' : 'yellow'}
                      size="sm"
                    >
                      {doc.status}
                    </NeoBadge>
                  }
                >
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                      <div className="p-2.5 border-2 border-black rounded-lg bg-white shadow-[1px_1px_0px_0px_#000]">
                        <span className="text-[10px] text-neutral-500 uppercase font-bold block">Elements</span>
                        <span className="font-extrabold text-sm">{doc.element_count || 0}</span>
                      </div>
                      <div className="p-2.5 border-2 border-black rounded-lg bg-white shadow-[1px_1px_0px_0px_#000]">
                        <span className="text-[10px] text-neutral-500 uppercase font-bold block">Chunks</span>
                        <span className="font-extrabold text-sm text-[#4da2ff]">{doc.chunk_count || 0}</span>
                      </div>
                      <div className="p-2.5 border-2 border-black rounded-lg bg-white shadow-[1px_1px_0px_0px_#000]">
                        <span className="text-[10px] text-neutral-500 uppercase font-bold block">Tables</span>
                        <span className="font-extrabold text-sm text-[#5c4ade]">{doc.tables_count || 0}</span>
                      </div>
                      <div className="p-2.5 border-2 border-black rounded-lg bg-white shadow-[1px_1px_0px_0px_#000]">
                        <span className="text-[10px] text-neutral-500 uppercase font-bold block">Images</span>
                        <span className="font-extrabold text-sm text-[#fb4903]">{doc.images_count || 0}</span>
                      </div>
                    </div>

                    <div className="text-[11px] font-mono text-neutral-500 flex justify-between border-t-2 border-neutral-200 pt-2.5">
                      <span>ID: {doc.document_id.slice(0, 16)}...</span>
                      <span>Uploaded: {new Date(doc.upload_date).toLocaleTimeString()}</span>
                    </div>

                    {/* Action Buttons: Preview, Download, Ingest, Delete */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-3 pb-1 border-t-2 border-black">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => openViewerForDoc(doc)}
                          className="inline-flex items-center gap-1 h-[32px] px-2.5 text-xs font-bold font-mono bg-white border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none transition-all cursor-pointer"
                          title="View / Inspect document"
                        >
                          <Eye size={13} />
                          <span>Preview</span>
                        </button>

                        <a
                          href={getDocumentDownloadUrl(doc.document_id)}
                          download={doc.filename}
                          className="inline-flex items-center gap-1 h-[32px] px-2.5 text-xs font-bold font-mono bg-[#ffd731] text-black border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none transition-all cursor-pointer select-none"
                          title="Download document file"
                        >
                          <Download size={13} />
                          <span>Download</span>
                        </a>
                      </div>

                      <div className="flex items-center gap-2">
                        <NeoButton
                          variant={isIngested ? 'neutral' : 'main'}
                          size="sm"
                          onClick={() => handleIngest(doc.document_id, isIngested)}
                          disabled={isIngesting}
                          icon={isIngesting ? Clock : RefreshCw}
                        >
                          {isIngesting ? 'Ingesting...' : isIngested ? 'Re-Ingest' : 'Ingest'}
                        </NeoButton>

                        <NeoButton
                          variant="danger"
                          size="sm"
                          onClick={() => handleDelete(doc.document_id)}
                          icon={Trash2}
                        >
                          Delete
                        </NeoButton>
                      </div>
                    </div>
                  </div>
                </NeoCard>
              );
            })}
          </div>
        )}
      </div>

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
