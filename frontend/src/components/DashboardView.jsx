import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  DollarSign,
  Percent,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '../api/client';

export function DashboardView({ activeCompany, companies, onNavigateToUpload }) {
  const [loading, setLoading] = useState(false);
  const [financialData, setFinancialData] = useState(null);

  const currentCompany = companies?.find((c) => c.id === activeCompany) || {
    id: activeCompany,
    name: activeCompany,
  };

  useEffect(() => {
    loadCompanyFinancials();
  }, [activeCompany]);

  const loadCompanyFinancials = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getCompanyFinancials(activeCompany);
      setFinancialData(data);
    } catch (err) {
      console.error('Failed to load company financials:', err);
      setFinancialData(null);
    } finally {
      setLoading(false);
    }
  };

  const facts = financialData?.facts || [];
  const calculations = financialData?.calculations || [];
  const hasData = facts.length > 0;

  // Extract available fiscal years sorted ascending
  const years = Array.from(new Set(facts.map((f) => f.fiscal_year))).sort((a, b) => a - b);
  const latestYear = years.length > 0 ? years[years.length - 1] : 2025;
  const priorYear = years.length > 1 ? years[years.length - 2] : null;

  // Helper value accessors
  const getFact = (yr, metricName) => {
    const f = facts.find((item) => item.fiscal_year === yr && item.metric === metricName);
    return f ? Number(f.value) : null;
  };

  const getCalc = (yr, calcName) => {
    const c = calculations.find((item) => item.fiscal_year === yr && item.name === calcName);
    return c ? Number(c.value) : null;
  };

  // KPI Metrics computation
  const latestRevenue = getFact(latestYear, 'revenue');
  const priorRevenue = priorYear ? getFact(priorYear, 'revenue') : null;
  const revenueGrowth =
    getCalc(latestYear, 'revenue_growth') ??
    (priorRevenue && latestRevenue ? ((latestRevenue - priorRevenue) / priorRevenue) * 100 : null);

  const latestNetIncome = getFact(latestYear, 'net_income');
  const priorNetIncome = priorYear ? getFact(priorYear, 'net_income') : null;
  const netIncomeGrowth =
    getCalc(latestYear, 'net_income_growth') ??
    (priorNetIncome && latestNetIncome ? ((latestNetIncome - priorNetIncome) / priorNetIncome) * 100 : null);

  const latestGrossProfit = getFact(latestYear, 'gross_profit');
  const latestOpIncome = getFact(latestYear, 'operating_income');

  const latestNetMargin =
    getCalc(latestYear, 'net_profit_margin') ??
    (latestRevenue ? (latestNetIncome / latestRevenue) * 100 : null);

  const latestOpMargin =
    getCalc(latestYear, 'operating_margin') ??
    (latestRevenue ? (latestOpIncome / latestRevenue) * 100 : null);

  const marginChangePp = getCalc(latestYear, 'net_margin_change_pp');

  // Formatters
  const formatM = (val) => {
    if (val == null) return '—';
    return `$${(val / 1e6).toFixed(1)}M`;
  };

  const formatCurrency = (val) => {
    if (val == null) return '—';
    return `$${Number(val).toLocaleString()}`;
  };

  const formatPct = (val) => {
    if (val == null) return '—';
    return `${Number(val).toFixed(1)}%`;
  };

  const formatPp = (val) => {
    if (val == null) return '—';
    const num = Number(val);
    return `${num > 0 ? '+' : ''}${num.toFixed(1)} pp`;
  };

  // Build dynamic chart dataset for Recharts
  const chartData = years.map((yr) => {
    const rev = getFact(yr, 'revenue') || 0;
    const ni = getFact(yr, 'net_income') || 0;
    const gp = getFact(yr, 'gross_profit') || 0;
    const oi = getFact(yr, 'operating_income') || 0;
    const npm = getCalc(yr, 'net_profit_margin') ?? (rev ? (ni / rev) * 100 : 0);
    const opm = getCalc(yr, 'operating_margin') ?? (rev ? (oi / rev) * 100 : 0);
    const gm = getCalc(yr, 'gross_margin') ?? (rev ? (gp / rev) * 100 : 0);

    return {
      year: `FY${yr}`,
      revenue: Number((rev / 1e6).toFixed(2)),
      net_income: Number((ni / 1e6).toFixed(2)),
      gross_profit: Number((gp / 1e6).toFixed(2)),
      operating_income: Number((oi / 1e6).toFixed(2)),
      net_profit_margin: Number(npm.toFixed(1)),
      operating_margin: Number(opm.toFixed(1)),
      gross_margin: Number(gm.toFixed(1)),
    };
  });

  // Table metric definitions
  const tableMetrics = [
    { key: 'revenue', label: 'Revenue (Total Net Sales)', isCurrency: true },
    { key: 'cost_of_revenue', label: 'Cost of Revenue (COGS)', isCurrency: true },
    { key: 'gross_profit', label: 'Gross Profit', isCurrency: true },
    { key: 'operating_expenses', label: 'Operating Expenses', isCurrency: true },
    { key: 'operating_income', label: 'Operating Income (EBIT)', isCurrency: true },
    { key: 'net_income', label: 'Net Income (Earnings)', isCurrency: true },
    { key: 'total_assets', label: 'Total Assets', isCurrency: true },
    { key: 'total_liabilities', label: 'Total Liabilities', isCurrency: true },
    { key: 'gross_margin', label: 'Gross Margin (%)', isRatio: true, calcKey: 'gross_margin' },
    { key: 'operating_margin', label: 'Operating Margin (%)', isRatio: true, calcKey: 'operating_margin' },
    { key: 'net_profit_margin', label: 'Net Profit Margin (%)', isRatio: true, calcKey: 'net_profit_margin' },
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4 text-center">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <p className="text-sm text-gray-400">Loading verified financials for {currentCompany.name}...</p>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-10 rounded-2xl border border-gray-800 text-center space-y-4">
          <div className="w-14 h-14 bg-gray-800/80 rounded-2xl flex items-center justify-center mx-auto text-gray-400 border border-gray-700/60">
            <FileSpreadsheet className="w-7 h-7 text-emerald-400" />
          </div>
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-bold text-white">No Ingested Financials for {currentCompany.name}</h3>
            <p className="text-xs text-gray-400 mt-2">
              The portfolio entity <span className="font-mono text-emerald-300 font-semibold">{activeCompany}</span> does not have parsed annual report or financial statement records in the PostgreSQL/SQLite database yet.
            </p>
          </div>
          {onNavigateToUpload && (
            <div className="pt-2">
              <button
                onClick={onNavigateToUpload}
                className="inline-flex items-center space-x-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-900/30 transition-all cursor-pointer"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Upload Report for {currentCompany.name}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI Highlight Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revenue Card */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              FY{latestYear} Revenue
            </span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold font-mono text-white">{formatM(latestRevenue)}</h3>
            {revenueGrowth != null ? (
              <span
                className={`inline-flex items-center text-xs font-semibold mt-1 ${
                  revenueGrowth >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {revenueGrowth >= 0 ? (
                  <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                ) : (
                  <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                )}
                {revenueGrowth >= 0 ? '+' : ''}
                {revenueGrowth.toFixed(1)}% YoY
              </span>
            ) : (
              <span className="text-xs text-gray-400 mt-1 block">Verified Ingestion</span>
            )}
          </div>
        </div>

        {/* Net Income Card */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              FY{latestYear} Net Income
            </span>
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold font-mono text-white">{formatM(latestNetIncome)}</h3>
            {netIncomeGrowth != null ? (
              <span
                className={`inline-flex items-center text-xs font-semibold mt-1 ${
                  netIncomeGrowth >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {netIncomeGrowth >= 0 ? (
                  <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                ) : (
                  <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                )}
                {netIncomeGrowth >= 0 ? '+' : ''}
                {netIncomeGrowth.toFixed(1)}% YoY
              </span>
            ) : (
              <span className="text-xs text-gray-400 mt-1 block">Verified Ingestion</span>
            )}
          </div>
        </div>

        {/* Margin Card */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Net Profit Margin
            </span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Percent className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold font-mono text-white">{formatPct(latestNetMargin)}</h3>
            <span className="inline-flex items-center text-xs font-semibold text-gray-400 mt-1">
              {marginChangePp != null
                ? `${formatPp(marginChangePp)} margin change`
                : latestOpMargin != null
                ? `Op Margin: ${formatPct(latestOpMargin)}`
                : 'Deterministic Ratio'}
            </span>
          </div>
        </div>

        {/* Audit Provenance Card */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Audit Provenance
            </span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-lg font-bold text-white">Verified</h3>
            <span className="text-xs text-gray-400">
              {facts.length} facts in PostgreSQL / SQLite
            </span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue & Net Income Bar Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Revenue & Net Income Comparison</h3>
              <p className="text-xs text-gray-400">Expressed in Millions (USD)</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="year" stroke="#9CA3AF" tickLine={false} />
                <YAxis stroke="#9CA3AF" tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#F3F4F6' }}
                />
                <Legend />
                <Bar dataKey="revenue" fill="#10B981" name="Revenue ($M)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="net_income" fill="#06B6D4" name="Net Income ($M)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Margin Trends Line Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Profitability Margin Trends</h3>
              <p className="text-xs text-gray-400">Deterministic Ratio %</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="year" stroke="#9CA3AF" tickLine={false} />
                <YAxis stroke="#9CA3AF" tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#F3F4F6' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="gross_margin"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  name="Gross Margin (%)"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="operating_margin"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Operating Margin (%)"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="net_profit_margin"
                  stroke="#10B981"
                  strokeWidth={2}
                  name="Net Margin (%)"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Side-by-Side Financial Variance Table */}
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
        <h3 className="text-base font-bold text-white mb-2">Annual Financial Statements & Variance Table</h3>
        <p className="text-xs text-gray-400 mb-4">
          Strict deterministic comparison distinguishing percentage change from percentage points for {currentCompany.name}
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 font-sans uppercase">
                <th className="py-3 px-4 font-semibold">Financial Metric</th>
                {priorYear && <th className="py-3 px-4 font-semibold text-right">FY{priorYear}</th>}
                <th className="py-3 px-4 font-semibold text-right">FY{latestYear}</th>
                {priorYear && <th className="py-3 px-4 font-semibold text-right">Absolute Variance</th>}
                {priorYear && <th className="py-3 px-4 font-semibold text-right">Relative Change</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 text-gray-300">
              {tableMetrics.map((item) => {
                const valPrior = item.isRatio
                  ? getCalc(priorYear, item.calcKey)
                  : getFact(priorYear, item.key);
                const valLatest = item.isRatio
                  ? getCalc(latestYear, item.calcKey)
                  : getFact(latestYear, item.key);

                if (valPrior == null && valLatest == null) return null;

                const absDiff = valPrior != null && valLatest != null ? valLatest - valPrior : null;
                const pctDiff =
                  valPrior != null && valLatest != null && valPrior !== 0
                    ? ((valLatest - valPrior) / Math.abs(valPrior)) * 100
                    : null;

                return (
                  <tr key={item.key} className="hover:bg-gray-800/20 transition-colors">
                    <td className="py-3 px-4 font-sans font-medium text-white">{item.label}</td>
                    {priorYear && (
                      <td className="py-3 px-4 text-right">
                        {item.isRatio ? formatPct(valPrior) : formatCurrency(valPrior)}
                      </td>
                    )}
                    <td className="py-3 px-4 text-right font-bold text-emerald-400">
                      {item.isRatio ? formatPct(valLatest) : formatCurrency(valLatest)}
                    </td>
                    {priorYear && (
                      <td className="py-3 px-4 text-right">
                        {absDiff != null ? (
                          <span
                            className={
                              absDiff > 0
                                ? 'text-emerald-400'
                                : absDiff < 0
                                ? 'text-red-400'
                                : 'text-gray-400'
                            }
                          >
                            {absDiff > 0 ? '+' : ''}
                            {item.isRatio ? formatPp(absDiff) : formatCurrency(absDiff)}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    )}
                    {priorYear && (
                      <td className="py-3 px-4 text-right font-semibold">
                        {item.isRatio ? (
                          absDiff != null ? (
                            <span className={absDiff === 0 ? 'text-gray-400' : absDiff > 0 ? 'text-emerald-400' : 'text-red-400'}>
                              {formatPp(absDiff)} {absDiff === 0 ? '(Constant)' : ''}
                            </span>
                          ) : (
                            '—'
                          )
                        ) : pctDiff != null ? (
                          <span className={pctDiff >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                            {pctDiff >= 0 ? '+' : ''}
                            {pctDiff.toFixed(1)}%
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
