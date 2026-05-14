import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, ExternalLink, Search, Download } from 'lucide-react';
import { loadCompanyArchive } from '../utils/api';
import type { IndexConfig, CompanyMetadata } from '../utils/types';

interface CompanyArchiveProps {
  index: IndexConfig;
  onBack: () => void;
}

function formatMarketCap(value: number | null): string {
  if (value == null) return '—';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  return `$${value.toLocaleString()}`;
}

function formatEmployees(value: number | null): string {
  if (value == null) return '—';
  return value.toLocaleString();
}

export function CompanyArchive({ index, onBack }: CompanyArchiveProps) {
  const [companies, setCompanies] = useState<CompanyMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    loadCompanyArchive(index.key).then((data) => {
      setCompanies(data);
      setLoading(false);
    });
  }, [index.key]);

  const sectors = useMemo(() => {
    const s = new Set(companies.map((c) => c.sector).filter(Boolean));
    return [...s].sort();
  }, [companies]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return companies.filter((c) => {
      const matchSearch =
        !q ||
        c.ticker.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q);
      return matchSearch && (!sectorFilter || c.sector === sectorFilter);
    });
  }, [companies, search, sectorFilter]);

  const downloadCSV = useCallback(() => {
    const header = ['Ticker', 'Company Name', 'Sector', 'Industry', 'Country', 'Employees', 'Market Cap', 'Website'];
    const lines = [
      header.join(','),
      ...filtered.map((c) =>
        [
          c.ticker,
          `"${c.name.replace(/"/g, '""')}"`,
          c.sector,
          `"${(c.industry || '').replace(/"/g, '""')}"`,
          c.country,
          c.employees ?? '',
          c.marketCap ?? '',
          c.website,
        ].join(',')
      ),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${index.key}_archive.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filtered, index.key]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.2 }}
      className="min-h-screen bg-slate-50 text-slate-900 font-sans"
    >
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center gap-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors font-medium"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <div className="h-5 w-px bg-slate-300" />
          <h1 className="text-lg font-bold text-slate-900">
            Company Archive — {index.name}
          </h1>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-32">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-slate-500 text-sm">Loading company archive...</p>
            </div>
          </div>
        ) : companies.length === 0 ? (
          <div className="text-center py-32">
            <p className="text-slate-500 text-base">
              Company metadata not yet fetched. Run{' '}
              <code className="bg-slate-200 px-2 py-0.5 rounded text-sm">
                fetch_company_metadata.py
              </code>{' '}
              for {index.name}.
            </p>
          </div>
        ) : (
          <>
            {/* Filters row */}
            <div className="flex flex-col sm:flex-row gap-3 mb-3 items-stretch sm:items-center">
              {/* Search */}
              <label
                htmlFor="archive-search"
                className="relative flex-1"
                style={{ display: 'flex', alignItems: 'center', minWidth: '0' }}
              >
                <Search
                  className="text-slate-400 pointer-events-none"
                  style={{ position: 'absolute', left: '0.75rem', width: '1rem', height: '1rem' }}
                />
                <input
                  id="archive-search"
                  type="text"
                  placeholder="Search by ticker or name..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{ paddingLeft: '2.25rem', paddingRight: '1rem', paddingTop: '0.625rem', paddingBottom: '0.625rem', fontSize: '0.875rem', lineHeight: '1.25rem' }}
                  className="w-full border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                />
              </label>

              {/* Sector filter */}
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                style={{ minWidth: '200px', paddingTop: '0.625rem', paddingBottom: '0.625rem', fontSize: '0.875rem' }}
                className="border border-slate-300 rounded-lg px-3 focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
              >
                <option value="">All Sectors</option>
                {sectors.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Count + Download row */}
            <div className="flex items-center justify-between mb-6">
              <span className="text-sm text-slate-500">
                {filtered.length} of {companies.length} companies
              </span>
              <button
                onClick={downloadCSV}
                style={{ minWidth: '10rem', paddingLeft: '1.75rem', paddingRight: '1.75rem' }}
                className="inline-flex items-center justify-center gap-2 bg-slate-900 text-white py-2 rounded-lg text-sm font-semibold hover:bg-slate-700 transition-colors whitespace-nowrap"
              >
                <Download className="w-4 h-4" />
                Download CSV
              </button>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm" style={{ minWidth: '1100px' }}>
                  <thead>
                    <tr className="bg-slate-900 text-white">
                      <th className="px-4 py-3 text-left font-semibold" style={{ width: '3rem' }}>#</th>
                      <th className="px-4 py-3 text-left font-semibold" style={{ width: '6rem' }}>Ticker</th>
                      <th className="px-4 py-3 text-left font-semibold" style={{ minWidth: '220px' }}>Company Name</th>
                      <th className="px-4 py-3 text-left font-semibold" style={{ minWidth: '160px' }}>Sector</th>
                      <th className="px-4 py-3 text-left font-semibold" style={{ minWidth: '200px' }}>Industry</th>
                      <th className="px-4 py-3 text-left font-semibold" style={{ width: '130px' }}>Country</th>
                      <th className="px-4 py-3 text-right font-semibold" style={{ width: '120px' }}>Employees</th>
                      <th className="px-4 py-3 text-right font-semibold" style={{ width: '130px' }}>Market Cap</th>
                      <th className="px-4 py-3 text-center font-semibold" style={{ width: '80px' }}>Website</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((company, i) => (
                      <tr
                        key={company.ticker}
                        className="border-t border-slate-100 hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-4 py-3 text-slate-400 font-medium">{i + 1}</td>
                        <td className="px-4 py-3 font-bold text-slate-900">{company.ticker}</td>
                        <td className="px-4 py-3 text-slate-700">
                          <span className="block truncate max-w-[220px]">{company.name}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{company.sector || '—'}</td>
                        <td className="px-4 py-3 text-slate-500">
                          <span className="block truncate max-w-[200px]">{company.industry || '—'}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-500">{company.country || '—'}</td>
                        <td className="px-4 py-3 text-right text-slate-600 tabular-nums">
                          {formatEmployees(company.employees)}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-slate-800 tabular-nums">
                          {formatMarketCap(company.marketCap)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {company.website ? (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center justify-center text-slate-500 hover:text-slate-900 transition-colors"
                              title={company.website}
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
