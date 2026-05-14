import { TrendingUp, TrendingDown, Calendar, User } from 'lucide-react';
import { motion } from 'motion/react';
import { formatDate } from '../utils/api';
import type { Company, CEOTransition, StockData } from '../utils/types';
import { MetricTooltip } from './MetricTooltip';

interface CEOHistoryViewProps {
  company: Company;
  stockData: StockData | null;
}

interface CEORecord {
  name: string;
  previousCEO?: string;
  startDate: string;
  endDate: string;
  duration: string;
  startPrice?: number;
  endPrice?: number;
  returnPct?: number;
  isCurrentCEO: boolean;
}

export function CEOHistoryView({ company, stockData }: CEOHistoryViewProps) {
  // Build CEO records with tenure and returns
  const ceoRecords: CEORecord[] = [];

  if (!company.transitions || company.transitions.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No CEO transitions found for this company.
      </div>
    );
  }

  // Build CEO list from transitions
  // Each CEO's tenure = from when they became CEO to when the next CEO took over
  // We only show CEOs from transitions since we need both start and end dates for accurate tenure calculation
  const ceoList: Array<{ name: string; startDate: string }> = company.transitions.map((transition) => ({
    name: transition.newCEO,
    startDate: transition.transitionDate
  }));

  // Process each CEO to calculate tenure and returns
  ceoList.forEach((ceo, idx) => {
    const startDate = ceo.startDate;
    const endDate = idx < ceoList.length - 1
      ? ceoList[idx + 1].startDate
      : new Date().toISOString().split('T')[0];

    // Find prices at start and end dates
    let startPrice: number | undefined;
    let endPrice: number | undefined;

    if (stockData?.data) {
      // Find start price (closest date on or after start)
      const startData = stockData.data.find(d => d.date >= startDate);
      startPrice = startData?.close;

      // Find end price (closest date on or before end)
      const endData = [...stockData.data]
        .reverse()
        .find(d => d.date <= endDate);
      endPrice = endData?.close;
    }

    // Calculate return
    let returnPct: number | undefined;
    if (startPrice && endPrice) {
      returnPct = ((endPrice - startPrice) / startPrice) * 100;
    }

    // Calculate duration
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const years = Math.floor(diffDays / 365);
    const months = Math.floor((diffDays % 365) / 30);
    let duration = '';
    if (years > 0) duration += `${years}y `;
    if (months > 0) duration += `${months}m`;
    if (!duration) duration = `${diffDays}d`;

    ceoRecords.push({
      name: ceo.name,
      startDate,
      endDate,
      duration,
      startPrice,
      endPrice,
      returnPct,
      isCurrentCEO: idx === ceoList.length - 1
    });
  });

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-slate-900 mb-4">All CEOs & Tenure Performance</h3>

      <div className="space-y-3">
        {ceoRecords.map((record, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className={`p-4 rounded-lg border ${
              record.isCurrentCEO
                ? 'border-blue-300 bg-blue-50'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <User className="w-5 h-5 text-slate-600" />
                </div>
                <div>
                  <div className="font-bold text-slate-900">{record.name}</div>
                  <div className="text-xs text-slate-500">
                    Started {formatDate(record.startDate)}
                  </div>
                </div>
                {record.isCurrentCEO && (
                  <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full font-medium ml-2">
                    Current
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-4 gap-3">
              <div className="bg-slate-50 p-3 rounded">
                <div className="text-xs text-slate-500 mb-1 font-medium flex items-center">
                  TENURE
                  <MetricTooltip text="Total length of this CEO's time in office, from their start date to when the next CEO took over (or today if they're the current CEO)." />
                </div>
                <div className="font-bold text-slate-900 text-sm">{record.duration}</div>
              </div>

              <div className="bg-slate-50 p-3 rounded">
                <div className="text-xs text-slate-500 mb-1 font-medium flex items-center">
                  START PRICE
                  <MetricTooltip text="The stock's adjusted closing price on the first trading day of this CEO's tenure." />
                </div>
                <div className="font-bold text-slate-900 text-sm">
                  {record.startPrice ? `$${record.startPrice.toFixed(2)}` : 'N/A'}
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded">
                <div className="text-xs text-slate-500 mb-1 font-medium flex items-center">
                  END PRICE
                  <MetricTooltip text="The stock's adjusted closing price on the last trading day of this CEO's tenure." />
                </div>
                <div className="font-bold text-slate-900 text-sm">
                  {record.endPrice ? `$${record.endPrice.toFixed(2)}` : 'N/A'}
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded">
                <div className="text-xs text-slate-500 mb-1 font-medium flex items-center">
                  TOTAL RETURN
                  <MetricTooltip text="Percentage price change from the CEO's first to last trading day. Captures the full stock performance during their tenure." />
                </div>
                {record.returnPct !== undefined ? (
                  <div className={`font-bold text-sm flex items-center gap-1 ${
                    record.returnPct >= 0 ? 'text-emerald-700' : 'text-red-700'
                  }`}>
                    {record.returnPct >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {record.returnPct.toFixed(1)}%
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">N/A</div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Summary statistics */}
      <div className="mt-6 pt-6 border-t border-slate-200">
        <div className="text-sm text-slate-600 space-y-2">
          <p>
            <span className="font-medium text-slate-900">{ceoRecords.length}</span> CEO{ceoRecords.length !== 1 ? 's' : ''} in {company.name}'s history
          </p>
          <p>
            <span className="font-medium text-slate-900">Average tenure:</span>{' '}
            {(ceoRecords.reduce((sum, c) => {
              const parts = c.duration.split(' ');
              let days = 0;
              parts.forEach(p => {
                if (p.includes('y')) days += parseInt(p) * 365;
                if (p.includes('m')) days += parseInt(p) * 30;
                if (p.includes('d')) days += parseInt(p);
              });
              return sum + days;
            }, 0) / ceoRecords.length / 365).toFixed(1)} years
          </p>
        </div>
      </div>
    </div>
  );
}
