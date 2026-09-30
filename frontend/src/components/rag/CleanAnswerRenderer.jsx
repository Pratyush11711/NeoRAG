import React, { useMemo } from 'react';
import { marked } from 'marked';
import { BookOpen } from 'lucide-react';

/**
 * Cleans up raw LaTeX equations into clean, readable notation.
 */
function cleanLatexMath(text = '') {
  if (!text) return '';

  return text
    // Replace block math $$ ... $$
    .replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
      let clean = formula
        .replace(/\\text\{([a-zA-Z0-9_\s]+)\}/g, '$1')
        .replace(/\\left\(/g, '(')
        .replace(/\\right\)/g, ')')
        .replace(/\\left\[/g, '[')
        .replace(/\\right\]/g, ']')
        .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1 / $2)')
        .replace(/\\cdot/g, '·')
        .replace(/\\times/g, '×')
        .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
        .replace(/_\{([^}]+)\}/g, '_$1')
        .replace(/\^T\b/g, 'ᵀ')
        .replace(/\^2\b/g, '²')
        .trim();

      return `\n\n\`\`\`math\n${clean}\n\`\`\`\n\n`;
    })
    // Replace inline math $ ... $
    .replace(/\$([^$\n]+)\$/g, (match, formula) => {
      let clean = formula
        .replace(/\\text\{([a-zA-Z0-9_\s]+)\}/g, '$1')
        .replace(/\\cdot/g, '·')
        .replace(/\\times/g, '×')
        .replace(/\^T\b/g, 'ᵀ')
        .trim();
      return `\`${clean}\``;
    });
}

/**
 * Normalizes all forms of citations ([chunk_id], [1], [1, 2], [chunk1, chunk2])
 * into clean standard tokens: {{CITE:rank:chunkId}}
 */
function normalizeCitations(text = '', sources = []) {
  if (!text) return '';

  // Build lookup maps
  const chunkMap = new Map();
  sources.forEach((src, idx) => {
    const rank = src.reranker_rank || src.retrieval_rank || (idx + 1);
    if (src.chunk_id) {
      chunkMap.set(src.chunk_id.toLowerCase().trim(), { rank, chunkId: src.chunk_id, doc: src.document, page: src.page });
    }
    if (src.source_id) {
      chunkMap.set(src.source_id.toLowerCase().trim(), { rank, chunkId: src.chunk_id || src.source_id, doc: src.document, page: src.page });
    }
  });

  // Match bracketed citation groups: [chunk1, chunk2] or [1, 2] or [chunk_id] or [1]
  return text.replace(/\[([a-zA-Z0-9_\-.,\s]+)\]/g, (match, inner) => {
    const parts = inner.split(',').map(p => p.trim()).filter(Boolean);
    const resolvedTokens = [];

    for (const item of parts) {
      // Check if it's already a clean number (e.g. 1, 2, 3)
      if (/^\d+$/.test(item)) {
        const num = parseInt(item, 10);
        const matchedSource = sources[num - 1];
        const chunkId = matchedSource?.chunk_id || `chunk_${num}`;
        resolvedTokens.push(`{{CITE:${num}:${chunkId}}}`);
        continue;
      }

      // Check if it matches a chunk_id in sources
      const lower = item.toLowerCase();
      if (chunkMap.has(lower)) {
        const info = chunkMap.get(lower);
        resolvedTokens.push(`{{CITE:${info.rank}:${info.chunkId}}}`);
        continue;
      }

      // Partial match on chunk ID (e.g. filename prefix or chunk number)
      let found = false;
      for (const [key, info] of chunkMap.entries()) {
        if (key.includes(lower) || lower.includes(key)) {
          resolvedTokens.push(`{{CITE:${info.rank}:${info.chunkId}}}`);
          found = true;
          break;
        }
      }

      // If not recognized as citation, keep as original bracket item
      if (!found) {
        resolvedTokens.push(item);
      }
    }

    return resolvedTokens.join(' ');
  });
}

