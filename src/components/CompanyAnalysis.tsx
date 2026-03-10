import { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { ArrowLeft, Calendar, User, TrendingUp, TrendingDown, Activity, DollarSign, Award, BookOpen, Clock } from 'lucide-react';
import { StockChart } from './StockChart';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { motion } from 'motion/react';
import { getStockDataAroundTransition, calculateTransitionMetrics, formatDate, formatDateShort } from '../utils/dataLoader';
import type { Company, CEOTransition, StockData } from '../utils/types';

interface CompanyAnalysisProps {
  company: Company;
  transition: CEOTransition;
  stockData: StockData | null;
  stockLoading: boolean;
  onBack: () => void;
  onChangeSelection: () => void;
}

type TimeRange = '6m' | '1y' | '2y' | '5y';

export function CompanyAnalysis({ company, transition, stockData, stockLoading, onBack, onChangeSelection }: CompanyAnalysisProps) {
  const [selectedRange, setSelectedRange] = useState<TimeRange>('1y');

  const daysMap: Record<TimeRange, number> = { '6m': 180, '1y': 365, '2y': 730, '5y': 1825 };

  // Get chart data around transition
  const chartData = useMemo(() => {
    if (!stockData) return [];
    const days = daysMap[selectedRange];
    return getStockDataAroundTransition(stockData.data, transition.transitionDate, days, days);
  }, [stockData, transition.transitionDate, selectedRange]);

  // Calculate metrics
  const metrics = useMemo(() => {
    if (!stockData) return null;
    return calculateTransitionMetrics(stockData.data, transition.transitionDate);
  }, [stockData, transition.transitionDate]);

  const isPositive = metrics ? (metrics.impact90Days ?? 0) >= 0 : true;
  const impactValue = metrics?.impact90Days ?? 0;

  // Build timeline
  const timeline = [
    {
      date: transition.filingBefore,
      event: 'Last Filing (Previous CEO)',
      details: `${transition.previousCEO} signed the 10-K filing`,
      type: 'neutral'
    },
    {
      date: transition.transitionDate,
      event: 'Estimated Transition',
      details: `${transition.newCEO} takes over as CEO`,
      type: 'highlight'
    },
    {
      date: transition.filingAfter,
      event: 'First Filing (New CEO)',
      details: `${transition.newCEO} signed the 10-K filing`,
      type: 'info'
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-slate-50 font-sans"
    >
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="bg-slate-900 text-white"
      >
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-6">
            <Button
              onClick={onBack}
              variant="ghost"
              className="text-slate-300 hover:text-white hover:bg-slate-800"
              size="sm"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
            <Button
              onClick={onChangeSelection}
              variant="outline"
              className="bg-transparent border-slate-600 text-slate-300 hover:text-white hover:bg-slate-800"
              size="sm"
            >
              Change Selection
            </Button>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center font-bold text-lg">
                  {company.ticker}
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">{company.name}</h1>
                  <div className="text-slate-400 text-sm">{company.sector}</div>
                </div>
              </div>
              <div className="space-y-2 mt-4">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300 text-sm">Transition: ~{formatDate(transition.transitionDate)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <User className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300 text-sm">{transition.previousCEO} → {transition.newCEO}</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <div className="text-sm text-slate-400 mb-2 uppercase tracking-wide font-medium">90-Day Post-Transition Impact</div>
              {stockLoading ? (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 border-2 border-slate-600 border-t-white rounded-full animate-spin"></div>
                  <span className="text-slate-400">Calculating...</span>
                </div>
              ) : metrics?.impact90Days !== null ? (
                <div className="flex items-center gap-3">
                  <div className="text-5xl font-bold tracking-tight">
                    {isPositive ? '+' : ''}{impactValue.toFixed(1)}%
                  </div>
                  <div className={`p-2 rounded-lg ${isPositive ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/50' : 'bg-red-900/30 text-red-400 border border-red-800/50'}`}>
                    {isPositive ? <TrendingUp className="w-6 h-6" /> : <TrendingDown className="w-6 h-6" />}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500">Insufficient data</div>
              )}
              {metrics?.priceAtTransition && (
                <div className="mt-3 text-sm text-slate-400">
                  Price at transition: ${metrics.priceAtTransition.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full max-w-2xl grid-cols-3 bg-slate-200 p-1 rounded-lg">
            <TabsTrigger value="overview" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-slate-600">Overview</TabsTrigger>
            <TabsTrigger value="timeline" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-slate-600">Timeline</TabsTrigger>
            <TabsTrigger value="insights" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-slate-600">Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* CEO Transition Info */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm"
            >
              <h3 className="mb-4 text-lg font-bold text-slate-900">Leadership Transition Profile</h3>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-4 p-5 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-center gap-2 mb-2">
                    <User className="w-4 h-4 text-slate-500" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Outgoing CEO</span>
                  </div>
                  <div>
                    <div className="font-bold text-xl text-slate-900">{transition.previousCEO}</div>
                    <div className="text-sm text-slate-500 mt-2 font-mono">
                      Last 10-K filing: {formatDateShort(transition.filingBefore)}
                    </div>
                  </div>
                </div>

                <div className="space-y-4 p-5 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center gap-2 mb-2">
                    <User className="w-4 h-4 text-slate-800" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Incoming CEO</span>
                  </div>
                  <div>
                    <div className="font-bold text-xl text-slate-900">{transition.newCEO}</div>
                    <div className="text-sm text-slate-500 mt-2 font-mono">
                      First 10-K filing: {formatDateShort(transition.filingAfter)}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Stock Chart with Time Range Selector */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              {/* Time Range Selector */}
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm text-slate-500 font-medium">Time Range:</span>
                {(['6m', '1y', '2y', '5y'] as TimeRange[]).map(range => (
                  <button
                    key={range}
                    onClick={() => setSelectedRange(range)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      selectedRange === range
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {range === '6m' ? '6 Months' : range === '1y' ? '1 Year' : range === '2y' ? '2 Years' : '5 Years'}
                  </button>
                ))}
              </div>

              {stockLoading ? (
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center justify-center py-16">
                    <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-900 rounded-full animate-spin mr-3"></div>
                    <span className="text-slate-500">Loading stock data...</span>
                  </div>
                </div>
              ) : (
                <StockChart
                  data={chartData}
                  transitionDate={transition.transitionDate}
                  companyName={company.name}
                  ticker={company.ticker}
                />
              )}
            </motion.div>

            {/* Key Metrics */}
            {metrics && (
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-1 md:grid-cols-4 gap-6"
              >
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                    <DollarSign className="w-4 h-4" />
                    Price at Transition
                  </div>
                  <div className="text-3xl font-bold mb-1 text-slate-900">
                    {metrics.priceAtTransition ? `$${metrics.priceAtTransition.toFixed(2)}` : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-500">Adjusted close</div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                    <TrendingUp className="w-4 h-4" />
                    1-Year Impact
                  </div>
                  <div className={`text-3xl font-bold mb-1 ${(metrics.impact1Year ?? 0) >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                    {metrics.impact1Year !== null ? `${metrics.impact1Year >= 0 ? '+' : ''}${metrics.impact1Year.toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-500">Post-transition</div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                    <Activity className="w-4 h-4" />
                    Volatility
                  </div>
                  <div className="text-3xl font-bold mb-1 text-slate-900">
                    {metrics.volatilityLevel}
                  </div>
                  <div className="text-xs text-slate-500">{metrics.volatility.toFixed(1)}% annualized</div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                    <Calendar className="w-4 h-4" />
                    Pre-Transition Trend
                  </div>
                  <div className={`text-3xl font-bold mb-1 ${(metrics.preTransitionTrend ?? 0) >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                    {metrics.preTransitionTrend !== null ? `${metrics.preTransitionTrend >= 0 ? '+' : ''}${metrics.preTransitionTrend.toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-500">90 days before</div>
                </div>
              </motion.div>
            )}
          </TabsContent>

          <TabsContent value="timeline">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="space-y-8"
            >
              {/* Horizontal Timeline */}
              <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 mb-8 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-slate-500" />
                  Transition Timeline
                </h3>

                <div className="relative pt-4 pb-8 overflow-x-auto">
                  <div className="absolute top-[27px] left-0 right-0 h-0.5 bg-slate-200 min-w-[500px]" />

                  <div className="flex justify-between min-w-[500px] gap-4 relative">
                    {timeline.map((event, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 * index }}
                        className="flex flex-col items-center w-48 relative group cursor-default"
                      >
                        <motion.div
                          whileHover={{ scale: 1.2 }}
                          className={`w-6 h-6 rounded-full border-4 z-10 bg-white transition-all duration-300 mb-4 flex items-center justify-center ${
                            event.type === 'highlight' ? 'border-amber-400' :
                            event.type === 'info' ? 'border-blue-400' :
                            'border-slate-300'
                          }`}
                        >
                          <div className={`w-2 h-2 rounded-full ${
                            event.type === 'highlight' ? 'bg-amber-500' :
                            event.type === 'info' ? 'bg-blue-500' :
                            'bg-slate-400'
                          }`} />
                        </motion.div>

                        <div className="text-center">
                          <div className="text-xs font-mono font-medium text-slate-500 mb-1">{formatDate(event.date)}</div>
                          <h4 className="text-sm font-bold text-slate-900 mb-1">{event.event}</h4>
                          <p className="text-xs text-slate-500 leading-tight">{event.details}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>

              {/* All transitions for this company */}
              {company.transitions.length > 1 && (
                <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                  <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                    <User className="w-5 h-5 text-slate-500" />
                    All CEO Transitions at {company.name}
                  </h3>
                  <div className="space-y-4">
                    {company.transitions.map((t, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-4 rounded-lg border ${
                          t === transition ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className="text-sm font-mono text-slate-500">{formatDateShort(t.transitionDate)}</div>
                          <div>
                            <div className="text-sm font-medium text-slate-900">
                              {t.previousCEO} → {t.newCEO}
                            </div>
                          </div>
                        </div>
                        {t === transition && (
                          <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full font-medium">Current</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </TabsContent>

          <TabsContent value="insights">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="space-y-6"
            >
              <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                <h3 className="mb-8 text-xl font-bold text-slate-900">Analysis & Insights</h3>
                <div className="grid gap-8">
                  <div className="flex gap-6 group">
                    <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-6 h-6 text-slate-700" />
                    </div>
                    <div className="flex-1">
                      <h4 className="mb-2 text-lg font-bold text-slate-900">Transition Overview</h4>
                      <div className="text-slate-600 leading-relaxed text-base">
                        The CEO transition at {company.name} from {transition.previousCEO} to {transition.newCEO} was identified
                        through SEC 10-K filing records. The last filing signed by {transition.previousCEO} was on {formatDate(transition.filingBefore)},
                        and the first filing signed by {transition.newCEO} was on {formatDate(transition.filingAfter)}.
                        The transition is estimated to have occurred around {formatDate(transition.transitionDate)}.
                      </div>
                    </div>
                  </div>

                  {metrics && (
                    <div className="flex gap-6 group">
                      <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <TrendingUp className="w-6 h-6 text-slate-700" />
                      </div>
                      <div className="flex-1">
                        <h4 className="mb-2 text-lg font-bold text-slate-900">Market Impact</h4>
                        <div className="text-slate-600 leading-relaxed text-base">
                          {metrics.impact90Days !== null ? (
                            <>
                              In the 90 days following the transition, {company.name}'s stock {metrics.impact90Days >= 0 ? 'increased' : 'decreased'} by{' '}
                              <span className={`font-bold ${metrics.impact90Days >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                                {Math.abs(metrics.impact90Days).toFixed(1)}%
                              </span>.
                              {metrics.impact1Year !== null && (
                                <> Over the full year, the stock {metrics.impact1Year >= 0 ? 'gained' : 'lost'}{' '}
                                  <span className={`font-bold ${metrics.impact1Year >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                                    {Math.abs(metrics.impact1Year).toFixed(1)}%
                                  </span>.
                                </>
                              )}
                              {' '}The annualized volatility around the transition period was {metrics.volatility.toFixed(1)}% ({metrics.volatilityLevel} risk).
                            </>
                          ) : (
                            'Insufficient stock data available to calculate the market impact for this transition period.'
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-6 group">
                    <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Award className="w-6 h-6 text-slate-700" />
                    </div>
                    <div className="flex-1">
                      <h4 className="mb-2 text-lg font-bold text-slate-900">Data Sources</h4>
                      <div className="text-slate-600 leading-relaxed text-base">
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                          <li>CEO information sourced from SEC 10-K annual filings (EDGAR database)</li>
                          <li>Stock data: Daily adjusted close prices from Yahoo Finance ({company.ticker})</li>
                          <li>Transition date estimated as midpoint between consecutive 10-K filings with different CEOs</li>
                          <li>Impact metrics calculated using adjusted close prices to account for splits and dividends</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary Card */}
              {metrics && (
                <div className="bg-slate-900 rounded-xl p-8 text-white shadow-xl">
                  <h3 className="mb-4 text-xl font-bold">Executive Summary</h3>
                  <p className="text-slate-300 mb-6 text-lg leading-relaxed">
                    The leadership transition at {company.name} ({company.ticker}) from {transition.previousCEO} to {transition.newCEO}{' '}
                    {metrics.impact90Days !== null ? (
                      <>
                        resulted in a{' '}
                        <span className={metrics.impact90Days >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                          {Math.abs(metrics.impact90Days).toFixed(1)}% {metrics.impact90Days >= 0 ? 'increase' : 'decline'}
                        </span>{' '}
                        in stock price over 90 days.
                      </>
                    ) : (
                      'occurred during a period with limited available stock data.'
                    )}
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-slate-700">
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide font-bold">90-Day Impact</div>
                      <div className="font-bold text-xl">
                        {metrics.impact90Days !== null ? `${metrics.impact90Days >= 0 ? '+' : ''}${metrics.impact90Days.toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide font-bold">Risk Profile</div>
                      <div className="font-bold text-xl">{metrics.volatilityLevel}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide font-bold">Sector</div>
                      <div className="font-bold text-xl">{company.sector}</div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}
