import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Volume2, TrendingUp, Award } from 'lucide-react';
import type { StockData } from '../utils/types';

interface AnalysisChartsProps {
  stockData: StockData | null;
  transitionDate: string;
}

export function AnalysisCharts({ stockData, transitionDate }: AnalysisChartsProps) {
  if (!stockData || !stockData.data || stockData.data.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No data available for analysis charts.
      </div>
    );
  }

  // Prepare volume data around transition
  const volumeData = stockData.data
    .filter(d => {
      const dDate = new Date(d.date);
      const tDate = new Date(transitionDate);
      const diffDays = Math.abs((dDate.getTime() - tDate.getTime()) / (1000 * 60 * 60 * 24));
      return diffDays <= 180; // 6 months around transition
    })
    .slice(0, 100) // Limit to last 100 points for visibility
    .map(d => ({
      date: d.date.slice(5), // MM-DD format
      volume: d.volume / 1000000, // Convert to millions
      isTransition: d.date === transitionDate
    }));

  // Calculate abnormal returns (comparison to pre-transition baseline)
  // Find closest date to transition (handle weekends/holidays with no trading data)
  const transitionDate_obj = new Date(transitionDate);
  const transitionIdx = stockData.data.reduce((closest, current, idx) => {
    const currentDiff = Math.abs(new Date(current.date).getTime() - transitionDate_obj.getTime());
    const closestDiff = Math.abs(new Date(stockData.data[closest].date).getTime() - transitionDate_obj.getTime());
    return currentDiff < closestDiff ? idx : closest;
  }, 0);

  const preTransitionIdx = Math.max(0, transitionIdx - 30);
  const baselinePrice = stockData.data[preTransitionIdx]?.close || 100;

  const abnormalReturnData = stockData.data
    .slice(transitionIdx, transitionIdx + 90)
    .map((d, idx) => {
      const expectedReturn = ((d.close - baselinePrice) / baselinePrice) * 100;
      return {
        date: d.date.slice(5),
        return: parseFloat(expectedReturn.toFixed(2)),
        isTransition: d.date === transitionDate
      };
    });

  // Tenure performance simulation (showing impact over time post-transition)
  const tenureData = stockData.data
    .slice(transitionIdx, Math.min(transitionIdx + 365, stockData.data.length))
    .map((d, idx) => {
      const daysElapsed = idx;
      const initialPrice = stockData.data[transitionIdx]?.close || 100;
      const cumulativeReturn = ((d.close - initialPrice) / initialPrice) * 100;
      return {
        days: daysElapsed,
        return: parseFloat(cumulativeReturn.toFixed(2)),
        date: d.date.slice(5)
      };
    });

  return (
    <div className="space-y-8">
      {/* Volume Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
            <Volume2 className="w-5 h-5 text-slate-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Trading Volume Analysis</h3>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={volumeData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              interval={Math.max(0, Math.floor(volumeData.length / 8))}
            />
            <YAxis
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              label={{ value: 'Volume (M)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}M shares`, 'Volume']}
              labelFormatter={(label: string) => `Date: ${label}`}
            />
            <ReferenceLine x={transitionDate.slice(5)} stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" />
            <Bar dataKey="volume" fill="#94a3b8" opacity={0.7} />
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900">Volume Insight:</span> Trading volume changes around CEO transitions can indicate investor interest and market sentiment about the leadership change.
          </p>
        </div>
      </div>

      {/* Abnormal Return Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-slate-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">90-Day Abnormal Return</h3>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={abnormalReturnData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              interval={Math.max(0, Math.floor(abnormalReturnData.length / 8))}
            />
            <YAxis
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
              labelFormatter={(label: string) => `Date: ${label}`}
            />
            <ReferenceLine y={0} stroke="#64748b" />
            <ReferenceLine x={transitionDate.slice(5)} stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" />
            <Line
              type="monotone"
              dataKey="return"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
              name="Abnormal Return"
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900">Abnormal Return Insight:</span> This shows the cumulative return relative to a baseline, helping isolate the market's reaction to the CEO change from broader market movements.
          </p>
        </div>
      </div>

      {/* Tenure Performance Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
            <Award className="w-5 h-5 text-slate-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Post-Transition Performance (1 Year)</h3>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={tenureData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              interval={Math.max(0, Math.floor(tenureData.length / 8))}
            />
            <YAxis
              tick={{ fill: '#475569', fontSize: 11 }}
              axisLine={{ stroke: '#e2e8f0' }}
              label={{ value: 'Cumulative Return (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
              labelFormatter={(label: string) => `Date: ${label}`}
            />
            <ReferenceLine y={0} stroke="#64748b" />
            <Line
              type="monotone"
              dataKey="return"
              stroke="#0369a1"
              strokeWidth={2}
              dot={false}
              name="Cumulative Return"
              isAnimationActive={true}
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900">Performance Insight:</span> This tracks the new CEO's performance in the first year, showing cumulative returns from the transition date forward.
          </p>
        </div>
      </div>
    </div>
  );
}
