import { useState, useEffect } from 'react';
import { HomePage } from './components/HomePage';
import { CompanySelector } from './components/CompanySelector';
import { CompanyAnalysis } from './components/CompanyAnalysis';
import { ChatBot } from './components/ChatBot';
import { AnimatePresence } from 'motion/react';
import { loadCompanies, loadStockData } from './utils/dataLoader';
import type { CompaniesData, Company, CEOTransition, StockData } from './utils/types';

type ViewType = 'home' | 'selector' | 'analysis';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('home');
  const [companiesData, setCompaniesData] = useState<CompaniesData | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [selectedTransition, setSelectedTransition] = useState<CEOTransition | null>(null);
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [stockLoading, setStockLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load companies on mount
  useEffect(() => {
    loadCompanies()
      .then(data => {
        // Filter out transitions with ERROR CEO names
        data.companies = data.companies.map(c => ({
          ...c,
          transitions: c.transitions.filter(
            t => !t.previousCEO.includes('ERROR') && !t.newCEO.includes('ERROR')
          ),
        })).map(c => ({
          ...c,
          hasTransitions: c.transitions.length > 0,
          transitionCount: c.transitions.length,
        }));

        // Recalculate stats
        data.stats.companiesWithTransitions = data.companies.filter(c => c.hasTransitions).length;
        data.stats.totalTransitions = data.companies.reduce((sum, c) => sum + c.transitionCount, 0);

        setCompaniesData(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load data. Please ensure the data files are generated.');
        setLoading(false);
        console.error(err);
      });
  }, []);

  const handleGetStarted = () => {
    setCurrentView('selector');
  };

  const handleAnalyze = async (company: Company, transition: CEOTransition) => {
    setSelectedCompany(company);
    setSelectedTransition(transition);
    setStockLoading(true);
    setCurrentView('analysis');

    const data = await loadStockData(company.ticker);
    setStockData(data);
    setStockLoading(false);
  };

  const handleBackToHome = () => {
    setCurrentView('home');
  };

  const handleBackToSelector = () => {
    setCurrentView('selector');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading company data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-600 font-medium mb-2">{error}</p>
          <p className="text-slate-500 text-sm">Run: <code className="bg-slate-200 px-2 py-1 rounded">node scripts/preprocess.mjs</code></p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <AnimatePresence mode="wait">
        {currentView === 'home' && companiesData && (
          <HomePage
            key="home"
            onGetStarted={handleGetStarted}
            stats={companiesData.stats}
          />
        )}
        {currentView === 'selector' && companiesData && (
          <CompanySelector
            key="selector"
            companies={companiesData.companies}
            onBack={handleBackToHome}
            onAnalyze={handleAnalyze}
          />
        )}
        {currentView === 'analysis' && selectedCompany && selectedTransition && (
          <CompanyAnalysis
            key="analysis"
            company={selectedCompany}
            transition={selectedTransition}
            stockData={stockData}
            stockLoading={stockLoading}
            onBack={handleBackToHome}
            onChangeSelection={handleBackToSelector}
          />
        )}
      </AnimatePresence>

      <ChatBot
        currentView={currentView}
        company={selectedCompany}
        transition={selectedTransition}
        stockData={stockData}
      />
    </div>
  );
}
