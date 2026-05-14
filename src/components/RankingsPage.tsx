import { useState, useEffect, useMemo } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, Trophy, TrendingUp, TrendingDown } from 'lucide-react';
import { loadCEORankings } from '../utils/api';
import { formatDateShort } from '../utils/api';
import type { Company, CEOTransition, CEORankingResult } from '../utils/types';
import { MetricTooltip } from './MetricTooltip';

interface RankingsPageProps {
  companies: Company[];
  onBack: () => void;
  onSelectCompany: (company: Company, transition: CEOTransition) => void;
  index: string;
}

const SECTOR_ICONS: Record<string, string> = {
  'Information Technology': '💻',
  'Technology': '💻',
  'Health Care': '🏥',
  'Healthcare': '🏥',
  'Financials': '💰',
  'Financial Services': '💰',
  'Energy': '⚡',
  'Consumer Discretionary': '🛒',
  'Consumer Cyclical': '🛒',
  'Consumer Staples': '🧴',
  'Consumer Defensive': '🧴',
  'Communication Services': '📡',
  'Industrials': '🏭',
  'Materials': '⚗️',
  'Basic Materials': '⚗️',
  'Real Estate': '🏢',
  'Utilities': '⚙️',
};

export function RankingsPage({ companies, onBack, onSelectCompany, index }: RankingsPageProps) {
  const [rankings, setRankings] = useState<CEORankingResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [macroAdjusted, setMacroAdjusted] = useState(true);

  useEffect(() => {
    setSelectedSector(null);
    const fetchRankings = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await loadCEORankings(index, 500, macroAdjusted);
        setRankings(data?.top_ceos || []);
      } catch (err) {
        console.error('Error loading rankings:', err);
        setError('Failed to load rankings. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchRankings();
  }, [index, macroAdjusted]);

  // Get unique sectors from rankings (exclude empty/unknown)
  const sectors = useMemo(() => {
    const sectorSet = new Set<string>();
    rankings.forEach(r => {
      if (r.sector && r.sector !== 'Unknown') sectorSet.add(r.sector);
    });
    return Array.from(sectorSet).sort();
  }, [rankings]);

  // Filter rankings by sector and re-rank within sector
  const filteredRankings = useMemo(() => {
    const filtered = selectedSector
      ? rankings.filter(r => r.sector === selectedSector)
      : rankings;
    return filtered.map((r, idx) => ({ ...r, globalRank: r.rank, rank: idx + 1 }));
  }, [rankings, selectedSector]);

  const handleSeeAnalysis = (ranking: CEORankingResult) => {
    const company = companies.find(c => c.ticker === ranking.ticker);
    if (company) {
      const transition = company.transitions.find(t => t.transitionDate === ranking.transition_date);
      if (transition) {
        onSelectCompany(company, transition);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading transition rankings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-600 font-medium mb-2">{error}</p>
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className="min-h-screen bg-slate-50"
    >
      {/* Header */}
      <div className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              CEO Transition Rankings
            </h1>
            <p className="text-sm text-slate-600">All {filteredRankings.length} transitions ranked by impact</p>
          </div>
        </div>
      </div>

      {/* Stats Banner */}
      <div className="bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-sm opacity-75 uppercase tracking-wider">Total Transitions</div>
              <div className="text-3xl font-bold">{rankings.length}</div>
            </div>
            <div>
              <div className="text-sm opacity-75 uppercase tracking-wider">Data Period</div>
              <div className="text-3xl font-bold">1996–2026</div>
            </div>
            <div>
              <div className="text-sm opacity-75 uppercase tracking-wider">Methodology</div>
              <div className="text-lg font-semibold">Impact Score</div>
            </div>
            <div>
              <div className="text-sm opacity-75 uppercase tracking-wider">Scoring</div>
              <div className="text-lg font-semibold">Macro-Adjusted</div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Filter Bar */}
        <div className="flex flex-col gap-4 mb-8">
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block mb-2">
              Filter by Sector
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedSector(null)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedSector === null
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                All Sectors
              </button>
              {sectors.map(sector => (
                <button
                  key={sector}
                  onClick={() => setSelectedSector(sector)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    selectedSector === sector
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {SECTOR_ICONS[sector] || ''} {sector}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block mb-2">
              Scoring Method
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setMacroAdjusted(true)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  macroAdjusted
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                Macro-Adjusted
              </button>
              <button
                onClick={() => setMacroAdjusted(false)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  !macroAdjusted
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                Raw Score
              </button>
            </div>
          </div>
        </div>

        {/* Rankings Table */}
        {filteredRankings.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Rank</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">CEO</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Sector</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Transition Date</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-slate-600 uppercase">
                    <span className="inline-flex items-center gap-1">
                      1-Year Return
                      <MetricTooltip text="Stock price percentage change over the full first year after the CEO transition. Positive = the stock rose; negative = it declined." position="top" />
                    </span>
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-slate-600 uppercase">
                    <span className="inline-flex items-center gap-1">
                      90-Day Return
                      <MetricTooltip text="Stock price change in the first 90 days after the transition. Reflects the market's near-term reaction to the incoming CEO." position="top" />
                    </span>
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-slate-600 uppercase">
                    <span className="inline-flex items-center gap-1">
                      Score
                      <MetricTooltip text="Composite impact score combining 35% 1-year return + 30% 90-day return + 20% low-volatility bonus + 15% tenure efficiency. Macro-adjusted scores account for recession context." position="top" />
                    </span>
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-bold text-slate-600 uppercase">Action</th>
                </tr>
              </thead>
              <tbody key={selectedSector ?? 'all'} className="divide-y divide-slate-200">
                {filteredRankings.map((ranking) => (
                  <tr
                    key={`${ranking.ticker}-${ranking.transition_date}`}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <span className="font-bold text-slate-900">#{ranking.rank}</span>
                      {selectedSector && (
                        <div className="text-xs text-slate-400">global #{(ranking as any).globalRank}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{ranking.ceo_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{ranking.company_name}</div>
                      <div className="text-xs text-slate-500">{ranking.ticker}</div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <span className="text-sm">{SECTOR_ICONS[ranking.sector] || ''} {ranking.sector}</span>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <span className="text-sm">{formatDateShort(ranking.transition_date)}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {ranking.impact_1year_pct >= 0 ? (
                          <TrendingUp className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-600" />
                        )}
                        <span
                          className={`font-semibold ${
                            ranking.impact_1year_pct >= 0 ? 'text-emerald-600' : 'text-red-600'
                          }`}
                        >
                          {ranking.impact_1year_pct >= 0 ? '+' : ''}{ranking.impact_1year_pct.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span
                        className={`font-semibold ${
                          ranking.impact_90days_pct >= 0 ? 'text-emerald-600' : 'text-red-600'
                        }`}
                      >
                        {ranking.impact_90days_pct >= 0 ? '+' : ''}{ranking.impact_90days_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div>
                        <div className="font-bold text-slate-900">{ranking.composite_score.toFixed(2)}</div>
                        <div className="text-xs text-slate-500 mt-1">{ranking.macro_context}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleSeeAnalysis(ranking)}
                        className="px-3 py-1 bg-slate-900 text-white text-xs font-medium rounded hover:bg-slate-800 transition-colors"
                      >
                        See Analysis
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filteredRankings.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <p className="text-slate-500">No transitions found for the selected sector.</p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
