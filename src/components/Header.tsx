import { TrendingUp, BarChart3, Users } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 bg-white/20 backdrop-blur-sm rounded-lg">
            <TrendingUp className="w-8 h-8" />
          </div>
          <h1 className="text-4xl font-bold">CEO Transition Impact Analysis</h1>
        </div>
        <p className="text-blue-100 text-lg max-w-3xl">
          Comprehensive analysis of leadership transitions and their impact on stock market performance across Fortune 500 companies
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 className="w-5 h-5 text-blue-200" />
              <span className="text-sm text-blue-100">Total Transitions Analyzed</span>
            </div>
            <div className="text-3xl font-bold">247</div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
            <div className="flex items-center gap-3 mb-2">
              <Users className="w-5 h-5 text-blue-200" />
              <span className="text-sm text-blue-100">Companies Tracked</span>
            </div>
            <div className="text-3xl font-bold">156</div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-blue-200" />
              <span className="text-sm text-blue-100">Average Performance</span>
            </div>
            <div className="text-3xl font-bold">+12.4%</div>
          </div>
        </div>
      </div>
    </header>
  );
}