/**
 * CleanAnswerRenderer
 * Transforms raw RAG LLM responses into high-clarity, beautiful typography
 * with interactive, compact footnote citations and clean equation blocks.
 */
export const CleanAnswerRenderer = ({ 
  text = '', 
  sources = [], 
  highlightedSource = null, 
  onSourceClick = () => {} 
}) => {
  const processedHtml = useMemo(() => {
    if (!text) return '';

    // 1. Remove robotic introductory boilerplate
    let cleaned = text.replace(/^(Based on the provided documents[,:\s]*|According to the provided (documents|context)[,:\s]*)/i, '');

    // 2. Clean math / LaTeX notation
    cleaned = cleanLatexMath(cleaned);

    // 3. Normalize all citations to token markers
    cleaned = normalizeCitations(cleaned, sources);

    // 4. Configure marked for clean HTML
    marked.setOptions({
      gfm: true,
      breaks: true
    });

    return marked.parse(cleaned);
  }, [text, sources]);

  if (!text) {
    return <p className="text-neutral-500 italic text-sm">No response generated.</p>;
  }

  // Split parsed HTML on {{CITE:rank:chunkId}} tokens to inject interactive React buttons
  const tokens = processedHtml.split(/(\{\{CITE:\d+:[^}]+\}\})/g);

  return (
    <div className="clean-answer-container text-neutral-900 leading-relaxed font-sans text-sm selection:bg-[#ffd731]">
      {tokens.map((segment, index) => {
        const citeMatch = segment.match(/^\{\{CITE:(\d+):([^}]+)\}\}$/);
        if (citeMatch) {
          const rank = citeMatch[1];
          const chunkId = citeMatch[2];
          const isHighlighted = highlightedSource === chunkId;
          const sourceObj = sources.find(s => s.chunk_id === chunkId) || sources[parseInt(rank, 10) - 1];
          const docName = sourceObj?.document || `Source ${rank}`;
          const pageStr = sourceObj?.page ? ` (P. ${sourceObj.page})` : '';

          return (
            <button
              key={index}
              type="button"
              onClick={() => onSourceClick(chunkId)}
              className={`
                inline-flex items-center justify-center font-mono text-[11px] font-black
                h-[18px] min-w-[20px] px-1 mx-0.5 -translate-y-0.5 rounded border border-black cursor-pointer
                transition-all duration-150 select-none
                ${isHighlighted 
                  ? 'bg-[#ffd731] scale-110 shadow-[2px_2px_0px_0px_#000] ring-1 ring-black' 
                  : 'bg-[#4da2ff] hover:bg-[#ffd731] text-black shadow-[1px_1px_0px_0px_#000] hover:translate-x-[0.5px] hover:translate-y-[0.5px]'}
              `}
              title={`[#${rank}] ${docName}${pageStr} — Click to inspect source`}
            >
              {rank}
            </button>
          );
        }

        // Render HTML segment with bespoke Neobrutalist prose styling
        return (
          <span
            key={index}
            dangerouslySetInnerHTML={{ __html: segment }}
            className="prose-content [&_p]:mb-3 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:my-2 [&_ul]:space-y-1.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:my-2 [&_ol]:space-y-1.5 [&_li]:leading-relaxed [&_strong]:font-extrabold [&_strong]:text-black [&_h3]:font-black [&_h3]:text-base [&_h3]:mt-4 [&_h3]:mb-1 [&_code]:font-mono [&_code]:text-xs [&_code]:bg-[#fff9db] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:border [&_code]:border-black [&_code]:rounded [&_code]:font-bold [&_pre]:bg-neutral-900 [&_pre]:text-[#55db9c] [&_pre]:p-3 [&_pre]:rounded-lg [&_pre]:border-2 [&_pre]:border-black [&_pre]:font-mono [&_pre]:text-xs [&_pre]:my-3 [&_pre]:overflow-x-auto"
          />
        );
      })}
    </div>
  );
};
