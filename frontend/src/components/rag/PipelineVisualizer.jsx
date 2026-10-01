import React, { useState } from 'react';
import {
  Cpu, Search, Split, Layers, Filter, Bot, ArrowRight, Clock, Hash, ChevronRight
} from 'lucide-react';
import { NeoBadge } from '../neobrutalism';

export const PipelineVisualizer = ({ trace = [], totalDurationMs = 0, strategy = 'full_pipeline' }) => {
  const [selectedStage, setSelectedStage] = useState(null);

  if (!trace || trace.length === 0) {
    return (
      <div className="p-4 border-2 border-dashed border-black rounded-lg text-center bg-white/50 text-neutral-600 text-xs font-mono">
        Pipeline execution trace will appear here after search or chat query.
      </div>
    );
  }

  const stageIcons = {
    query_processing: Cpu,
    query_generation: Split,
    vector_retrieval: Search,
    bm25_retrieval: Hash,
    weighted_hybrid_fusion: Layers,
    hybrid_rrf_fusion: Layers,
    rrf_fusion: Layers,
    mmr_selection: Filter,
    gemini_reranking: Bot,
    generation: Bot
  };

  const stageColors = {
    query_processing: '#e9e9e9',   // Soft Mist
    query_generation: '#e9ccff',   // Lavender
    vector_retrieval: '#4da2ff',   // Electric Blue
    bm25_retrieval: '#ffd731',     // Sunburst
    weighted_hybrid_fusion: '#55db9c', // Mint Pop
    hybrid_rrf_fusion: '#55db9c',      // Mint Pop
    rrf_fusion: '#55db9c',             // Mint Pop
    mmr_selection: '#5c4ade',      // Voltage Violet
    gemini_reranking: '#e9ccff',   // Lavender
    generation: '#55db9c'          // Mint Pop
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Total Latency Header */}
      <div className="flex items-center justify-between bg-black text-white p-2.5 px-4 rounded-md border-2 border-black">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#ffd731]" />
          <span className="font-mono text-xs uppercase font-bold tracking-wider">
            Total Pipeline Latency:
          </span>
          <span className="font-mono text-xs text-[#ffd731] font-extrabold">
            {totalDurationMs.toFixed(2)} ms
          </span>
        </div>
        <NeoBadge variant="lime" size="sm">
          {strategy}
        </NeoBadge>
      </div>

      {/* Visual Flowchart Track */}
      <div className="overflow-x-auto pb-2">
        <div className="flex items-center gap-2 min-w-max p-2">
          {trace.map((item, idx) => {
            const Icon = stageIcons[item.stage] || Cpu;
            const bg = stageColors[item.stage] || '#ffd731';
            const isSelected = selectedStage?.stage === item.stage;

            return (
              <React.Fragment key={idx}>
                <button
                  type="button"
                  onClick={() => setSelectedStage(isSelected ? null : item)}
                  className={`
                    flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 border-black
                    transition-all cursor-pointer text-left
                    ${isSelected ? 'shadow-[5px_5px_0px_0px_#000] translate-y-[-2px] ring-2 ring-black' : 'shadow-[3px_3px_0px_0px_#000] hover:translate-y-[-1px] hover:shadow-[4px_4px_0px_0px_#000]'}
                  `}
                  style={{ backgroundColor: bg, minWidth: '135px' }}
                >
                  <div className="w-full flex items-center justify-between gap-1">
                    <div className="p-1 border border-black bg-white rounded shadow-[1px_1px_0px_0px_#000]">
                      <Icon size={16} className="w-4 h-4 text-black shrink-0" />
                    </div>
                    <span className="font-mono text-[10px] font-bold px-1 border border-black bg-white/90 rounded">
                      {item.duration_ms} ms
                    </span>
                  </div>

                  <span className="font-mono text-xs font-extrabold uppercase text-black line-clamp-1 w-full text-center">
                    {item.stage.replace(/_/g, ' ')}
                  </span>

                  {(item.input_count !== null || item.output_count !== null) && (
                    <div className="font-mono text-[9px] text-neutral-800 font-bold bg-white/80 px-1.5 py-0.5 border border-black rounded w-full text-center">
                      {item.input_count !== null && `${item.input_count} in`}
                      {item.input_count !== null && item.output_count !== null && ' → '}
                      {item.output_count !== null && `${item.output_count} out`}
                    </div>
                  )}
                </button>

                {idx < trace.length - 1 && (
                  <ArrowRight size={16} className="w-4 h-4 text-black shrink-0 mx-0.5" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Selected Stage Detail Drawer / Banner */}
      {selectedStage && (
        <div className="p-3 bg-white border-2 border-black rounded-lg shadow-[3px_3px_0px_0px_#000] text-xs">
          <div className="flex items-center justify-between border-b-2 border-black pb-1.5 mb-2">
            <span className="font-bold uppercase tracking-wider text-black">
              Stage Inspector: <span className="font-mono text-[#4da2ff] bg-black px-1.5 py-0.5 rounded">{selectedStage.stage}</span>
            </span>
            <span className="font-mono text-xs font-bold text-neutral-600">
              Duration: {selectedStage.duration_ms} ms
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2">
            <div className="p-2 border border-black bg-neutral-50 rounded">
              <span className="text-[10px] uppercase font-bold text-neutral-500 block">Input Items</span>
              <span className="font-mono font-extrabold text-sm">{selectedStage.input_count ?? 'N/A'}</span>
            </div>
            <div className="p-2 border border-black bg-neutral-50 rounded">
              <span className="text-[10px] uppercase font-bold text-neutral-500 block">Output Items</span>
              <span className="font-mono font-extrabold text-sm">{selectedStage.output_count ?? 'N/A'}</span>
            </div>
            <div className="p-2 border border-black bg-neutral-50 rounded col-span-2">
              <span className="text-[10px] uppercase font-bold text-neutral-500 block">Stage Status</span>
              <span className="font-mono font-extrabold text-sm text-green-700">COMPLETED ✓</span>
            </div>
          </div>

          {selectedStage.metadata && Object.keys(selectedStage.metadata).length > 0 && (
            <div className="mt-2">
              <span className="text-[10px] uppercase font-bold text-neutral-500 block mb-1">Metadata Telemetry:</span>
              <pre className="p-2 bg-[#F8F5EE] border border-black rounded font-mono text-[11px] overflow-x-auto text-black">
                {JSON.stringify(selectedStage.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
