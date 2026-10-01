import React, { useState, useEffect } from 'react';
import {
  FileText, Download, ExternalLink, X, Eye, Layers, Table, Image as ImageIcon, CheckCircle, RefreshCw, AlertCircle
} from 'lucide-react';
import { NeoButton, NeoBadge } from '../neobrutalism';
import {
  getDocumentViewUrl,
  getDocumentDownloadUrl,
  getReferenceDocumentUrl,
  fetchDocumentDetails,
  fetchDocumentRawContent
} from '../../services/api';

export const DocumentViewerModal = ({ isOpen, onClose, document: doc, referenceFilename }) => {
  const [activeTab, setActiveTab] = useState('preview'); // 'preview' | 'chunks'
  const [details, setDetails] = useState(null);
  const [textContent, setTextContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const filename = doc?.filename || referenceFilename || 'Document';
  const isPdf = filename.toLowerCase().endsWith('.pdf');
  const isReference = !doc?.document_id && !!referenceFilename;

  const viewUrl = doc?.document_id
    ? getDocumentViewUrl(doc.document_id)
    : getReferenceDocumentUrl(referenceFilename || filename, false);

  const downloadUrl = doc?.document_id
    ? getDocumentDownloadUrl(doc.document_id)
    : getReferenceDocumentUrl(referenceFilename || filename, true);

  useEffect(() => {
    if (!isOpen) {
      setDetails(null);
      setTextContent(null);
      setError(null);
      return;
    }

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (doc?.document_id) {
          // Fetch document chunks
          const det = await fetchDocumentDetails(doc.document_id);
          setDetails(det);

          if (!isPdf) {
            const raw = await fetchDocumentRawContent(doc.document_id);
            setTextContent(raw.content || '');
          }
        } else if (!isPdf && referenceFilename) {
          // If reference is non-pdf, fetch content
          const res = await fetch(viewUrl);
          const txt = await res.text();
          setTextContent(txt);
        }
      } catch (err) {
        console.warn('Could not load extra document details:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isOpen, doc?.document_id, referenceFilename, isPdf, viewUrl]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="relative flex flex-col w-full max-w-5xl h-[90vh] bg-white border-4 border-black rounded-[16px] shadow-[8px_8px_0px_0px_#000] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-[#ffd731] border-b-4 border-black shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-white border-2 border-black rounded-lg shadow-[2px_2px_0px_0px_#000] shrink-0">
              <FileText className="w-5 h-5 text-black" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-black text-sm sm:text-base text-black truncate uppercase tracking-tight" title={filename}>
                  {filename}
                </h3>
                <NeoBadge variant={isPdf ? 'cyan' : 'lime'} size="sm">
                  {isPdf ? 'PDF DOCUMENT' : filename.endsWith('.md') ? 'MARKDOWN' : 'TEXT'}
                </NeoBadge>
              </div>
              <p className="text-[11px] font-mono text-black/80 font-bold truncate">
                {isReference
                  ? 'Official Reference Paper • Attention Is All You Need (Vaswani et al.)'
                  : doc?.document_id ? `Document ID: ${doc.document_id}` : 'Document Viewer'
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Download Button */}
            <a
              href={downloadUrl}
              download={filename}
              className="inline-flex items-center gap-1.5 h-[36px] px-3.5 text-xs font-black uppercase tracking-wider bg-[#55db9c] text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
              title={`Download ${filename}`}
            >
              <Download size={15} className="w-[15px] h-[15px] text-black" />
              <span>Download File</span>
            </a>

            {/* Open in New Tab Button */}
            <a
              href={viewUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 h-[36px] px-3 text-xs font-bold font-mono bg-white text-black border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[1px_1px_0px_0px_#000] transition-all cursor-pointer select-none"
              title="Open full view in new tab"
            >
              <span>New Tab</span>
              <ExternalLink size={13} />
            </a>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 bg-black text-white hover:bg-[#fb4903] hover:text-black border-2 border-black rounded-lg transition-colors cursor-pointer"
              title="Close modal"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Navigation Tabs (Preview vs Indexed Chunks) */}
        {details?.chunks && details.chunks.length > 0 && (
          <div className="flex items-center gap-2 px-5 py-2 bg-neutral-100 border-b-2 border-black font-mono text-xs font-bold shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('preview')}
              className={`
                px-3 py-1 border-2 border-black rounded transition-all cursor-pointer
                ${activeTab === 'preview' ? 'bg-[#ffd731] shadow-[2px_2px_0px_0px_#000]' : 'bg-white hover:bg-neutral-200'}
              `}
            >
              📄 Original Document Preview
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('chunks')}
              className={`
                px-3 py-1 border-2 border-black rounded transition-all cursor-pointer flex items-center gap-1.5
                ${activeTab === 'chunks' ? 'bg-[#4da2ff] text-white shadow-[2px_2px_0px_0px_#000]' : 'bg-white hover:bg-neutral-200 text-black'}
              `}
            >
              <Layers size={13} />
              <span>Extracted Chunks ({details.chunks.length})</span>
            </button>
          </div>
        )}

        {/* Modal Body Area */}
        <div className="flex-1 overflow-auto bg-neutral-50 p-3 sm:p-5">
          {activeTab === 'preview' ? (
            <div className="w-full h-full flex flex-col min-h-[420px]">
              {isPdf ? (
                <div className="relative flex-1 w-full h-full min-h-[500px] border-3 border-black rounded-xl overflow-hidden bg-neutral-200 shadow-[3px_3px_0px_0px_#000]">
                  <iframe
                    src={`${viewUrl}#toolbar=1&navpanes=0`}
                    title={filename}
                    className="w-full h-full min-h-[500px] border-0"
                  />
                  {/* Fallback info bar */}
                  <div className="absolute bottom-2 left-2 right-2 bg-white/95 border-2 border-black rounded-lg p-2.5 flex items-center justify-between gap-3 text-xs font-mono shadow-[2px_2px_0px_0px_#000]">
                    <span className="truncate">
                      Previewing <strong>{filename}</strong>
                    </span>
                    <a
                      href={downloadUrl}
                      download={filename}
                      className="font-bold underline text-blue-600 hover:text-blue-800 shrink-0 flex items-center gap-1"
                    >
                      <Download size={13} />
                      Download directly
                    </a>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-white border-3 border-black rounded-xl shadow-[3px_3px_0px_0px_#000] font-mono text-xs whitespace-pre-wrap leading-relaxed max-h-full overflow-y-auto">
                  {textContent || 'Loading document text...'}
                </div>
              )}
            </div>
          ) : (
            /* Indexed Chunks & Multimodal breakdown */
            <div className="space-y-4">
              <div className="p-3 bg-[#e9ccff] border-2 border-black rounded-lg font-mono text-xs font-bold flex items-center justify-between">
                <span>Total Chunks in Vector Index: {details.chunks.length}</span>
                <span>Document: {filename}</span>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {details.chunks.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="p-4 bg-white border-2 border-black rounded-xl shadow-[3px_3px_0px_0px_#000] space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-neutral-200 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-black bg-black text-white px-2 py-0.5 rounded">
                          Chunk #{idx + 1}
                        </span>
                        <span className="font-mono text-xs text-neutral-600 font-bold">
                          {chunk.chunk_id}
                        </span>
                      </div>
                      {chunk.page_number && (
                        <NeoBadge variant="yellow" size="sm">
                          Page {chunk.page_number}
                        </NeoBadge>
                      )}
                    </div>

                    <p className="font-mono text-xs text-neutral-800 whitespace-pre-wrap leading-relaxed">
                      {chunk.page_content || chunk.raw_text}
                    </p>

                    {/* Tables extracted */}
                    {chunk.tables && chunk.tables.length > 0 && (
                      <div className="p-3 bg-[#eef6ff] border-2 border-[#4da2ff] rounded-lg space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-[#4da2ff]">
                          <Table size={14} />
                          <span>Extracted HTML Table ({chunk.tables.length})</span>
                        </div>
                        {chunk.tables.map((t, tIdx) => (
                          <div
                            key={tIdx}
                            dangerouslySetInnerHTML={{ __html: t.html }}
                            className="overflow-x-auto text-[11px] font-sans border border-black/30 rounded p-1 bg-white"
                          />
                        ))}
                      </div>
                    )}

                    {/* Images extracted */}
                    {chunk.images && chunk.images.length > 0 && (
                      <div className="p-3 bg-[#fff7e6] border-2 border-[#ffd731] rounded-lg space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-black">
                          <ImageIcon size={14} />
                          <span>Extracted Figure / Image ({chunk.images.length})</span>
                        </div>
                        <div className="flex flex-wrap gap-3">
                          {chunk.images.map((img, iIdx) => (
                            <img
                              key={iIdx}
                              src={`data:${img.mime_type || 'image/jpeg'};base64,${img.base64}`}
                              alt={img.caption || `Extracted image ${iIdx + 1}`}
                              className="max-h-48 border-2 border-black rounded shadow-[2px_2px_0px_0px_#000]"
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
