import React, { useState } from 'react';
import { FileText, Table as TableIcon, Image as ImageIcon, ExternalLink, Hash, Eye } from 'lucide-react';
import { NeoCard, NeoBadge, NeoButton, NeoModal } from '../neobrutalism';

export const MultimodalChunkCard = ({ chunk, rank, score, isCitationTarget = false }) => {
  const [activeTab, setActiveTab] = useState('content'); // content, tables, images, metadata
  const [previewImage, setPreviewImage] = useState(null);

  const hasTables = chunk.tables && chunk.tables.length > 0;
  const hasImages = chunk.images && chunk.images.length > 0;

  return (
    <>
      <NeoCard
        className={`transition-all ${isCitationTarget ? 'ring-4 ring-[#ffd731] bg-[#dceeff]/30' : ''}`}
        headerColor={rank ? '#ffd731' : '#FFFFFF'}
        title={
          <div className="flex items-center gap-2">
            {rank && (
              <span className="font-mono text-xs font-extrabold px-2 py-0.5 bg-black text-white rounded">
                Rank #{rank}
              </span>
            )}
            <span className="font-mono text-xs font-bold truncate max-w-[260px]" title={chunk.chunk_id}>
              {chunk.chunk_id}
            </span>
          </div>
        }
        actions={
          <div className="flex items-center gap-1.5">
            {chunk.page && (
              <NeoBadge variant="cyan" size="sm">
                Page {chunk.page}
              </NeoBadge>
            )}
            {score !== null && score !== undefined && (
              <NeoBadge variant="lime" size="sm">
                Score: {typeof score === 'number' ? score.toFixed(4) : score}
              </NeoBadge>
            )}
          </div>
        }
      >
        {/* Multimodal Content Type Badges */}
        <div className="flex items-center gap-2.5 mb-4 border-b-2 border-black pb-3">
          <NeoBadge variant="dark" size="sm" icon={FileText}>
            Text
          </NeoBadge>
          {hasTables && (
            <NeoBadge variant="pink" size="sm" icon={TableIcon}>
              {chunk.tables.length} Table{chunk.tables.length > 1 ? 's' : ''}
            </NeoBadge>
          )}
          {hasImages && (
            <NeoBadge variant="purple" size="sm" icon={ImageIcon}>
              {chunk.images.length} Image{chunk.images.length > 1 ? 's' : ''}
            </NeoBadge>
          )}
          <span className="text-[11px] text-neutral-500 font-mono ml-auto truncate max-w-[180px]">
            {chunk.source || chunk.document_id}
          </span>
        </div>

        {/* View Tabs */}
        {(hasTables || hasImages) && (
          <div className="flex flex-wrap gap-2 mb-4 border-b border-neutral-300 pb-3">
            <button
              type="button"
              onClick={() => setActiveTab('content')}
              className={`px-3 py-1.5 text-xs font-bold border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] transition-all ${activeTab === 'content' ? 'bg-[#ffd731]' : 'bg-white hover:bg-neutral-100'}`}
            >
              Text Content
            </button>
            {hasTables && (
              <button
                type="button"
                onClick={() => setActiveTab('tables')}
                className={`px-3 py-1.5 text-xs font-bold border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] transition-all ${activeTab === 'tables' ? 'bg-[#e9ccff]' : 'bg-white hover:bg-neutral-100'}`}
              >
                Tables ({chunk.tables.length})
              </button>
            )}
            {hasImages && (
              <button
                type="button"
                onClick={() => setActiveTab('images')}
                className={`px-3 py-1.5 text-xs font-bold border-2 border-black rounded shadow-[2px_2px_0px_0px_#000] transition-all ${activeTab === 'images' ? 'bg-[#5c4ade] text-white' : 'bg-white hover:bg-neutral-100'}`}
              >
                Diagrams & Images ({chunk.images.length})
              </button>
            )}
          </div>
        )}

        {/* Tab 1: Text Content */}
        {activeTab === 'content' && (
          <div className="space-y-3">
            <div className="p-3 bg-[#e9e9e9]/30 border-2 border-black rounded text-xs font-medium leading-relaxed max-h-56 overflow-y-auto whitespace-pre-wrap">
              {chunk.content || chunk.raw_text}
            </div>
            {chunk.raw_text && chunk.content && chunk.raw_text !== chunk.content && (
              <details className="text-[11px] font-mono text-neutral-600 bg-white p-2 border border-black rounded">
                <summary className="cursor-pointer font-bold uppercase text-neutral-800">
                  Inspect Original Raw Text (Pre-Enhancement)
                </summary>
                <div className="mt-2 p-2 bg-neutral-100 border border-neutral-300 rounded whitespace-pre-wrap">
                  {chunk.raw_text}
                </div>
              </details>
            )}
          </div>
        )}

        {/* Tab 2: Tables Content */}
        {activeTab === 'tables' && (
          <div className="space-y-3">
            {chunk.tables.map((table, tIdx) => (
              <div key={table.table_id || tIdx} className="border-2 border-black rounded p-3 bg-white shadow-[2px_2px_0px_0px_#000]">
                <div className="flex items-center justify-between mb-2 pb-1 border-b border-black">
                  <span className="font-mono text-xs font-bold">
                    Table #{tIdx + 1} (Page {table.page_number || 'N/A'})
                  </span>
                  <NeoBadge variant="pink" size="sm">HTML Table</NeoBadge>
                </div>
                <div
                  className="overflow-x-auto text-xs [&_table]:w-full [&_table]:border-collapse [&_th]:border-2 [&_th]:border-black [&_th]:p-1.5 [&_th]:bg-[#ffd731] [&_td]:border [&_td]:border-black [&_td]:p-1.5"
                  dangerouslySetInnerHTML={{ __html: table.html }}
                />
              </div>
            ))}
          </div>
        )}

        {/* Tab 3: Images Content */}
        {activeTab === 'images' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {chunk.images.map((img, iIdx) => {
              const src = img.base64?.startsWith('data:')
                ? img.base64
                : `data:${img.mime_type || 'image/jpeg'};base64,${img.base64}`;

              return (
                <div key={img.image_id || iIdx} className="border-2 border-black rounded p-2 bg-white shadow-[2px_2px_0px_0px_#000] flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold">Figure #{iIdx + 1}</span>
                    <button
                      type="button"
                      onClick={() => setPreviewImage(src)}
                      className="p-1 border border-black rounded bg-[#ffd731] shadow-[1px_1px_0px_0px_#000] hover:scale-105"
                      title="Enlarge Image"
                    >
                      <Eye className="w-3.5 h-3.5 text-black" />
                    </button>
                  </div>
                  <div className="border border-black rounded overflow-hidden bg-neutral-100 flex items-center justify-center p-1">
                    <img
                      src={src}
                      alt={img.caption || `Extracted diagram ${iIdx + 1}`}
                      className="max-h-40 object-contain cursor-pointer"
                      onClick={() => setPreviewImage(src)}
                    />
                  </div>
                  {img.caption && (
                    <p className="text-[10px] text-neutral-600 italic line-clamp-2">{img.caption}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </NeoCard>

      {/* Image Preview Modal */}
      <NeoModal
        isOpen={Boolean(previewImage)}
        onClose={() => setPreviewImage(null)}
        title="Multimodal Diagram Inspector"
        headerColor="#4da2ff"
        maxWidth="max-w-3xl"
      >
        <div className="flex flex-col items-center gap-3">
          <div className="border-3 border-black rounded-lg overflow-hidden shadow-[4px_4px_0px_0px_#000] bg-white p-2 w-full flex justify-center">
            <img src={previewImage} alt="Diagram full preview" className="max-h-[60vh] object-contain" />
          </div>
          <NeoButton variant="neutral" size="sm" onClick={() => setPreviewImage(null)}>
            Close Inspector
          </NeoButton>
        </div>
      </NeoModal>
    </>
  );
};
