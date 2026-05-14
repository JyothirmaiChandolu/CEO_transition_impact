import { AlertCircle, TrendingUp } from 'lucide-react';

interface MacroEconomicContextProps {
  inRecession: boolean;
  context: string;
  analysisNote: string;
  macroSummary?: {
    totalRecessionPeriods: number;
    totalRecessionDays: number;
    recessionPercentage: number;
    recessions: Array<{
      name: string;
      start: string;
      end: string;
      durationMonths: number;
    }>;
  };
}

export function MacroEconomicContext({
  inRecession,
  context,
  analysisNote,
  macroSummary
}: MacroEconomicContextProps) {
  return (
    <div className="space-y-4">
      {/* Main Alert */}
      <div className={`rounded-lg border p-4 ${
        inRecession
          ? 'bg-amber-50 border-amber-200'
          : 'bg-emerald-50 border-emerald-200'
      }`}>
        <div className="flex items-start gap-3">
          {inRecession ? (
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          ) : (
            <TrendingUp className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
          )}
          <div className="flex-1">
            <div className={`font-semibold mb-1 ${
              inRecession ? 'text-amber-900' : 'text-emerald-900'
            }`}>
              {context}
            </div>
            <div className={`text-sm ${
              inRecession ? 'text-amber-800' : 'text-emerald-800'
            }`}>
              {analysisNote}
            </div>
          </div>
        </div>
      </div>

      {/* Recession Details */}
      {macroSummary && macroSummary.recessions.length > 0 && (
        <div className="bg-white rounded-lg border border-border p-4">
          <div className="font-semibold text-sm mb-3">Historical Recessions</div>
          <div className="space-y-2">
            {macroSummary.recessions.map((recession, idx) => (
              <div key={idx} className="border-l-2 border-amber-300 pl-3 py-1">
                <div className="text-sm font-medium text-gray-900">{recession.name}</div>
                <div className="text-xs text-muted-foreground">
                  {recession.start} to {recession.end} ({recession.durationMonths} months)
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
