import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Sliders, FolderOpen, History, Sparkles, ExternalLink, Zap, ShieldCheck
} from 'lucide-react';
import { NeoButton, NeoBadge } from './components/neobrutalism';
import { ChatView } from './views/ChatView';
import { RetrievalPlaygroundView } from './views/RetrievalPlaygroundView';
import { DocumentsView } from './views/DocumentsView';
import { HistoryView } from './views/HistoryView';
import { fetchHealth } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [health, setHealth] = useState(null);
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await fetchHealth();
        setHealth(data);
        setBackendOnline(true);
      } catch (e) {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'chat', label: 'RAG Chat & Visualizer', icon: MessageSquare, badge: 'Live' },
    { id: 'playground', label: 'Retrieval Playground', icon: Sliders },
    { id: 'documents', label: 'Documents & Ingestion', icon: FolderOpen, badge: health ? `${health.total_documents}` : undefined },
    { id: 'history', label: 'Run History', icon: History }
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Slush Marquee Announcement Strip */}
      <div className="w-full bg-black text-white overflow-hidden py-1 border-b-2 border-black select-none z-50">
        <div className="flex whitespace-nowrap animate-marquee font-mono text-[11px] font-bold tracking-[0.032em] uppercase gap-6 items-center">
          <span>★ MULTIMODAL RAG ACTIVE</span>
          <span className="text-[#ffd731]">•</span>
          <span>GEMINI 3.6 FLASH EMBEDDINGS & GENERATION</span>
          <span className="text-[#55db9c]">•</span>
          <span>RECIPROCAL RANK FUSION (RRF) ENGINE</span>
          <span className="text-[#4da2ff]">•</span>
          <span>CHROMADB HYBRID VECTOR STORE</span>
          <span className="text-[#e9ccff]">•</span>
          <span>SLUSH DESIGN SYSTEM</span>
          <span className="text-[#fb4903]">•</span>
          <span>★ MULTIMODAL RAG ACTIVE</span>
          <span className="text-[#ffd731]">•</span>
          <span>GEMINI 3.6 FLASH EMBEDDINGS & GENERATION</span>
          <span className="text-[#55db9c]">•</span>
          <span>RECIPROCAL RANK FUSION (RRF) ENGINE</span>
          <span className="text-[#4da2ff]">•</span>
          <span>CHROMADB HYBRID VECTOR STORE</span>
          <span className="text-[#e9ccff]">•</span>
          <span>SLUSH DESIGN SYSTEM</span>
          <span className="text-[#fb4903]">•</span>
        </div>
      </div>

      {/* Neo-brutalist Top Header */}
      <header className="sticky top-0 z-40 bg-white border-b-4 border-black px-4 sm:px-8 py-3 shadow-[0px_4px_0px_0px_#000]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-3 border-black bg-[#ffd731] rounded-lg shadow-[3px_3px_0px_0px_#000] flex items-center justify-center font-black text-xl text-black">
              N
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-extrabold text-lg sm:text-xl tracking-tight text-black leading-none uppercase">
                  NEO-RAG // SYSTEM
                </h1>
                <span className="font-mono text-[10px] font-extrabold bg-[#55db9c] text-black px-1.5 py-0.2 border border-black rounded shadow-[1px_1px_0px_0px_#000]">
                  v1.0.0
                </span>
              </div>
              <p className="text-[11px] font-mono text-neutral-600 font-semibold mt-0.5">
                Multimodal RAG • Gemini Embeddings • ChromaDB • RRF • Gemini Reranker
              </p>
            </div>
          </div>

          {/* Backend Status Pills */}
          <div className="flex items-center flex-wrap gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 border-2 border-black rounded-md bg-white shadow-[2px_2px_0px_0px_#000] text-xs font-mono">
              <span className={`w-2.5 h-2.5 rounded-full ${backendOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="font-bold">{backendOnline ? 'API Connected' : 'API Offline'}</span>
            </div>

            {health && (
              <>
                <div className="hidden lg:flex items-center gap-1 px-2.5 py-1 border-2 border-black rounded-md bg-[#e9e9e9] shadow-[2px_2px_0px_0px_#000] text-[11px] font-mono">
                  <span className="text-neutral-500 font-bold">LLM:</span>
                  <span className="font-extrabold">{health.gemini_chat_model}</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 border-2 border-black rounded-md bg-[#ffd731] shadow-[2px_2px_0px_0px_#000] text-[11px] font-mono">
                  <span className="font-bold">Chunks:</span>
                  <span className="font-extrabold">{health.total_chunks}</span>
                </div>
              </>
            )}

            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold font-mono border-2 border-black rounded-md bg-[#4da2ff] shadow-[4px_4px_0px_0px_#000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none transition-all duration-150"
            >
              <span>Swagger API</span>
              <ExternalLink size={14} className="w-3.5 h-3.5 shrink-0" />
            </a>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto mt-3 pt-2 pb-3.5 px-1 border-t-2 border-neutral-200 flex overflow-x-auto md:overflow-visible gap-3 items-center">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTab(item.id)}
                className={`
                  flex items-center gap-2.5 h-[42px] px-4.5 font-bold text-xs uppercase tracking-wider
                  border-2 border-black rounded-lg transition-all duration-150 cursor-pointer select-none whitespace-nowrap
                  ${isActive ? 'bg-[#ffd731] shadow-[4px_4px_0px_0px_#000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none' : 'bg-white hover:bg-neutral-100 shadow-[4px_4px_0px_0px_#000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none'}
                `}
              >
                <Icon size={18} className="w-[18px] h-[18px] text-black shrink-0" />
                <span>{item.label}</span>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 border border-black font-mono font-bold rounded ${isActive ? 'bg-white' : 'bg-neutral-200'}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8">
        {activeTab === 'chat' && <ChatView onSelectDocument={() => setActiveTab('documents')} />}
        {activeTab === 'playground' && <RetrievalPlaygroundView />}
        {activeTab === 'documents' && <DocumentsView />}
        {activeTab === 'history' && <HistoryView />}
      </main>

      {/* Neo-brutalist Footer */}
      <footer className="bg-white border-t-4 border-black p-4 text-center text-xs font-mono text-neutral-700">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-extrabold uppercase text-black">NEO-RAG PLATFORM</span>
            <span>•</span>
            <span className="font-extrabold text-black bg-[#ffd731] px-2 py-0.5 border border-black rounded shadow-[2px_2px_0px_0px_#000]">
              made by Pratyush Gupta
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-[#55db9c] border border-black font-bold rounded">FastAPI</span>
            <span className="px-2 py-0.5 bg-[#4da2ff] border border-black font-bold rounded">ChromaDB</span>
            <span className="px-2 py-0.5 bg-[#e9ccff] border border-black font-bold rounded">RRF</span>
            <span className="px-2 py-0.5 bg-[#ffd731] border border-black font-bold rounded">Gemini</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
