import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertTriangle, ShieldCheck, FileText, ArrowUpRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '../api/client';
import { CitationModal } from './CitationModal';

export function ChatView({ activeCompany, companies }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Welcome to the **Financial Statement Intelligence Platform**.\n\nI can retrieve verified financial facts from corporate filings, compute exact deterministic indicators (such as YoY revenue growth, net margins, and debt ratios), and retrieve supporting management commentary with document page citations.`,
      structured_payload: {
        intent: 'info',
        metrics_retrieved: [],
        calculations: [],
        citations: [],
      },
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionText) => {
    const q = questionText || input;
    if (!q.trim() || loading) return;

    const userMsg = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await apiClient.queryChat({
        question: q,
        company_ids: [activeCompany],
      });

      const assistantMsg = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: res.data.answer,
        structured_payload: {
          intent: res.data.intent,
          metrics_retrieved: res.data.metrics_retrieved || [],
          calculations: res.data.calculations || [],
          citations: res.data.citations || [],
          validation_status: res.data.validation_status,
          validation_warnings: res.data.validation_warnings || [],
        },
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `**Error:** Failed to execute query. ${err.response?.data?.error || err.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    `How did Company A's revenue and net profit margin change from 2024 to 2025, and what explains the changes?`,
    `What factors and risks were identified behind operating expenses?`,
    `Calculate operating margin and net profit margin for FY2025.`,
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] glass-panel rounded-2xl border border-gray-800 overflow-hidden shadow-2xl">
      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-3xl rounded-2xl p-5 ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/20'
                  : 'bg-[#111827] border border-gray-800 text-gray-200'
              }`}
            >
              {/* Markdown Content */}
              <div className="prose prose-invert prose-sm max-w-none leading-relaxed">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {/* Verified Metrics Card (if assistant returned structured data) */}
              {msg.structured_payload?.metrics_retrieved?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-800">
                  <span className="text-[10px] font-bold tracking-wider uppercase text-emerald-400 flex items-center gap-1 mb-2">
                    <ShieldCheck className="w-3.5 h-3.5" /> Approved Financial Figures (PostgreSQL)
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {msg.structured_payload.metrics_retrieved.map((m, i) => (
                      <div key={i} className="bg-[#0B0F19] rounded-lg p-2.5 border border-gray-800">
                        <p className="text-[10px] text-gray-400 uppercase font-mono">{m.metric.replace('_', ' ')} (FY{m.fiscal_year})</p>
                        <p className="text-xs font-bold text-gray-100 font-mono mt-0.5">
                          ${(m.value / 1e6).toFixed(1)}M {m.currency}
                        </p>
                        <span className="text-[9px] text-gray-500">Page {m.source_page || 'Filing'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Deterministic Calculations Badges */}
              {msg.structured_payload?.calculations?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <span className="text-[10px] font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-1 mb-2">
                    <Sparkles className="w-3.5 h-3.5" /> Deterministic Python Indicators
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.structured_payload.calculations.map((c, i) => (
                      <div
                        key={i}
                        className="bg-cyan-950/40 border border-cyan-800/50 rounded-lg px-2.5 py-1.5 text-xs font-mono"
                      >
                        <span className="text-gray-400 text-[10px] mr-1.5">{c.name.replace(/_/g, ' ')}:</span>
                        <span className="text-cyan-300 font-bold">{c.value.toFixed(1)}{c.unit}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Citations Buttons */}
              {msg.structured_payload?.citations?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <span className="text-[10px] font-bold tracking-wider uppercase text-gray-400 flex items-center gap-1 mb-2">
                    <FileText className="w-3.5 h-3.5 text-emerald-400" /> Evidence Citations
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.structured_payload.citations.map((cit, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedCitation(cit)}
                        className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-800/80 hover:bg-gray-700 text-emerald-400 border border-gray-700 rounded-md text-[11px] font-mono transition-all group"
                      >
                        <span>[Page {cit.page_number} - {cit.section || 'Filing'}]</span>
                        <ArrowUpRight className="w-3 h-3 text-gray-400 group-hover:text-emerald-400 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Validation Warnings */}
              {msg.structured_payload?.validation_warnings?.length > 0 && (
                <div className="mt-3 bg-amber-500/10 border border-amber-500/20 rounded-lg p-2.5 text-amber-300 text-xs flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[11px]">Audit Warning:</span>
                    <ul className="list-disc list-inside text-[11px] space-y-0.5 mt-0.5 text-amber-300/90">
                      {msg.structured_payload.validation_warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 text-gray-400 text-xs animate-pulse">
            <Bot className="w-5 h-5 text-emerald-400" />
            <span>Analyzing query, retrieving structured facts and generating grounded response...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Chips */}
      {messages.length <= 2 && (
        <div className="px-6 py-2 border-t border-gray-800/60 bg-[#0B0F19]/40 flex flex-wrap gap-2">
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              className="text-xs bg-gray-800/60 hover:bg-emerald-950/40 hover:border-emerald-700/50 border border-gray-700/50 text-gray-300 hover:text-emerald-300 px-3 py-1.5 rounded-full transition-all text-left"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input Bar */}
      <div className="p-4 border-t border-gray-800 bg-[#111827]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3"
        >
          <input
            id="chat-query-input"
            type="text"
            placeholder="Ask a question about profitability, drivers, or compare company periods..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 bg-[#0B0F19] border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
          <button
            id="chat-send-btn"
            type="submit"
            disabled={!input.trim() || loading}
            className="p-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl transition-all shadow-lg shadow-emerald-950/30"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Citation Details Modal */}
      <CitationModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
