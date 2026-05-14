import { ArrowRight, Calendar, TrendingUp, TrendingDown, Briefcase } from 'lucide-react';

interface CEOTransitionCardProps {
  company: string;
  previousCEO: string;
  newCEO: string;
  transitionDate: string;
  impact: number;
  tenure: {
    previous: string;
    new: string;
  };
  reason: string;
  imageUrl?: string;
}

export function CEOTransitionCard({ 
  company, 
  previousCEO, 
  newCEO, 
  transitionDate, 
  impact,
  tenure,
  reason,
  imageUrl
}: CEOTransitionCardProps) {
  const isPositive = impact >= 0;

  return (
    <div className="bg-white rounded-xl border border-border overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {imageUrl && (
        <div className="h-48 overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-50">
          <img src={imageUrl} alt={company} className="w-full h-full object-cover" />
        </div>
      )}
      
      <div className="p-6">
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
              <span className="font-semibold">{isPositive ? '+' : ''}{impact}%</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="text-sm text-muted-foreground mb-1">Outgoing CEO</div>
              <div className="font-medium">{previousCEO}</div>
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

        <div className="flex items-start gap-2">
          <Briefcase className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
          <div className="text-sm text-muted-foreground">{reason}</div>
        </div>
      </div>
    </div>
  );
}
