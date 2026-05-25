import { useState, useEffect, useMemo } from 'react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { loadIndexData } from '../utils/api';
import type { ChartDataPoint } from '../utils/types';

const SECTOR_ETF_MAP: Record<string, string> = {
  'Information Technology': 'XLK',
  'Technology': 'XLK',
  'Health Care': 'XLV',
  'Healthcare': 'XLV',
  'Financials': 'XLF',
  'Financial Services': 'XLF',
  'Consumer Discretionary': 'XLY',
  'Consumer Cyclical': 'XLY',
  'Consumer Staples': 'XLP',
  'Consumer Defensive': 'XLP',
  'Energy': 'XLE',
  'Utilities': 'XLU',
  'Materials': 'XLB',
  'Basic Materials': 'XLB',
  'Industrials': 'XLI',
  'Real Estate': 'XLRE',
  'Communication Services': 'XLC',
};

interface IndexComparisonProps {
  companyData: ChartDataPoint[];
  companyTicker: string;
  transitionDate: string;
  companyName: string;
  benchmarkTicker: string;
  sector?: string;
}

export function IndexComparison({ companyData, companyTicker, transitionDate, companyName, benchmarkTicker, sector }: IndexComparisonProps) {
  const [indexData, setIndexData] = useState<ChartDataPoint[]>([]);
  const [sectorData, setSectorData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const sectorTicker = sector ? SECTOR_ETF_MAP[sector] ?? null : null;

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const fetches: Promise<void>[] = [
          loadIndexData(benchmarkTicker).then(data => {
            if (data) setIndexData(data.data.map(p => ({ ...p, dateLabel: new Date(p.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }), isTransitionDate: false })));
          }),
        ];
        if (sectorTicker) {
          fetches.push(
            loadIndexData(sectorTicker).then(data => {
              if (data) setSectorData(data.data.map(p => ({ ...p, dateLabel: new Date(p.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }), isTransitionDate: false })));
            })
          );
        }
        await Promise.all(fetches);
      } catch (error) {
        console.error('Error loading comparison data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [benchmarkTicker, sectorTicker]);

  // Merge and normalize data
  const mergedData = useMemo(() => {
    if (!companyData || !indexData) return [];

    const indexMap = new Map(indexData.map(d => [d.date, d]));
    const sectorMap = new Map(sectorData.map(d => [d.date, d]));

    return companyData
      .filter(d => indexMap.has(d.date))
      .map(d => {
        const idx = indexMap.get(d.date)!;
        const sec = sectorMap.get(d.date);
        return {
          date: d.date,
          dateLabel: d.dateLabel,
          companyClose: d.close,
          indexClose: idx.close,
          sectorClose: sec ? sec.close : null,
          isTransitionDate: d.isTransitionDate,
        };
      });
  }, [companyData, indexData, sectorData]);

  // Normalize prices to base 100 for comparison
  const normalizedData = useMemo(() => {
    if (mergedData.length === 0) return [];

    const firstCompanyPrice = mergedData[0].companyClose;
    const firstIndexPrice = mergedData[0].indexClose;
    const firstSectorPrice = mergedData.find(d => d.sectorClose != null)?.sectorClose ?? null;

    return mergedData.map(d => ({
      ...d,
      companyNormalized: (d.companyClose / firstCompanyPrice) * 100,
      indexNormalized: (d.indexClose / firstIndexPrice) * 100,
      sectorNormalized: (firstSectorPrice && d.sectorClose) ? (d.sectorClose / firstSectorPrice) * 100 : undefined,
    }));
  }, [mergedData]);

  // True abnormal return: stock return − benchmark return, both anchored at transition date
  const abnormalReturnData = useMemo(() => {
    if (mergedData.length === 0) return [];

    const targetDate = new Date(transitionDate);
    const transitionIdx = mergedData.reduce((best, _, idx) => {
      const bestDiff = Math.abs(new Date(mergedData[best].date).getTime() - targetDate.getTime());
      const currDiff = Math.abs(new Date(mergedData[idx].date).getTime() - targetDate.getTime());
      return currDiff < bestDiff ? idx : best;
    }, 0);

    const baseCompany = mergedData[transitionIdx].companyClose;
    const baseIndex   = mergedData[transitionIdx].indexClose;
    const baseSector  = mergedData[transitionIdx].sectorClose;

    return mergedData.slice(transitionIdx, transitionIdx + 365).map((d, i) => {
      const stockRet = ((d.companyClose - baseCompany) / baseCompany) * 100;
      const benchRet = ((d.indexClose   - baseIndex)   / baseIndex)   * 100;
      const secRet   = (baseSector && d.sectorClose) ? ((d.sectorClose - baseSector) / baseSector) * 100 : undefined;
      return {
        date: d.date,
        day: i,
        abnormalReturn: parseFloat((stockRet - benchRet).toFixed(2)),
        stockReturn:    parseFloat(stockRet.toFixed(2)),
        benchmarkReturn: parseFloat(benchRet.toFixed(2)),
        sectorReturn:   secRet != null ? parseFloat(secRet.toFixed(2)) : undefined,
      };
    });
  }, [mergedData, transitionDate]);

  const ar90 = abnormalReturnData[89]?.abnormalReturn
    ?? abnormalReturnData[abnormalReturnData.length - 1]?.abnormalReturn
    ?? null;
  const ar1y = abnormalReturnData[251]?.abnormalReturn
    ?? abnormalReturnData[abnormalReturnData.length - 1]?.abnormalReturn
    ?? null;

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 rounded w-1/3"></div>
          <div className="h-96 bg-slate-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (normalizedData.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <p className="text-slate-500 text-center py-8">No comparison data available for this period.</p>
      </div>
    );
  }

  // Calculate performance metrics
  const firstData = normalizedData[0];
  const lastData = normalizedData[normalizedData.length - 1];

  const companyPerf = lastData.companyNormalized - firstData.companyNormalized;
  const indexPerf = lastData.indexNormalized - firstData.indexNormalized;
  const outperformance = companyPerf - indexPerf;
  const sectorPerf = (lastData.sectorNormalized != null && firstData.sectorNormalized != null)
    ? lastData.sectorNormalized - firstData.sectorNormalized
    : null;
  const vsSecPerf = sectorPerf != null ? companyPerf - sectorPerf : null;

  const transitionLabel = (() => {
    const exactMatch = normalizedData.find(d => d.isTransitionDate);
    if (exactMatch) return exactMatch.date;

    const targetDate = new Date(transitionDate);
    const closest = normalizedData.reduce((prev, curr) => {
      const prevDiff = Math.abs(new Date(prev.date).getTime() - targetDate.getTime());
      const currDiff = Math.abs(new Date(curr.date).getTime() - targetDate.getTime());
      return currDiff < prevDiff ? curr : prev;
    });
    return closest?.date || transitionDate;
  })();

  // Downsample for rendering
  const chartData = normalizedData.length > 500
    ? normalizedData.filter((_, i) => i % Math.ceil(normalizedData.length / 500) === 0 || normalizedData[i]?.isTransitionDate)
    : normalizedData;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              {companyName} vs Russell 2000{sectorTicker ? ` vs ${sector} Sector (${sectorTicker})` : ''}
            </h3>
            <p className="text-sm text-slate-600 mt-1">Normalized comparison (Base = 100)</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-2">
              {outperformance >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-600" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-600" />
              )}
              <span className={`text-sm font-semibold ${outperformance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}% vs index
              </span>
            </div>
          </div>
        </div>

        {/* Performance Comparison Cards */}
        <div className={`grid gap-3 mb-6 ${sectorTicker ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2 md:grid-cols-3'}`}>
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs text-blue-700 font-medium">{companyTicker} Performance</div>
            <div className={`text-lg font-bold ${companyPerf >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {companyPerf >= 0 ? '+' : ''}{companyPerf.toFixed(2)}%
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
            <div className="text-xs text-purple-700 font-medium">Russell 2000</div>
            <div className={`text-lg font-bold ${indexPerf >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {indexPerf >= 0 ? '+' : ''}{indexPerf.toFixed(2)}%
            </div>
          </div>

          {sectorTicker && sectorPerf !== null && (
            <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
              <div className="text-xs text-emerald-700 font-medium">{sector} Sector ({sectorTicker})</div>
              <div className={`text-lg font-bold ${sectorPerf >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {sectorPerf >= 0 ? '+' : ''}{sectorPerf.toFixed(2)}%
              </div>
            </div>
          )}

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <div className="text-xs text-slate-700 font-medium">vs Index</div>
            <div className={`text-lg font-bold ${outperformance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}%
            </div>
            {vsSecPerf !== null && (
              <div className={`text-xs font-medium mt-0.5 ${vsSecPerf >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {vsSecPerf >= 0 ? '+' : ''}{vsSecPerf.toFixed(2)}% vs sector
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-slate-50 rounded-lg p-4">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCompany" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorIndex" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorSector" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#94a3b8"
              interval={Math.ceil(chartData.length / 12) - 1}
              tickFormatter={(date) => {
                const d = new Date(date);
                return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
              }}
            />
            <YAxis
              label={{ value: 'Normalized Price', angle: -90, position: 'insideLeft' }}
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              formatter={(value) => (typeof value === 'number' ? value.toFixed(2) : value)}
              labelFormatter={(label) => {
                const d = new Date(label);
                return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
              }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <ReferenceLine
              x={transitionLabel}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{
                value: 'Transition',
                position: 'insideTopRight',
                fill: '#ef4444',
                fontSize: 12,
                fontWeight: 'bold',
                offset: -5
              }}
            />
            <Area
              type="monotone"
              dataKey="companyNormalized"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#colorCompany)"
              name={`${companyTicker} (Normalized)`}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="indexNormalized"
              stroke="#a855f7"
              fillOpacity={1}
              fill="url(#colorIndex)"
              name="Russell 2000 (Normalized)"
              isAnimationActive={false}
            />
            {sectorTicker && (
              <Area
                type="monotone"
                dataKey="sectorNormalized"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#colorSector)"
                name={`${sector} Sector — ${sectorTicker} (Normalized)`}
                isAnimationActive={false}
                connectNulls
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-xs text-slate-600 bg-slate-50 rounded p-3">
        <p>
          <span className="font-medium">Note:</span> All prices normalized to 100 at period start.
          {sectorTicker ? ` Green line = ${sectorTicker} SPDR sector ETF (${sector}).` : ''} Red dashed line = CEO transition date.
        </p>
      </div>

      {/* Abnormal Return Section */}
      {abnormalReturnData.length > 0 && (
        <div className="mt-8 border-t border-slate-200 pt-6">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-slate-900">Cumulative Abnormal Return (Post-Transition)</h3>
            <p className="text-sm text-slate-500 mt-1">
              Stock return minus benchmark return, both measured from the CEO transition date. Isolates the CEO-specific market impact from broader market movements.
            </p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className={`rounded-lg p-4 border ${ar90 !== null && ar90 >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
              <div className="text-xs font-medium text-slate-600 mb-1">90-Day Abnormal Return</div>
              <div className={`text-2xl font-bold ${ar90 !== null && ar90 >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {ar90 !== null ? `${ar90 >= 0 ? '+' : ''}${ar90.toFixed(2)}%` : 'N/A'}
              </div>
              <div className="text-xs text-slate-500 mt-1">vs {benchmarkTicker}</div>
            </div>
            <div className={`rounded-lg p-4 border ${ar1y !== null && ar1y >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
              <div className="text-xs font-medium text-slate-600 mb-1">1-Year Abnormal Return</div>
              <div className={`text-2xl font-bold ${ar1y !== null && ar1y >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {ar1y !== null ? `${ar1y >= 0 ? '+' : ''}${ar1y.toFixed(2)}%` : 'N/A'}
              </div>
              <div className="text-xs text-slate-500 mt-1">vs {benchmarkTicker}</div>
            </div>
          </div>

          {/* Abnormal Return Chart */}
          <div className="bg-slate-50 rounded-lg p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={abnormalReturnData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 12 }}
                  stroke="#94a3b8"
                  tickFormatter={(d) => `Day ${d}`}
                  interval={Math.ceil(abnormalReturnData.length / 8) - 1}
                />
                <YAxis
                  tickFormatter={(v) => `${v.toFixed(1)}%`}
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                  formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name]}
                  labelFormatter={(day) => `Day ${day} post-transition`}
                />
                <Legend wrapperStyle={{ paddingTop: '16px' }} />
                <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="abnormalReturn"
                  stroke="#f59e0b"
                  dot={false}
                  strokeWidth={2}
                  name="Abnormal Return (vs Index)"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="stockReturn"
                  stroke="#3b82f6"
                  dot={false}
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  name={`${companyTicker} Return`}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="benchmarkReturn"
                  stroke="#a855f7"
                  dot={false}
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  name={`${benchmarkTicker} Return`}
                  isAnimationActive={false}
                />
                {sectorTicker && (
                  <Line
                    type="monotone"
                    dataKey="sectorReturn"
                    stroke="#10b981"
                    dot={false}
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    name={`${sectorTicker} Sector Return`}
                    isAnimationActive={false}
                    connectNulls
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-3 text-xs text-slate-600 bg-slate-50 rounded p-3">
            <span className="font-medium">How to read:</span> Abnormal Return (amber) = {companyTicker} return − {benchmarkTicker} return from transition date.
            {sectorTicker ? ` Green line = ${sectorTicker} sector ETF return for context.` : ''} Positive values mean the stock outperformed the market.
          </div>
        </div>
      )}
    </div>
  );
}
