import { useState, useEffect, useMemo } from 'react';
import { TrendingDown, TrendingUp, AlertCircle, BarChart3, Zap } from 'lucide-react';
import { loadRecessionAnalysis, loadIndexData } from '../utils/api';
import type { RecessionImpactAnalysis } from '../utils/types';

interface RecessionBenchmarkProps {
  transitionDate: string;
  companyTicker: string;
  stockData?: any;
}

export function RecessionBenchmark({ transitionDate, companyTicker, stockData }: RecessionBenchmarkProps) {
  const [analysis, setAnalysis] = useState<RecessionImpactAnalysis | null>(null);
  const [indexData, setIndexData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analysisData, indexDataTemp] = await Promise.all([
          loadRecessionAnalysis(),
          loadIndexData('RUT')
        ]);
        setAnalysis(analysisData);
        setIndexData(indexDataTemp);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Determine if transition was during recession
  const transitionInRecession = useMemo(() => {
    if (!analysis || !transitionDate) return null;
    const transDate = new Date(transitionDate);

    for (const recession of analysis.recessions) {
      const startDate = new Date(recession.period.start);
      const endDate = new Date(recession.period.end);
      if (transDate >= startDate && transDate <= endDate) {
        return recession;
      }
    }
    return null;
  }, [analysis, transitionDate]);

  // Find company stock price at transition date
  const companyPriceAtTransition = useMemo(() => {
    if (!stockData?.data) return null;
    const transitionDate_obj = new Date(transitionDate);

    const closest = stockData.data.reduce((prev: any, curr: any) => {
      const prevDiff = Math.abs(new Date(prev.date).getTime() - transitionDate_obj.getTime());
      const currDiff = Math.abs(new Date(curr.date).getTime() - transitionDate_obj.getTime());
      return currDiff < prevDiff ? curr : prev;
    });

    return closest;
  }, [stockData, transitionDate]);

  // Find index price at transition date
  const indexPriceAtTransition = useMemo(() => {
    if (!indexData?.data) return null;
    const transitionDate_obj = new Date(transitionDate);

    const closest = indexData.data.reduce((prev: any, curr: any) => {
      const prevDiff = Math.abs(new Date(prev.date).getTime() - transitionDate_obj.getTime());
      const currDiff = Math.abs(new Date(curr.date).getTime() - transitionDate_obj.getTime());
      return currDiff < prevDiff ? curr : prev;
    });

    return closest;
  }, [indexData, transitionDate]);

  // Calculate relative performance during recession
  const relativePerformance = useMemo(() => {
    if (!transitionInRecession || !companyPriceAtTransition || !indexPriceAtTransition || !stockData?.data) return null;

    const recessEndDate = new Date(transitionInRecession.period.end);

    // Find company stock value at recession end
    const companyAtEnd = stockData.data
      .filter((d: any) => new Date(d.date) <= recessEndDate)
      .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime())[0];

    // Find index value at recession end
    const indexAtEnd = indexData?.data
      ?.filter((d: any) => new Date(d.date) <= recessEndDate)
      .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime())[0];

    if (!companyAtEnd || !indexAtEnd) return null;

    const companyDecline = ((companyAtEnd.close - companyPriceAtTransition.close) / companyPriceAtTransition.close) * 100;
    const indexDecline = ((indexAtEnd.close - indexPriceAtTransition.close) / indexPriceAtTransition.close) * 100;
    const outperformance = companyDecline - indexDecline;

    return {
      companyStart: companyPriceAtTransition.close,
      companyEnd: companyAtEnd.close,
      companyDecline,
      indexStart: indexPriceAtTransition.close,
      indexEnd: indexAtEnd.close,
      indexDecline,
      outperformance,
      betterPerformer: outperformance > 0 ? 'company' : 'index'
    };
  }, [transitionInRecession, companyPriceAtTransition, indexPriceAtTransition, stockData, indexData]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 rounded w-1/3"></div>
          <div className="h-20 bg-slate-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <p className="text-slate-500 text-center py-8">No analysis data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200 p-6 bg-gradient-to-r from-slate-900 to-slate-800">
        <div className="flex items-center gap-3 mb-3">
          <BarChart3 className="w-6 h-6 text-white" />
          <h3 className="text-xl font-bold text-white">Economic Impact Attribution</h3>
        </div>
        <p className="text-base text-slate-200">Analyze CEO transition impact during economic cycles</p>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-6">
        {/* Recession Status */}
        <div className="border rounded-lg p-6 bg-gradient-to-br from-slate-50 to-blue-50">
          <h4 className="font-semibold text-slate-900 text-base mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-600" />
            Transition Period Status
          </h4>

          {transitionInRecession ? (
            <div className="space-y-3">
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-1" />
                  <div>
                    <h5 className="font-semibold text-orange-900 text-sm">
                      ⚠️ CEO Transition During {transitionInRecession.name}
                    </h5>
                    <p className="text-sm text-orange-800 mt-2">
                      The CEO transition occurred during a recession period ({transitionInRecession.period.start} to{' '}
                      {transitionInRecession.period.end}), lasting {transitionInRecession.period.duration_months} months.
                    </p>
                  </div>
                </div>
              </div>

              {/* Comparison Analysis */}
              {relativePerformance && (
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Company Performance */}
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <div className="text-xs text-slate-600 font-semibold uppercase mb-3">Company Stock Performance</div>
                    <div className="space-y-2">
                      <div>
                        <div className="text-xs text-slate-600">At Transition:</div>
                        <div className="text-2xl font-bold text-slate-900">${relativePerformance.companyStart.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-600">At Recession End:</div>
                        <div className="text-2xl font-bold text-slate-900">${relativePerformance.companyEnd.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-600">Change:</div>
                        <div className={`text-xl font-bold ${relativePerformance.companyDecline >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {relativePerformance.companyDecline >= 0 ? '+' : ''}{relativePerformance.companyDecline.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Index Performance */}
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <div className="text-xs text-purple-600 font-semibold uppercase mb-3">Russell 2000 Index Performance</div>
                    <div className="space-y-2">
                      <div>
                        <div className="text-xs text-purple-600">At Transition:</div>
                        <div className="text-2xl font-bold text-slate-900">${relativePerformance.indexStart.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-purple-600">At Recession End:</div>
                        <div className="text-2xl font-bold text-slate-900">${relativePerformance.indexEnd.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-purple-600">Change:</div>
                        <div className={`text-xl font-bold ${relativePerformance.indexDecline >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {relativePerformance.indexDecline >= 0 ? '+' : ''}{relativePerformance.indexDecline.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Insight Card */}
              {relativePerformance && (
                <div className={`rounded-lg p-4 border-2 ${
                  relativePerformance.outperformance > 5
                    ? 'bg-green-50 border-green-300'
                    : relativePerformance.outperformance > -5
                    ? 'bg-blue-50 border-blue-300'
                    : 'bg-red-50 border-red-300'
                }`}>
                  <h5 className={`font-semibold text-sm mb-2 flex items-center gap-2 ${
                    relativePerformance.outperformance > 5
                      ? 'text-green-900'
                      : relativePerformance.outperformance > -5
                      ? 'text-blue-900'
                      : 'text-red-900'
                  }`}>
                    {relativePerformance.outperformance > 5 ? (
                      <>
                        <TrendingUp className="w-4 h-4" />
                        Strong Relative Performance
                      </>
                    ) : relativePerformance.outperformance > -5 ? (
                      <>
                        <AlertCircle className="w-4 h-4" />
                        Matched Market Performance
                      </>
                    ) : (
                      <>
                        <TrendingDown className="w-4 h-4" />
                        Underperformance vs Market
                      </>
                    )}
                  </h5>
                  <p className={`text-sm ${
                    relativePerformance.outperformance > 5
                      ? 'text-green-800'
                      : relativePerformance.outperformance > -5
                      ? 'text-blue-800'
                      : 'text-red-800'
                  }`}>
                    {relativePerformance.outperformance > 5
                      ? `${companyTicker} declined ${Math.abs(relativePerformance.companyDecline).toFixed(2)}% while Russell 2000 declined ${Math.abs(relativePerformance.indexDecline).toFixed(2)}%. The company outperformed by ${relativePerformance.outperformance.toFixed(2)}%, suggesting the new CEO navigated the recession better than market average.`
                      : relativePerformance.outperformance > -5
                      ? `${companyTicker} declined ${Math.abs(relativePerformance.companyDecline).toFixed(2)}% and Russell 2000 declined ${Math.abs(relativePerformance.indexDecline).toFixed(2)}%. Performance tracking the broader market suggests recession had similar impact on both, making CEO transition impact harder to isolate.`
                      : `${companyTicker} declined ${Math.abs(relativePerformance.companyDecline).toFixed(2)}% while Russell 2000 declined only ${Math.abs(relativePerformance.indexDecline).toFixed(2)}%. Underperformance of ${Math.abs(relativePerformance.outperformance).toFixed(2)}% may indicate sector headwinds or CEO execution challenges during crisis.`}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold mt-1">
                  ✓
                </div>
                <div>
                  <h5 className="font-semibold text-green-900 text-sm">CEO Transition During Economic Expansion</h5>
                  <p className="text-sm text-green-800 mt-2">
                    The CEO transition occurred outside major recession periods. Stock performance is more clearly attributable to CEO actions rather than macro-economic headwinds.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Key Analysis */}
        <div className="border-t border-slate-200 pt-6">
          <h4 className="font-semibold text-slate-900 text-base mb-4">Stock Behavior Analysis</h4>
          <div className="grid md:grid-cols-2 gap-4">
            {/* Recession Impact */}
            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <h5 className="font-semibold text-orange-900 text-sm mb-2">Recession Impact</h5>
              <p className="text-sm text-orange-800">
                {transitionInRecession
                  ? `Stock declined during ${transitionInRecession.name}. Typical Russell 2000 decline was ${analysis.summary?.average_decline.toFixed(2)}%. Your company's relative performance indicates ${relativePerformance?.outperformance! > 0 ? 'better-than-average' : 'worse-than-average'} crisis management.`
                  : 'Transition occurred outside recession periods. Economic factors provided tailwinds rather than headwinds.'}
              </p>
            </div>

            {/* CEO Transition Impact */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h5 className="font-semibold text-blue-900 text-sm mb-2">CEO Transition Impact</h5>
              <p className="text-sm text-blue-800">
                {transitionInRecession
                  ? `During crisis, new CEO's decisions on cost control, strategy, and stakeholder management directly visible. ${relativePerformance?.outperformance! > 0 ? 'Outperformance suggests strong crisis leadership.' : 'Underperformance suggests execution challenges during volatile period.'}`
                  : 'In expansion, positive stock moves more likely reflect CEO strategy and execution. Strong/weak performance clearer indicator of leadership quality.'}
              </p>
            </div>
          </div>
        </div>

        {/* Historical Context */}
        {analysis && (
          <div className="border-t border-slate-200 pt-6">
            <h4 className="font-semibold text-slate-900 text-base mb-4">Historical Recession Benchmarks</h4>
            <div className="space-y-2">
              {analysis.recessions.map((recession, idx) => (
                <div key={idx} className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-semibold text-slate-900 text-sm">{recession.name}</h5>
                      <p className="text-xs text-slate-600">{recession.period.start} to {recession.period.end}</p>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        recession.decline.percentage > 30 ? 'text-red-600' :
                        recession.decline.percentage >= 20 ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {recession.decline.percentage.toFixed(2)}%
                      </div>
                      <div className="text-xs text-slate-600">decline</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">
        <p className="text-xs text-slate-600">
          <span className="font-medium">How to Interpret:</span> Compare the CEO's performance during recessions against Russell 2000 benchmarks. Outperformance during downturns is a strong indicator of crisis leadership quality.
        </p>
      </div>
    </div>
  );
}
