import React, { useState, useEffect } from 'react';
import { BarChart3, MessageSquare, UploadCloud, Building2, ShieldCheck, ChevronDown } from 'lucide-react';
import { DashboardView } from './components/DashboardView';
import { ChatView } from './components/ChatView';
import { UploadView } from './components/UploadView';
import { apiClient } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [companies, setCompanies] = useState([
    { id: 'company_a', name: 'Example Corp A', ticker: 'EXA' },
    { id: 'msft', name: 'Microsoft Corporation', ticker: 'MSFT' },
    { id: 'aapl', name: 'Apple Inc.', ticker: 'AAPL' },
  ]);
  const [activeCompany, setActiveCompany] = useState('company_a');

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const data = await apiClient.getCompanies();
      if (data && data.length > 0) {
        setCompanies(data);
      }
    } catch {
      // Fallback to default initial companies
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F19] text-[#F3F4F6]">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-gray-800 bg-[#0B0F19]/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-white via-gray-200 to-emerald-400 bg-clip-text text-transparent">
              FinIntel
            </span>
            <span className="text-[11px] text-gray-400 ml-2 font-mono">Hybrid RAG</span>
          </div>
        </div>

        {/* Company Selector Context */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-gray-900/90 border border-gray-800 px-3 py-1.5 rounded-xl text-xs">
            <Building2 className="w-4 h-4 text-emerald-400" />
            <span className="text-gray-400">Portfolio Entity:</span>
            <select
              id="header-company-select"
              value={activeCompany}
              onChange={(e) => setActiveCompany(e.target.value)}
              className="bg-transparent text-emerald-300 font-semibold focus:outline-none cursor-pointer"
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id} className="bg-gray-900 text-gray-200">
                  {c.name} ({c.ticker || c.id})
                </option>
              ))}
            </select>
          </div>

          <div className="hidden sm:flex items-center space-x-1 text-[11px] px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>FastAPI + ChromaDB Live</span>
          </div>
        </div>
      </header>

      {/* Main App Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 border-b border-gray-800/80 pb-3">
          <button
            id="tab-dashboard-btn"
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'dashboard'
                ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 shadow-md shadow-emerald-950/20'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Financial Analytics & Charts</span>
          </button>

          <button
            id="tab-chat-btn"
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'chat'
                ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 shadow-md shadow-emerald-950/20'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Financial RAG Assistant</span>
          </button>

          <button
            id="tab-upload-btn"
            onClick={() => setActiveTab('upload')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'upload'
                ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 shadow-md shadow-emerald-950/20'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/40'
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Filings & Ingestion</span>
          </button>
        </div>

        {/* Tab Content Views */}
        <main>
          {activeTab === 'dashboard' && (
            <DashboardView
              activeCompany={activeCompany}
              companies={companies}
              onNavigateToUpload={() => setActiveTab('upload')}
            />
          )}

          {activeTab === 'chat' && (
            <ChatView activeCompany={activeCompany} companies={companies} />
          )}

          {activeTab === 'upload' && (
            <UploadView
              companies={companies}
              activeCompany={activeCompany}
              onUploadSuccess={() => loadCompanies()}
            />
          )}
        </main>
      </div>
    </div>
  );
}
