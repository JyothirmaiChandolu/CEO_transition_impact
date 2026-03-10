import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { ChartDataPoint } from '../utils/types';

interface StockChartProps {
  data: ChartDataPoint[];
  transitionDate: string;
  companyName: string;
  ticker: string;
}

export function StockChart({ data, transitionDate, companyName, ticker }: StockChartProps) {
  const [showVolume, setShowVolume] = useState(false);

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <p className="text-slate-500 text-center py-8">No stock data available for this period.</p>
      </div>
    );
  }

  const firstPrice = data[0].close;
  const lastPrice = data[data.length - 1].close;
  const priceChange = lastPrice - firstPrice;
  const percentChange = (priceChange / firstPrice) * 100;
  const isPositive = priceChange >= 0;

  // Find the closest data point to transition date for the reference line
  const transitionLabel = data.find(d => d.isTransitionDate)?.date || transitionDate;

  // Downsample data if too many points for smooth rendering
  const chartData = data.length > 500
    ? data.filter((_, i) => i % Math.ceil(data.length / 500) === 0 || data[i]?.isTransitionDate)
    : data;

  // Format date for display
  const formatXAxisDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[d.getMonth()]} '${String(d.getFullYear()).slice(2)}`;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-sm text-slate-500 mb-1">Stock Performance</div>
          <h2 className="text-lg font-bold text-slate-900 mb-2">{companyName} ({ticker})</h2>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold text-slate-900">${lastPrice.toFixed(2)}</span>
            <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
              {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="text-sm font-medium">
                {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{percentChange.toFixed(2)}%)
              </span>
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {data[0].date} to {data[data.length - 1].date} (Adjusted Close)
          </div>
        </div>

        <button
          onClick={() => setShowVolume(!showVolume)}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
            showVolume ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          {showVolume ? 'Hide Volume' : 'Show Volume'}
        </button>
      </div>

      {/* Price Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`colorPrice-${ticker}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={isPositive ? "#0f766e" : "#b91c1c"} stopOpacity={0.15} />
              <stop offset="95%" stopColor={isPositive ? "#0f766e" : "#b91c1c"} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#475569', fontSize: 11 }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickFormatter={formatXAxisDate}
            interval={Math.max(1, Math.floor(chartData.length / 8))}
          />
          <YAxis
            tick={{ fill: '#475569', fontSize: 11 }}
            axisLine={{ stroke: '#e2e8f0' }}
            domain={['auto', 'auto']}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '8px 12px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Adj. Close']}
            labelFormatter={(label: string) => {
              const d = new Date(label);
              return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
            }}
          />
          <ReferenceLine
            x={transitionLabel}
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="4 4"
            label={{
              value: 'CEO Transition',
              position: 'top',
              fill: '#92400e',
              fontSize: 11,
              fontWeight: 600
            }}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke={isPositive ? "#0f766e" : "#b91c1c"}
            strokeWidth={1.5}
            fill={`url(#colorPrice-${ticker})`}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Volume Chart */}
      {showVolume && (
        <div className="mt-4">
          <div className="text-xs text-slate-500 font-medium mb-2">Trading Volume</div>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={chartData}>
              <XAxis dataKey="date" hide />
              <YAxis
                tick={{ fill: '#475569', fontSize: 10 }}
                axisLine={false}
                tickFormatter={(v: number) => {
                  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
                  if (v >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
                  return `${(v / 1e3).toFixed(0)}K`;
                }}
              />
              <Tooltip
                formatter={(value: number) => [value?.toLocaleString() || 'N/A', 'Volume']}
                labelFormatter={(label: string) => new Date(label).toLocaleDateString()}
              />
              <ReferenceLine x={transitionLabel} stroke="#f59e0b" strokeWidth={1} strokeDasharray="4 4" />
              <Bar dataKey="volume" fill="#94a3b8" opacity={0.6} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
