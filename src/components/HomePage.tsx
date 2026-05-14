import { BarChart3, Building2, ArrowRight, Trophy, Archive, ArrowLeft } from 'lucide-react';
import { motion } from 'motion/react';

interface HomePageProps {
  onGetStarted: () => void;
  onOutlierAnalysis: () => void;
  onRankings: () => void;
  onArchive: () => void;
  onChangeIndex: () => void;
  indexName: string;
  stats: {
    totalCompanies: number;
    companiesWithTransitions: number;
    totalTransitions: number;
    dateRange: string;
  };
}

export function HomePage({ onGetStarted, onOutlierAnalysis, onRankings, onArchive, onChangeIndex, indexName, stats }: HomePageProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Top nav */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-3">
          <button
            onClick={onChangeIndex}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors font-medium text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Change Index
          </button>
          <div className="h-4 w-px bg-slate-300" />
          <span className="text-sm font-semibold text-slate-900">{indexName}</span>
        </div>
      </div>

      {/* 4 Action Cards */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center mb-10">
            <h1 className="text-5xl font-extrabold mb-6 text-slate-900 tracking-tight">
              CEO Performance Analysis
            </h1>

            <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-8 font-light leading-relaxed">
              Explore how leadership changes affect stock market performance.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Company Archive Card */}
              <motion.button
                onClick={(e) => { e.preventDefault(); onArchive(); }}
                type="button"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 18, delay: 0 }}
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                className="bg-white rounded-lg p-8 shadow-sm border-2 border-slate-900 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center justify-center mb-4 w-12 h-12 bg-slate-900 rounded-lg text-white">
                  <Archive className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Company Archive</h2>
                <p className="text-sm text-slate-600 mb-6 text-left">
                  Browse all companies with financial profiles, sector data, market cap, and more.
                </p>
                <span className="inline-flex items-center gap-2 bg-slate-900 text-white px-8 py-4 rounded-lg font-semibold text-base hover:bg-slate-700 transition-colors w-full justify-center">
                  Browse Archive
                  <ArrowRight className="w-5 h-5" />
                </span>
              </motion.button>

              {/* CEO Transition Analysis Card */}
              <motion.button
                onClick={(e) => { e.preventDefault(); onGetStarted(); }}
                type="button"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 18, delay: 0.1 }}
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                className="bg-white rounded-lg p-8 shadow-sm border-2 border-slate-900 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center justify-center mb-4 w-12 h-12 bg-slate-900 rounded-lg text-white">
                  <Building2 className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">CEO Transition Analysis</h2>
                <p className="text-sm text-slate-600 mb-6 text-left">
                  Select a company and explore how CEO transitions impact stock performance with detailed metrics and historical comparisons.
                </p>
                <span className="inline-flex items-center gap-2 bg-slate-900 text-white px-8 py-4 rounded-lg font-semibold text-base hover:bg-slate-700 transition-colors w-full justify-center">
                  Start Analysis
                  <ArrowRight className="w-5 h-5" />
                </span>
              </motion.button>

              {/* Outlier Analysis Card */}
              <motion.button
                onClick={(e) => { e.preventDefault(); onOutlierAnalysis(); }}
                type="button"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 18, delay: 0.2 }}
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                className="bg-white rounded-lg p-8 shadow-sm border-2 border-slate-900 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center justify-center mb-4 w-12 h-12 bg-slate-900 rounded-lg text-white">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Outlier Analysis</h2>
                <p className="text-sm text-slate-600 mb-6 text-left">
                  Identify statistical outlier CEOs and companies by sector using z-score analysis across multiple performance metrics.
                </p>
                <span className="inline-flex items-center gap-2 bg-slate-900 text-white px-8 py-4 rounded-lg font-semibold text-base hover:bg-slate-700 transition-colors w-full justify-center">
                  Explore Outliers
                  <ArrowRight className="w-5 h-5" />
                </span>
              </motion.button>

              {/* Global Rankings Card */}
              <motion.button
                onClick={(e) => { e.preventDefault(); onRankings(); }}
                type="button"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 18, delay: 0.3 }}
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                className="bg-white rounded-lg p-8 shadow-sm border-2 border-slate-900 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center justify-center mb-4 w-12 h-12 bg-slate-900 rounded-lg text-white">
                  <Trophy className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Global Rankings</h2>
                <p className="text-sm text-slate-600 mb-6 text-left">
                  See who leads: best CEOs ranked by macro-adjusted stock impact, and best companies by risk-adjusted long-term returns.
                </p>
                <span className="inline-flex items-center gap-2 bg-slate-900 text-white px-8 py-4 rounded-lg font-semibold text-base hover:bg-slate-700 transition-colors w-full justify-center">
                  View Rankings
                  <ArrowRight className="w-5 h-5" />
                </span>
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
