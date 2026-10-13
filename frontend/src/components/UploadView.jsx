import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  CheckCircle,
  AlertCircle,
  Clock,
  FileCheck,
  Layers,
  Database,
  Sparkles,
  RefreshCw,
  Info,
  Check,
} from 'lucide-react';
import { apiClient } from '../api/client';

export function UploadView({ companies, activeCompany, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [companyId, setCompanyId] = useState(activeCompany || 'company_a');
  const [fiscalYear, setFiscalYear] = useState('2025');
  const [periodType, setPeriodType] = useState('FY');
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [userModified, setUserModified] = useState({ company: false, year: false, period: false });
  const [isDragging, setIsDragging] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    loadDocuments();
  }, [companyId]);

  const loadDocuments = async () => {
    try {
      const docs = await apiClient.getDocuments(companyId);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const runDetection = async (selectedFile) => {
    setDetecting(true);
    setDetectionResult(null);
    setUserModified({ company: false, year: false, period: false });

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await apiClient.detectDocumentMetadata(formData);
      setDetectionResult(res);

      if (res.detected_company_id) {
        setCompanyId(res.detected_company_id);
      }
      if (res.detected_fiscal_year) {
        setFiscalYear(String(res.detected_fiscal_year));
      }
      if (res.detected_period_type) {
        setPeriodType(res.detected_period_type);
      }
    } catch (err) {
      console.warn('Auto-detection notice:', err);
    } finally {
      setDetecting(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      runDetection(selected);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.type === 'application/pdf' || dropped.name.toLowerCase().endsWith('.pdf')) {
        setFile(dropped);
        setError(null);
        runDetection(dropped);
      } else {
        setError('Please select or drop a valid PDF document.');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF document to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', companyId);
    formData.append('fiscal_year', fiscalYear);
    formData.append('period_type', periodType);

    try {
      const res = await apiClient.uploadDocument(formData);
      setActiveJob({
        jobId: res.job_id,
        docId: res.document.id,
        stage: 'PARSING',
        progress: 20,
      });

      // Poll status
      pollJobStatus(res.document.id);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to upload document');
      setUploading(false);
    }
  };

  const pollJobStatus = (docId) => {
    const interval = setInterval(async () => {
      try {
        const status = await apiClient.getDocumentStatus(docId);
        setActiveJob((prev) => ({
          ...prev,
          stage: status.stage,
          progress: status.progress_percent,
          errorMessage: status.error_message,
        }));

        if (status.stage === 'COMPLETED' || status.stage === 'FAILED') {
          clearInterval(interval);
          setUploading(false);
          loadDocuments();
          if (onUploadSuccess && status.stage === 'COMPLETED') {
            onUploadSuccess();
          }
        }
      } catch {
        clearInterval(interval);
        setUploading(false);
      }
    }, 1500);
  };

  const stages = [
    { key: 'QUEUED', label: 'Queued', icon: Clock },
    { key: 'PARSING', label: 'PyMuPDF Layout Parsing', icon: Layers },
    { key: 'EXTRACTING_FACTS', label: 'Table & Fact Normalization', icon: Database },
    { key: 'INDEXING_VECTORS', label: 'ChromaDB Vector Indexing', icon: FileCheck },
    { key: 'COMPLETED', label: 'Processing Complete', icon: CheckCircle },
  ];

  return (
    <div className="space-y-6">
      {/* Upload Card */}
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl">
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Upload Financial Filing (PDF)</h2>
            <p className="text-xs text-gray-400">Ingest annual reports, balance sheets, and MD&A commentary</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all bg-[#0B0F19]/40 ${
              isDragging
                ? 'border-emerald-400 bg-emerald-500/10 scale-[1.01]'
                : file
                ? 'border-emerald-500/50 bg-emerald-950/10'
                : 'border-gray-700 hover:border-emerald-500/50'
            }`}
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-upload-input" className="cursor-pointer flex flex-col items-center">
              <UploadCloud
                className={`w-10 h-10 mb-3 transition-colors ${
                  file ? 'text-emerald-400' : 'text-emerald-400/80 animate-pulse'
                }`}
              />
              <span className="text-sm font-medium text-gray-300">
                {file ? (
                  <span className="text-emerald-300 font-semibold">{file.name}</span>
                ) : (
                  'Click to select annual report (PDF) or drag and drop'
                )}
              </span>
              <span className="text-xs text-gray-500 mt-1">SEC Form 10-K, Annual Reports up to 50MB</span>
            </label>
          </div>

          {/* Detecting Banner */}
          {detecting && (
            <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 flex items-center space-x-3 animate-pulse">
              <RefreshCw className="w-5 h-5 animate-spin text-cyan-400 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-white">Analyzing Filing Cover Page...</p>
                <p className="text-[11px] text-gray-400">
                  Detecting company name, reporting fiscal year, and filing period directly from the PDF...
                </p>
              </div>
            </div>
          )}

          {/* Smart Auto-Detect Confirmation Card */}
          {detectionResult && !detecting && (
            <div
              className={`p-4 rounded-xl border transition-all ${
                detectionResult.confidence === 'high'
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200'
                  : 'bg-amber-950/20 border-amber-500/40 text-amber-200'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start space-x-3">
                  <div
                    className={`p-2 rounded-lg mt-0.5 shrink-0 ${
                      detectionResult.confidence === 'high'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold tracking-tight text-white">
                        Smart Auto-Detect: {detectionResult.confidence === 'high' ? 'High Confidence Match' : 'Suggested Parameters'}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-semibold border ${
                          detectionResult.confidence === 'high'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                        }`}
                      >
                        {detectionResult.confidence} confidence
                      </span>
                    </div>

                    <p className="text-xs text-gray-300 leading-relaxed">
                      Identified{' '}
                      <strong className="text-white">
                        {detectionResult.detected_company_name || 'Target Company'}
                      </strong>{' '}
                      for reporting period{' '}
                      <strong className="text-white">
                        FY{detectionResult.detected_fiscal_year || fiscalYear} ({detectionResult.detected_period_type || periodType})
                      </strong>
                      .
                    </p>

                    {detectionResult.evidence && (
                      <p className="text-[11px] text-gray-400 font-mono mt-1">
                        Basis: {detectionResult.evidence}
                      </p>
                    )}

                    <p className="text-[11px] text-gray-400 mt-2 flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      <span>
                        Values pre-populated below. Confirm or customize before starting dual ingestion.
                      </span>
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setDetectionResult(null);
                    setCompanyId(activeCompany || 'company_a');
                    setFiscalYear('2025');
                    setPeriodType('FY');
                    setUserModified({ company: false, year: false, period: false });
                  }}
                  className="text-xs text-gray-400 hover:text-gray-200 px-2.5 py-1 rounded bg-gray-800/60 hover:bg-gray-800 transition-colors shrink-0"
                >
                  Reset
                </button>
              </div>
            </div>
          )}

          {/* Target Parameters Selection / Confirmation */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Target Company
                </label>
                {detectionResult?.detected_company_id && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      userModified.company
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}
                  >
                    {userModified.company ? 'Modified' : 'Auto-Detected'}
                  </span>
                )}
              </div>
              <select
                id="upload-company-select"
                value={companyId}
                onChange={(e) => {
                  setCompanyId(e.target.value);
                  setUserModified((prev) => ({ ...prev, company: true }));
                }}
                className={`w-full bg-[#0B0F19] border text-gray-200 text-sm rounded-lg px-3 py-2.5 focus:border-emerald-500 focus:outline-none transition-colors ${
                  detectionResult && !userModified.company
                    ? 'border-emerald-500/60'
                    : 'border-gray-700'
                }`}
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.ticker || c.id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Fiscal Year
                </label>
                {detectionResult?.detected_fiscal_year && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      userModified.year
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}
                  >
                    {userModified.year ? 'Modified' : 'Auto-Detected'}
                  </span>
                )}
              </div>
              <input
                id="upload-year-input"
                type="number"
                min="2000"
                max="2035"
                value={fiscalYear}
                onChange={(e) => {
                  setFiscalYear(e.target.value);
                  setUserModified((prev) => ({ ...prev, year: true }));
                }}
                className={`w-full bg-[#0B0F19] border text-gray-200 text-sm rounded-lg px-3 py-2.5 focus:border-emerald-500 focus:outline-none font-mono transition-colors ${
                  detectionResult && !userModified.year
                    ? 'border-emerald-500/60'
                    : 'border-gray-700'
                }`}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Period Type
                </label>
                {detectionResult?.detected_period_type && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      userModified.period
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}
                  >
                    {userModified.period ? 'Modified' : 'Auto-Detected'}
                  </span>
                )}
              </div>
              <select
                id="upload-period-select"
                value={periodType}
                onChange={(e) => {
                  setPeriodType(e.target.value);
                  setUserModified((prev) => ({ ...prev, period: true }));
                }}
                className={`w-full bg-[#0B0F19] border text-gray-200 text-sm rounded-lg px-3 py-2.5 focus:border-emerald-500 focus:outline-none transition-colors ${
                  detectionResult && !userModified.period
                    ? 'border-emerald-500/60'
                    : 'border-gray-700'
                }`}
              >
                <option value="FY">Full Fiscal Year (FY)</option>
                <option value="Q1">First Quarter (Q1)</option>
                <option value="Q2">Second Quarter (Q2)</option>
                <option value="Q3">Third Quarter (Q3)</option>
                <option value="Q4">Fourth Quarter (Q4)</option>
              </select>
            </div>
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              id="start-ingestion-btn"
              type="submit"
              disabled={uploading || detecting || !file}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-900/30 flex items-center space-x-2"
            >
              {uploading ? (
                <span>Processing Ingestion Pipeline...</span>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Confirm & Start Dual Ingestion</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Live Processing Pipeline Progress */}
        {activeJob && (
          <div className="mt-8 pt-6 border-t border-gray-800">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              Ingestion Pipeline Status: <span className="text-emerald-400 font-mono">{activeJob.stage}</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
              {stages.map((st, i) => {
                const isPassed =
                  st.key === 'QUEUED' ||
                  (activeJob.stage === 'PARSING' && i <= 1) ||
                  (activeJob.stage === 'EXTRACTING_FACTS' && i <= 2) ||
                  (activeJob.stage === 'INDEXING_VECTORS' && i <= 3) ||
                  activeJob.stage === 'COMPLETED';

                const isCurrent = activeJob.stage === st.key;
                const Icon = st.icon;

                return (
                  <div
                    key={st.key}
                    className={`p-3 rounded-xl border text-center transition-all ${
                      isPassed
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : isCurrent
                        ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400 animate-pulse'
                        : 'bg-gray-800/30 border-gray-800 text-gray-500'
                    }`}
                  >
                    <Icon className="w-5 h-5 mx-auto mb-1.5" />
                    <p className="text-[11px] font-medium leading-tight">{st.label}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Document Library */}
      <div className="glass-panel p-6 rounded-2xl border border-gray-800">
        <h3 className="text-base font-bold text-white mb-4">Indexed Document Filings</h3>
        {documents.length === 0 ? (
          <p className="text-xs text-gray-500">No documents uploaded yet for this company.</p>
        ) : (
          <div className="divide-y divide-gray-800 text-xs">
            {documents.map((d) => (
              <div key={d.id} className="py-3 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-gray-200">{d.original_filename}</span>
                  <span className="ml-2 text-gray-500">FY{d.fiscal_year} ({d.period_type})</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {d.status}
                  </span>
                  <span className="text-gray-500 text-[11px]">
                    {new Date(d.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
