import { useState, useEffect, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { loadIndexData } from '../utils/api';
import type { ChartDataPoint } from '../utils/types';

interface IndexComparisonProps {
  companyData: ChartDataPoint[];
  companyTicker: string;
  transitionDate: string;
  companyName: string;
  benchmarkTicker: string;
}

export function IndexComparison({ companyData, companyTicker, transitionDate, companyName, benchmarkTicker }: IndexComparisonProps) {
  const [indexData, setIndexData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIndexData = async () => {
      try {
        const data = await loadIndexData(benchmarkTicker);
        if (data) {
          setIndexData(data.data.map(p => ({
            ...p,
            dateLabel: new Date(p.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
            isTransitionDate: false,
          })));
        }
      } catch (error) {
        console.error('Error loading index data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchIndexData();
  }, [benchmarkTicker]);

  // Merge and normalize data
  const mergedData = useMemo(() => {
    if (!companyData || !indexData) return [];

    // Create a map of index data by date for quick lookup
    const indexMap = new Map(indexData.map(d => [d.date, d]));

    // Filter company data to only dates that exist in both datasets
    return companyData
      .filter(d => indexMap.has(d.date))
      .map(d => {
        const idx = indexMap.get(d.date)!;
        return {
          date: d.date,
          dateLabel: d.dateLabel,
          companyClose: d.close,
          indexClose: idx.close,
          isTransitionDate: d.isTransitionDate
        };
      });
  }, [companyData, indexData]);

  // Normalize prices to base 100 for comparison
  const normalizedData = useMemo(() => {
    if (mergedData.length === 0) return [];

    const firstCompanyPrice = mergedData[0].companyClose;
    const firstIndexPrice = mergedData[0].indexClose;

    return mergedData.map(d => ({
      ...d,
      companyNormalized: (d.companyClose / firstCompanyPrice) * 100,
      indexNormalized: (d.indexClose / firstIndexPrice) * 100
    }));
  }, [mergedData]);

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
            <h3 className="text-lg font-bold text-slate-900">{companyName} vs Russell 2000</h3>
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
                {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}% outperformance
              </span>
            </div>
          </div>
        </div>

        {/* Performance Comparison Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs text-blue-700 font-medium">Company Performance</div>
            <div className={`text-lg font-bold ${companyPerf >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {companyPerf >= 0 ? '+' : ''}{companyPerf.toFixed(2)}%
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
            <div className="text-xs text-purple-700 font-medium">Russell 2000 Performance</div>
            <div className={`text-lg font-bold ${indexPerf >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {indexPerf >= 0 ? '+' : ''}{indexPerf.toFixed(2)}%
            </div>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <div className="text-xs text-slate-700 font-medium">Relative Performance</div>
            <div className={`text-lg font-bold ${outperformance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}%
            </div>
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
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-xs text-slate-600 bg-slate-50 rounded p-3">
        <p>
          <span className="font-medium">Note:</span> Both prices are normalized to 100 at the start of the period for easy comparison. Red line marks CEO transition date.
        </p>
      </div>
    </div>
  );
}
