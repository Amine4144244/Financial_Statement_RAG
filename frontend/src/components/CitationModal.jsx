import React from 'react';
import { X, FileText, CheckCircle2 } from 'lucide-react';

export function CitationModal({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div 
        id="citation-modal"
        className="w-full max-w-lg bg-[#111827] border border-gray-700 rounded-xl shadow-2xl p-6 relative"
      >
        <button
          id="close-citation-modal-btn"
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-white">Source Citation Provenance</h3>
            <p className="text-xs text-gray-400">Document Page Verification</p>
          </div>
        </div>

        <div className="bg-[#0B0F19] rounded-lg p-4 border border-gray-800 space-y-2 mb-4 text-xs font-mono">
          <div className="flex justify-between">
            <span className="text-gray-500">Document ID:</span>
            <span className="text-gray-300">{citation.document_id || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Company / Fiscal Year:</span>
            <span className="text-emerald-400 font-semibold">{citation.company_id} · FY{citation.fiscal_year}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Report Page:</span>
            <span className="text-cyan-400 font-bold">Page {citation.page_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Section:</span>
            <span className="text-gray-300">{citation.section || 'Management Discussion'}</span>
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-400 font-medium uppercase tracking-wider block mb-2">
            Verified Excerpt Passage
          </label>
          <div className="bg-[#1F2937]/50 rounded-lg p-3 text-sm text-gray-200 border-l-4 border-emerald-500 italic max-h-48 overflow-y-auto leading-relaxed">
            "{citation.excerpt}"
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between pt-3 border-t border-gray-800 text-xs text-gray-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" /> Ground-truth anchored
          </span>
          <button
            id="dismiss-citation-btn"
            onClick={onClose}
            className="px-4 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded-md text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
