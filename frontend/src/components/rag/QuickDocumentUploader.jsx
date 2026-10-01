import React, { useState, useRef } from 'react';
import {
  Upload, FileText, CheckCircle, Clock, Sparkles, X, Eye, Download, ArrowRight, AlertCircle
} from 'lucide-react';
import { NeoButton, NeoBadge, NeoAlert } from '../neobrutalism';
import { uploadAndIngestDocument, getDocumentDownloadUrl } from '../../services/api';

export const QuickDocumentUploader = ({
  onDocumentIngested,
  activeDocument,
  onClearActiveDocument,
  onPreviewDocument
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState(null); // { stage, percent, message }
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const processFile = async (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'txt', 'md'].includes(ext)) {
      setError('Please upload a PDF, TXT, or MD document.');
      return;
    }

    setError(null);
    setStatus({ stage: 'uploading', percent: 20, message: `Uploading ${file.name}...` });

    try {
      const result = await uploadAndIngestDocument(file, (progress) => {
        setStatus(progress);
      });

      if (onDocumentIngested) {
        onDocumentIngested(result);
      }

      // Auto-clear status after 3.5 seconds
      setTimeout(() => {
        setStatus(null);
      }, 3500);
    } catch (err) {
      setError(err.message || 'Upload & Ingestion failed.');
      setStatus(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="space-y-3">
      {/* Active Document Indicator / Filter pill */}
      {activeDocument && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-[#eef6ff] border-2 border-[#4da2ff] rounded-xl shadow-[3px_3px_0px_0px_#4da2ff]">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="p-1.5 bg-[#4da2ff] text-white border-2 border-black rounded shadow-[1px_1px_0px_0px_#000] shrink-0">
              <FileText size={16} />
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] font-black uppercase tracking-wider bg-black text-white px-1.5 py-0.2 rounded">
                  Targeted Document
                </span>
                <span className="font-extrabold text-xs sm:text-sm text-black truncate" title={activeDocument.filename}>
                  {activeDocument.filename}
                </span>
              </div>
              <p className="text-[11px] font-mono text-neutral-600 font-bold truncate">
                {activeDocument.chunk_count
                  ? `${activeDocument.chunk_count} chunks indexed • Questions will target this file`
                  : 'Ready for question answering & retrieval'
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onPreviewDocument && (
              <button
                type="button"
                onClick={() => onPreviewDocument(activeDocument)}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold font-mono bg-white border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none transition-all cursor-pointer"
                title="Preview document content"
              >
                <Eye size={13} />
                <span>View</span>
              </button>
            )}

            <a
              href={getDocumentDownloadUrl(activeDocument.document_id)}
              download={activeDocument.filename}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold font-mono bg-[#55db9c] text-black border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none transition-all cursor-pointer select-none"
              title="Download file"
            >
              <Download size={13} />
              <span>Download</span>
            </a>

            {onClearActiveDocument && (
              <button
                type="button"
                onClick={onClearActiveDocument}
                className="p-1 text-neutral-600 hover:text-black border border-black rounded bg-white hover:bg-neutral-200 transition-colors cursor-pointer"
                title="Clear filter & query all documents"
              >
                <X size={15} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative border-2 border-dashed rounded-xl p-4 sm:p-5 transition-all text-center
          ${isDragging
            ? 'border-black bg-[#ffd731]/20 scale-[1.01]'
            : 'border-black bg-white hover:bg-neutral-50 shadow-[2px_2px_0px_0px_#000]'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) {
              processFile(e.target.files[0]);
              e.target.value = '';
            }
          }}
        />

        {status ? (
          /* Multi-stage Progress State */
          <div className="space-y-3 py-1">
            <div className="flex items-center justify-center gap-2">
              <Clock className="w-5 h-5 text-black animate-spin" />
              <span className="font-extrabold text-sm font-mono text-black uppercase">
                {status.stage === 'completed' ? 'Ingestion Complete!' : 'Processing Document...'}
              </span>
            </div>

            {/* Neo-brutalist Progress Bar */}
            <div className="w-full max-w-md mx-auto h-4 bg-white border-2 border-black rounded-full overflow-hidden shadow-[2px_2px_0px_0px_#000]">
              <div
                className="h-full bg-[#55db9c] border-r-2 border-black transition-all duration-300"
                style={{ width: `${status.percent}%` }}
              />
            </div>

            <p className="text-xs font-mono font-bold text-neutral-700">
              {status.message}
            </p>
          </div>
        ) : (
          /* Default Upload Prompt */
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-left">
              <div className="p-2.5 bg-[#ffd731] border-2 border-black rounded-lg shadow-[2px_2px_0px_0px_#000] shrink-0">
                <Upload className="w-5 h-5 text-black" />
              </div>
              <div>
                <h4 className="font-extrabold text-xs sm:text-sm text-black uppercase tracking-tight">
                  Upload Any Document & Query It
                </h4>
                <p className="text-[11px] font-mono text-neutral-600 font-medium mt-0.5">
                  Drag & drop or browse a PDF, TXT, or MD to automatically extract tables, images, and index in ChromaDB.
                </p>
              </div>
            </div>

            <div className="shrink-0">
              <NeoButton
                variant="main"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                icon={Upload}
              >
                Select & Ingest Document
              </NeoButton>
            </div>
          </div>
        )}
      </div>

      {error && (
        <NeoAlert type="error" title="Upload Error" onClose={() => setError(null)}>
          {error}
        </NeoAlert>
      )}
    </div>
  );
};
