import { ArrowRight, Calendar, TrendingUp, TrendingDown, Briefcase, AlertCircle, CheckCircle } from 'lucide-react';

interface CEOTransitionWithMacroProps {
  company: string;
  previousCEO: string;
  newCEO: string;
  transitionDate: string;
  impact90d: number;
  impact1y?: number;
  tenure: {
    previous: string;
    new: string;
  };
  reason: string;
  imageUrl?: string;
  // Macro-economic context
  inRecession: boolean;
  recessionPeriod?: string;
  analysisNote: string;
}

export function CEOTransitionWithMacroCard({
  company,
  previousCEO,
  newCEO,
  transitionDate,
  impact90d,
  impact1y,
  tenure,
  reason,
  imageUrl,
  inRecession,
  recessionPeriod,
  analysisNote
}: CEOTransitionWithMacroProps) {
  const isPositive = impact90d >= 0;

  return (
    <div className="bg-white rounded-xl border border-border overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* Image */}
      {imageUrl && (
        <div className="h-48 overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-50">
          <img src={imageUrl} alt={company} className="w-full h-full object-cover" />
        </div>
      )}

      <div className="p-6">
        {/* Header with Impact */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="mb-1">{company}</h3>
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Calendar className="w-4 h-4" />
              <span>{transitionDate}</span>
            </div>
          </div>
          <div className={`px-3 py-1.5 rounded-lg ${isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
            <div className="flex items-center gap-1">
              {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="font-semibold">{isPositive ? '+' : ''}{impact90d}%</span>
            </div>
            <div className="text-xs opacity-75 mt-1">90-day impact</div>
          </div>
        </div>

        {/* CEO Transition Details */}
        <div className="bg-slate-50 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="text-sm text-muted-foreground mb-1">{previousCEO ? 'Outgoing CEO' : 'Initial Appointment'}</div>
              <div className="font-medium">{previousCEO || '—'}</div>
              <div className="text-xs text-muted-foreground mt-1">{tenure.previous}</div>
            </div>
            <ArrowRight className="w-5 h-5 text-amber-500 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm text-muted-foreground mb-1">Incoming CEO</div>
              <div className="font-medium">{newCEO}</div>
              <div className="text-xs text-muted-foreground mt-1">{tenure.new}</div>
            </div>
          </div>
        </div>

        {/* Reason */}
        <div className="flex items-start gap-2 mb-4">
          <Briefcase className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
          <div className="text-sm text-muted-foreground">{reason}</div>
        </div>

        {/* Macro-Economic Context */}
        <div className={`rounded-lg border p-3 ${
          inRecession
            ? 'bg-amber-50 border-amber-200'
            : 'bg-emerald-50 border-emerald-200'
        }`}>
          <div className="flex items-start gap-2">
            {inRecession ? (
              <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            ) : (
              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
            )}
            <div className="flex-1">
              <div className={`text-xs font-semibold ${
                inRecession ? 'text-amber-900' : 'text-emerald-900'
              }`}>
                {inRecession ? '⚠️ Recession Period' : '✓ Economic Expansion'}
              </div>
              {recessionPeriod && (
                <div className={`text-xs mt-1 ${
                  inRecession ? 'text-amber-800' : 'text-emerald-800'
                }`}>
                  {recessionPeriod}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Note */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-xs text-blue-900">
            <span className="font-semibold block mb-1">Analysis Note:</span>
            {analysisNote}
          </div>
        </div>

        {/* 1-Year Impact if available */}
        {impact1y !== undefined && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-muted-foreground mb-2">1-Year Impact</div>
            <div className="flex items-center gap-2">
              <div className={`text-xl font-semibold ${impact1y >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {impact1y >= 0 ? '+' : ''}{impact1y}%
              </div>
              <div className="text-xs text-muted-foreground">
                {impact1y > impact90d ? '📈 Improving trend' : impact1y < impact90d ? '📉 Declining trend' : '→ Stable'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
