import { Calendar, TrendingUp, TrendingDown } from 'lucide-react';

interface TimelineEvent {
  date: string;
  company: string;
  event: string;
  impact: number;
  details: string;
}

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events }: TimelineProps) {
  return (
    <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
      <h3 className="mb-6">Recent CEO Transitions Timeline</h3>
      
      <div className="space-y-6">
        {events.map((event, index) => {
          const isPositive = event.impact >= 0;
          
          return (
            <div key={index} className="relative">
              {index !== events.length - 1 && (
                <div className="absolute left-[19px] top-10 bottom-0 w-0.5 bg-border" />
              )}
              
              <div className="flex gap-4">
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-blue-50 border-2 border-blue-200 flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
                
                <div className="flex-1 pb-6">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div>
                      <h4 className="mb-1">{event.company}</h4>
                      <p className="text-sm text-muted-foreground">{event.date}</p>
                    </div>
                    <div className={`flex items-center gap-1 px-2.5 py-1 rounded-lg ${isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                      {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                      <span className="text-sm font-medium">{isPositive ? '+' : ''}{event.impact}%</span>
                    </div>
                  </div>
                  <p className="text-sm mb-2">{event.event}</p>
                  <p className="text-xs text-muted-foreground">{event.details}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
