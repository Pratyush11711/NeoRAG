import React from 'react';
import { NeoTable, NeoBadge } from '../neobrutalism';
import { TrendingUp, Layers } from 'lucide-react';

export const RRFBreakdownTable = ({ rrfResults = [], rrfK = 60 }) => {
  if (!rrfResults || rrfResults.length === 0) {
    return (
      <div className="p-4 border-2 border-dashed border-black rounded-lg text-center bg-white/50 text-neutral-600 text-xs font-mono">
        No RRF fusion data available. Run a query using 'hybrid_rrf', 'multi_query_rrf', or 'full_pipeline'.
      </div>
    );
  }

  // Extract all unique sources from ranks (e.g. vector, bm25, query_1, etc.)
  const allSources = Array.from(
    new Set(rrfResults.flatMap((r) => Object.keys(r.ranks || {})))
  );

  const headers = [
    { label: 'Rank', align: 'center' },
    { label: 'Chunk ID' },
    ...allSources.map((s) => ({ label: `${s.toUpperCase()} (Rank / Contrib)`, align: 'center' })),
    { label: 'Final RRF Score', align: 'right' }
  ];

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs font-mono px-1">
        <span className="flex items-center gap-1.5 font-bold">
          <Layers className="w-4 h-4 text-[#5c4ade]" />
          Reciprocal Rank Fusion Analysis: <span className="underline">Score = Σ 1 / ({rrfK} + Rank)</span>
        </span>
        <span className="text-neutral-500 font-medium">
          Fused {rrfResults.length} candidate documents
        </span>
      </div>

      <NeoTable headers={headers} headerBg="#e9ccff">
        {rrfResults.map((item, idx) => {
          const isMultiSource = Object.keys(item.ranks || {}).length > 1;

          return (
            <tr
              key={item.chunk_id || idx}
              className={`hover:bg-[#dceeff]/40 transition-colors ${isMultiSource ? 'bg-[#55db9c]/15' : ''}`}
            >
              {/* Overall Rank */}
              <td className="p-3 text-center border-r-2 border-black font-extrabold font-mono text-sm">
                <span className="w-6 h-6 inline-flex items-center justify-center bg-black text-white rounded-full">
                  {idx + 1}
                </span>
              </td>

              {/* Chunk ID */}
              <td className="p-3 border-r-2 border-black font-mono font-bold text-xs">
                <div className="flex items-center gap-2">
                  <span className="truncate max-w-[200px]" title={item.chunk_id}>
                    {item.chunk_id}
                  </span>
                  {isMultiSource && (
                    <NeoBadge variant="lime" size="sm" icon={TrendingUp}>
                      Multi-Match
                    </NeoBadge>
                  )}
                </div>
              </td>

              {/* Source Columns */}
              {allSources.map((source) => {
                const rank = item.ranks ? item.ranks[source] : undefined;
                const contrib = item.contributions ? item.contributions[source] : undefined;

                return (
                  <td key={source} className="p-3 text-center border-r-2 border-black font-mono">
                    {rank !== undefined ? (
                      <div className="flex flex-col items-center">
                        <span className="font-extrabold text-xs">
                          #{rank}
                        </span>
                        <span className="text-[10px] text-neutral-600 bg-white px-1 border border-black rounded shadow-[1px_1px_0px_0px_#000]">
                          +{contrib?.toFixed(5)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-neutral-400 font-bold">—</span>
                    )}
                  </td>
                );
              })}

              {/* Final Score */}
              <td className="p-3 text-right font-mono font-extrabold text-xs text-black">
                <span className="px-2 py-1 bg-[#ffd731] border-2 border-black rounded shadow-[2px_2px_0px_0px_#000]">
                  {item.rrf_score.toFixed(6)}
                </span>
              </td>
            </tr>
          );
        })}
      </NeoTable>
    </div>
  );
};
