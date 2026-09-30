import React, { useState, useEffect } from 'react';
import { History, Eye, Clock, RefreshCw, Cpu, Layers } from 'lucide-react';
import { 
  NeoButton, NeoCard, NeoTable, NeoBadge, NeoModal, NeoAlert 
} from '../components/neobrutalism';
import { PipelineVisualizer } from '../components/rag/PipelineVisualizer';
import { fetchRuns, fetchRunDetail } from '../services/api';

export const HistoryView = () => {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await fetchRuns(50);
      setRuns(res.runs || []);
    } catch (err) {
      setError('Failed to fetch run history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleInspect = async (runId) => {
    setDetailLoading(true);
    try {
      const detail = await fetchRunDetail(runId);
      setSelectedRun(detail);
    } catch (err) {
      setError('Failed to load run details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const headers = [
    { label: 'Timestamp' },
    { label: 'Query' },
    { label: 'Strategy' },
    { label: 'Duration', align: 'center' },
    { label: 'Candidates', align: 'center' },
    { label: 'Actions', align: 'center' }
  ];

  return (
    <div className="space-y-6">
      <NeoCard
        headerColor="#ffd731"
        title="Execution Run History & Telemetry Log"
        actions={
          <NeoButton variant="neutral" size="sm" onClick={loadHistory} disabled={loading} icon={RefreshCw}>
            Refresh
          </NeoButton>
        }
      >
        <p className="text-xs text-neutral-600 font-medium mb-5">
          Every search and chat request is permanently recorded in SQLite for latency analysis and telemetry audits.
        </p>

        {error && (
          <NeoAlert type="error" title="Error" onClose={() => setError(null)} className="mb-4">
            {error}
          </NeoAlert>
        )}

        {runs.length === 0 ? (
          <div className="p-6 border-2 border-dashed border-black rounded text-center font-mono text-xs text-neutral-600">
            No pipeline runs logged yet. Execute a search or chat query to record telemetry.
          </div>
        ) : (
          <div className="my-2">
            <NeoTable headers={headers} headerBg="#ffd731">
              {runs.map((r) => (
                <tr key={r.run_id} className="hover:bg-[#dceeff]/30 transition-colors">
                  <td className="px-4 py-4 border-r-2 border-black font-mono text-[11px] text-neutral-600 whitespace-nowrap">
                    {new Date(r.created_at).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-4 border-r-2 border-black font-medium text-xs max-w-[280px] truncate" title={r.query}>
                    {r.query}
                  </td>
                  <td className="px-4 py-4 border-r-2 border-black font-mono">
                    <NeoBadge variant="lime" size="sm">
                      {r.strategy}
                    </NeoBadge>
                  </td>
                  <td className="px-4 py-4 text-center border-r-2 border-black font-mono font-bold text-xs">
                    {r.duration_ms} ms
                  </td>
                  <td className="px-4 py-4 text-center border-r-2 border-black font-mono font-bold text-xs">
                    {r.number_of_candidates}
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <NeoButton
                      variant="neutral"
                      size="sm"
                      onClick={() => handleInspect(r.run_id)}
                      icon={Eye}
                    >
                      Trace
                    </NeoButton>
                  </td>
                </tr>
              ))}
            </NeoTable>
          </div>
        )}
      </NeoCard>

      {/* Run Detail Modal */}
      <NeoModal
        isOpen={Boolean(selectedRun)}
        onClose={() => setSelectedRun(null)}
        title={`Run Telemetry: ${selectedRun?.run_id}`}
        headerColor="#4da2ff"
        maxWidth="max-w-3xl"
      >
        {selectedRun && (
          <div className="space-y-4">
            <div className="p-3 bg-white border-2 border-black rounded-lg">
              <span className="text-[10px] font-mono uppercase font-bold text-neutral-500 block">Query:</span>
              <p className="font-extrabold text-sm text-black mt-0.5">{selectedRun.query}</p>
            </div>

            {selectedRun.final_answer && (
              <div className="p-3 bg-white border-2 border-black rounded-lg">
                <span className="text-[10px] font-mono uppercase font-bold text-neutral-500 block mb-1">Final Answer:</span>
                <p className="text-xs leading-relaxed font-medium whitespace-pre-wrap">{selectedRun.final_answer}</p>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-xs font-mono font-extrabold uppercase text-black block">
                Execution Stage Trace:
              </span>
              <PipelineVisualizer
                trace={selectedRun.trace}
                totalDurationMs={selectedRun.duration_ms}
                strategy={selectedRun.strategy}
              />
            </div>
          </div>
        )}
      </NeoModal>
    </div>
  );
};
