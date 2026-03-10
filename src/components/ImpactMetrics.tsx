import { TrendingUp, TrendingDown, BarChart3, Users, DollarSign, Activity } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  change: number;
  icon: React.ReactNode;
  description: string;
}

function MetricCard({ title, value, change, icon, description }: MetricCardProps) {
  const isPositive = change >= 0;
  
  return (
    <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="p-2.5 bg-blue-50 rounded-lg">
          {icon}
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-sm ${isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
          {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
          <span className="font-medium">{isPositive ? '+' : ''}{change}%</span>
        </div>
      </div>
      <div className="text-sm text-muted-foreground mb-1">{title}</div>
      <div className="text-2xl font-semibold mb-2">{value}</div>
      <div className="text-xs text-muted-foreground">{description}</div>
    </div>
  );
}

export function ImpactMetrics() {
  const metrics = [
    {
      title: 'Average Stock Impact',
      value: '+12.4%',
      change: 12.4,
      icon: <BarChart3 className="w-5 h-5 text-blue-600" />,
      description: 'First 90 days post-transition'
    },
    {
      title: 'Market Volatility',
      value: '±8.2%',
      change: -3.1,
      icon: <Activity className="w-5 h-5 text-blue-600" />,
      description: 'Compared to industry average'
    },
    {
      title: 'Investor Confidence',
      value: '76%',
      change: 5.8,
      icon: <Users className="w-5 h-5 text-blue-600" />,
      description: 'Positive sentiment rating'
    },
    {
      title: 'Market Cap Change',
      value: '$2.8B',
      change: 8.6,
      icon: <DollarSign className="w-5 h-5 text-blue-600" />,
      description: 'Average across transitions'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metrics.map((metric, index) => (
        <MetricCard key={index} {...metric} />
      ))}
    </div>
  );
}
