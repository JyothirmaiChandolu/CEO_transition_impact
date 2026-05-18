import { TrendingUp, ArrowRight, Building2, Clock, BarChart3, Archive, Trophy } from 'lucide-react';
import { motion } from 'motion/react';
import type { ActionView } from '../App';

interface IndexSelectorProps {
  onSelectAction: (action: ActionView) => void;
}

const NAV_LINKS = [
  { label: 'Home', id: 'is-hero' },
  { label: 'Features', id: 'is-features' },
  { label: 'Overview', id: 'is-overview' },
  { label: 'About', id: 'is-about' },
];

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
}

const ACTIONS = [
  {
    key: 'archive' as ActionView,
    icon: Archive,
    title: 'Company Archive',
    description: 'Browse all companies with financial profiles, sector data, market cap, and more.',
    cta: 'Browse Archive',
  },
  {
    key: 'selector' as ActionView,
    icon: Building2,
    title: 'Start Analysis',
    description: 'Select a company and explore how CEO transitions impact stock performance with detailed metrics.',
    cta: 'Start Analysis',
  },
  {
    key: 'outlier-analysis' as ActionView,
    icon: BarChart3,
    title: 'Outlier Analysis',
    description: 'Identify statistical outlier CEOs and companies by sector using z-score analysis.',
    cta: 'Explore Outliers',
  },
  {
    key: 'rankings' as ActionView,
    icon: Trophy,
    title: 'Global Rankings',
    description: 'See top CEOs ranked by macro-adjusted stock impact and best companies by long-term returns.',
    cta: 'View Rankings',
  },
];

