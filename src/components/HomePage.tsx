import { TrendingUp, BarChart3, Clock, Building2, ArrowRight } from 'lucide-react';

interface HomePageProps {
  onGetStarted: () => void;
  stats: {
    totalCompanies: number;
    companiesWithTransitions: number;
    totalTransitions: number;
    dateRange: string;
  };
}

export function HomePage({ onGetStarted, stats }: HomePageProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-slate-200 text-slate-700 px-4 py-2 rounded-full mb-6 border border-slate-300">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm font-semibold uppercase tracking-wide">Leadership Impact Research</span>
            </div>

            <h1 className="text-5xl font-extrabold mb-6 text-slate-900 tracking-tight">
              CEO Transition Impact Analysis
            </h1>

            <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-8 font-light leading-relaxed">
              Explore how leadership changes affect stock market performance. Analyze real SEC 10-K filing data and historical stock prices from S&P 500 companies spanning {stats.dateRange}.
            </p>

            <button
              onClick={(e) => {
                e.preventDefault();
                onGetStarted();
              }}
              type="button"
              className="relative z-50 inline-flex items-center justify-center bg-slate-900 hover:bg-slate-800 text-white px-8 py-4 text-lg font-medium rounded-lg shadow-md hover:shadow-lg transition-all cursor-pointer transform hover:-translate-y-0.5"
            >
              Start Analysis
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4 text-slate-700">
                <Building2 className="w-6 h-6" />
              </div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">Company Selection</h3>
              <p className="text-slate-500 leading-relaxed">
                Choose from {stats.totalCompanies} companies across multiple sectors. Filter by industry, search by name or ticker symbol.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors">
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4 text-slate-700">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="mb-3 text-lg font-bold text-slate-900">30 Years of Data</h3>
              <p className="text-slate-500 leading-relaxed">
                Analyze stock performance around CEO transitions using daily OHLCV data from {stats.dateRange}.
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

          {/* Stats Section */}
          <div className="bg-slate-900 rounded-xl p-12 text-white shadow-xl">
            <h2 className="text-center mb-10 text-2xl font-semibold tracking-wide">Research Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 border-t border-slate-700 pt-8">
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 tracking-tight">{stats.totalTransitions}</div>
                <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">CEO Transitions Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 tracking-tight">{stats.companiesWithTransitions}</div>
                <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Companies with Transitions</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 tracking-tight">{stats.totalCompanies}</div>
                <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Total Companies Tracked</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2 tracking-tight">{stats.dateRange}</div>
                <div className="text-slate-400 text-sm uppercase tracking-wider font-medium">Analysis Period</div>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="mt-16 bg-white rounded-xl p-12 shadow-sm border border-slate-200">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-center mb-8 text-2xl font-bold text-slate-900">About This Project</h2>
              <p className="text-slate-600 text-lg leading-loose mb-10 text-center">
                This comprehensive analysis examines the relationship between CEO transitions and stock market performance across S&P 500 companies. Using SEC 10-K filings to identify leadership changes and daily stock data to measure market impact, we provide insights into investor sentiment and long-term performance trends.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
                <div className="flex items-start gap-4">
                  <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                  <div>
                    <h4 className="mb-1 font-bold text-slate-900">SEC Filing Data</h4>
                    <p className="text-sm text-slate-500">
                      CEO transitions detected from real SEC 10-K annual filings across decades of company history
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-1.5 h-1.5 bg-slate-900 rounded-full mt-2.5 flex-shrink-0"></div>
                  <div>
                    <h4 className="mb-1 font-bold text-slate-900">Historical Stock Data</h4>
                    <p className="text-sm text-slate-500">
                      Daily OHLCV stock data from 1996 to 2025 sourced from Yahoo Finance
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
    </div>
  );
}