export function IndexSelector({ onSelectAction }: IndexSelectorProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sticky Nav */}
      <div style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 10 }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 2rem', height: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <img src="/logo.png" alt="Logo" style={{ height: 52, width: 'auto', display: 'block' }} />
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {NAV_LINKS.map((link) => (
              <motion.button
                key={link.id}
                onClick={() => scrollTo(link.id)}
                type="button"
                whileHover="hover"
                style={{ position: 'relative', padding: '0.5rem 1.25rem', fontSize: '1rem', fontWeight: 500, color: '#475569', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {link.label}
                <motion.span
                  variants={{ hover: { width: '100%' } }}
                  initial={{ width: 0 }}
                  transition={{ duration: 0.25 }}
                  style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: '#0f172a', display: 'block' }}
                />
              </motion.button>
            ))}
          </nav>
        </div>
      </div>

      {/* Hero / Action Selection */}
      <div id="is-hero" className="flex flex-col items-center px-6 py-12">
        <div className="text-center mb-10 w-full max-w-5xl">
          <div className="inline-flex items-center gap-2 bg-slate-200 text-slate-700 px-4 py-2 rounded-full mb-5 border border-slate-300">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-semibold uppercase tracking-wide">Leadership Impact Research</span>
          </div>
          <h1 className="text-5xl font-extrabold mb-3 text-slate-900 tracking-tight">
            CEO Performance Analysis
          </h1>
          <p className="text-lg text-slate-500 font-light">
            Choose an analysis type to get started
          </p>
        </div>

        {/* 4 Action Cards */}
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-6">
          {ACTIONS.map((action, i) => {
            const Icon = action.icon;
            return (
              <motion.div
                key={action.key}
                onClick={() => onSelectAction(action.key)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelectAction(action.key)}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20, delay: i * 0.07 }}
                whileHover={{ y: -4, boxShadow: '0 16px 32px rgba(0,0,0,0.10)' }}
                className="bg-white rounded-xl shadow-sm border border-slate-200 hover:border-slate-300 transition-colors cursor-pointer"
                style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', textAlign: 'left' }}
              >
                <div className="w-12 h-12 bg-slate-900 rounded-xl flex items-center justify-center text-white mb-5 flex-shrink-0">
                  <Icon className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2 w-full">{action.title}</h2>
                <p className="text-sm text-slate-500 leading-relaxed w-full" style={{ marginBottom: '2rem', flex: 1 }}>{action.description}</p>
                <div className="w-full flex items-center justify-center gap-2 bg-slate-900 text-white rounded-lg font-semibold text-sm hover:bg-slate-700 transition-colors" style={{ padding: '0.875rem 1.5rem' }}>
                  {action.cta}
                  <ArrowRight className="w-4 h-4" />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Feature Cards + Stats + About */}
      <div className="max-w-7xl mx-auto px-6 pb-16">
        {/* Feature Cards */}
        <div id="is-features">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4 text-slate-700">
                <Building2 className="w-6 h-6" />
              </div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">Company Selection</h3>
              <p className="text-slate-500 leading-relaxed">
                Choose from 237 companies across multiple sectors. Filter by industry, search by name or ticker symbol.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4 text-slate-700">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">30 Years of Data</h3>
              <p className="text-slate-500 leading-relaxed">
                Analyze stock performance around CEO transitions using daily OHLCV data from 1996-2026.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4 text-slate-700">
                <BarChart3 className="w-6 h-6" />
              </div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">Detailed Insights</h3>
              <p className="text-slate-500 leading-relaxed">
                Get comprehensive analysis including interactive stock charts, impact metrics, volatility assessment, and timeline views.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all">
              <div className="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center mb-4 text-white">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-3">Z-Score Calculations</h3>
              <p className="text-slate-500 text-sm leading-relaxed">
                Each CEO and company metric is standardized relative to their sector peers using z-scores. A composite score combines multiple dimensions of performance.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all">
              <div className="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center mb-4 text-white">
                <BarChart3 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-3">Sector-wise Outliers</h3>
              <p className="text-slate-500 text-sm leading-relaxed">
                Analysis is scoped per sector so comparisons are fair. Top and bottom 20% within each sector are flagged as outliers with strength ratings.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all">
              <div className="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center mb-4 text-white">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-3">Insightful Charts</h3>
              <p className="text-slate-500 text-sm leading-relaxed">
                Visual breakdowns of high and low performers within each sector, with percentile rankings and macro-economic context for every CEO transition.
              </p>
            </div>
          </div>
        </div>

        {/* Research Overview */}
        <div id="is-overview" className="bg-slate-900 rounded-xl p-12 text-white shadow-xl mb-16">
          <h2 className="text-center mb-10 text-2xl font-semibold tracking-wide">Research Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 border-t border-slate-700 pt-8">
            <div className="text-center">
              <div className="text-4xl font-bold mb-2 tracking-tight">1,200+</div>
              <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">CEO Transitions Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold mb-2 tracking-tight">237+</div>
              <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Companies with Transitions</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold mb-2 tracking-tight">2,500+</div>
              <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Total Companies Tracked</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold mb-2 tracking-tight">1996-2026</div>
              <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Analysis Period</div>
            </div>
          </div>
        </div>

        {/* About Section */}
        <div id="is-about" className="bg-white rounded-xl p-12 shadow-sm border border-slate-200">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-center mb-8 text-2xl font-bold text-slate-900">About This Project</h2>
            <p className="text-slate-600 text-lg leading-loose mb-10 text-center">
              This comprehensive analysis examines the relationship between CEO transitions and stock market performance. CEO transitions are identified from verified SEC 8-K filings and company announcements, combined with daily stock data to measure market impact. All transition dates have been web-researched and validated for accuracy.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
              <div className="flex items-start gap-4">
                <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                <div>
                  <h4 className="mb-1 font-bold text-slate-900">Verified CEO Transitions</h4>
                  <p className="text-sm text-slate-500">
                    CEO transitions validated from SEC 8-K filings, 10-K reports, and official announcements with web research verification
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                <div>
                  <h4 className="mb-1 font-bold text-slate-900">Historical Stock Data</h4>
                  <p className="text-sm text-slate-500">
                    Daily OHLCV stock data from 1996 to 2026 sourced from Yahoo Finance
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                <div>
                  <h4 className="mb-1 font-bold text-slate-900">Multi-Sector Coverage</h4>
                  <p className="text-sm text-slate-500">
                    Spanning Technology, Healthcare, Financials, Energy, Consumer, Industrials, and more
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                <div>
                  <h4 className="mb-1 font-bold text-slate-900">Interactive Analysis</h4>
                  <p className="text-sm text-slate-500">
                    Explore stock performance before and after each CEO transition with interactive charts
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
