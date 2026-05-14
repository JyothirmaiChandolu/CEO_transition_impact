import { useState, useEffect } from 'react';
import { IndexSelector } from './components/IndexSelector';
import { HomePage } from './components/HomePage';
import { CompanySelector } from './components/CompanySelector';
import { CompanyAnalysis } from './components/CompanyAnalysis';
import { CompanyArchive } from './components/CompanyArchive';
import { OutlierAnalysis } from './components/OutlierAnalysis';
import { RankingsPage } from './components/RankingsPage';
import { ChatBot } from './components/ChatBot';
import { AnimatePresence } from 'motion/react';
import { loadIndices, loadCompanies, loadStockData } from './utils/api';
import type { CompaniesData, Company, CEOTransition, StockData, IndexConfig } from './utils/types';

type ViewType = 'index-selector' | 'home' | 'archive' | 'selector' | 'analysis' | 'outlier-analysis' | 'rankings';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('index-selector');
  const [indices, setIndices] = useState<IndexConfig[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<IndexConfig | null>(null);
  const [companiesData, setCompaniesData] = useState<CompaniesData | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [selectedTransition, setSelectedTransition] = useState<CEOTransition | null>(null);
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [stockLoading, setStockLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load indices on mount
  useEffect(() => {
    loadIndices()
      .then(data => {
        setIndices(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load indices. Please ensure the backend is running.');
        setLoading(false);
        console.error(err);
      });
  }, []);

  const handleIndexSelect = (index: IndexConfig) => {
    setSelectedIndex(index);
    setCompaniesData(null);
    setLoading(true);

    loadCompanies(index.key)
      .then(data => {
        data.companies = data.companies.map(c => ({
          ...c,
          transitions: c.transitions.filter(
            t => !t.previousCEO.includes('ERROR') && !t.newCEO.includes('ERROR') &&
                 !t.previousCEO.includes('NOT FOUND') && !t.newCEO.includes('NOT FOUND')
          ),
        })).map(c => ({
          ...c,
          hasTransitions: c.transitions.length > 0,
          transitionCount: c.transitions.length,
        }));

        data.stats.companiesWithTransitions = data.companies.filter(c => c.hasTransitions).length;
        data.stats.totalTransitions = data.companies.reduce((sum, c) => sum + c.transitionCount, 0);

        setCompaniesData(data);
        setLoading(false);
        setCurrentView('home');
      })
      .catch(err => {
        setError('Failed to load company data. Please ensure the backend is running.');
        setLoading(false);
        console.error(err);
      });
  };

  const handleGetStarted = () => setCurrentView('selector');
  const handleOutlierAnalysis = () => setCurrentView('outlier-analysis');
  const handleRankings = () => setCurrentView('rankings');
  const handleArchive = () => setCurrentView('archive');
  const handleBackToHome = () => setCurrentView('home');
  const handleBackToSelector = () => setCurrentView('selector');
  const handleBackToIndexSelector = () => setCurrentView('index-selector');

  const handleAnalyze = async (company: Company, transition: CEOTransition) => {
    setSelectedCompany(company);
    setSelectedTransition(transition);
    setStockLoading(true);
    setCurrentView('analysis');

    const data = await loadStockData(company.ticker, selectedIndex!.key);
    setStockData(data);
    setStockLoading(false);
  };

  if (loading && currentView === 'index-selector') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-600 font-medium mb-2">{error}</p>
          <p className="text-slate-500 text-sm">Ensure the backend is running.</p>
        </div>
      </div>
    );
  }

  // Loading spinner while switching index
  if (loading && currentView !== 'index-selector') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading company data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <AnimatePresence mode="wait">
        {currentView === 'index-selector' && (
          <IndexSelector
            key="index-selector"
            indices={indices}
            onSelect={handleIndexSelect}
          />
        )}
        {currentView === 'home' && companiesData && selectedIndex && (
          <HomePage
            key="home"
            onGetStarted={handleGetStarted}
            onOutlierAnalysis={handleOutlierAnalysis}
            onRankings={handleRankings}
            onArchive={handleArchive}
            onChangeIndex={handleBackToIndexSelector}
            indexName={selectedIndex.name}
            stats={companiesData.stats}
          />
        )}
        {currentView === 'archive' && selectedIndex && (
          <CompanyArchive
            key="archive"
            index={selectedIndex}
            onBack={handleBackToHome}
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
        {currentView === 'analysis' && selectedCompany && selectedTransition && selectedIndex && (
          <CompanyAnalysis
            key="analysis"
            company={selectedCompany}
            transition={selectedTransition}
            stockData={stockData}
            stockLoading={stockLoading}
            onBack={handleBackToHome}
            onChangeSelection={handleBackToSelector}
            index={selectedIndex.key}
            benchmarkTicker={selectedIndex.benchmark_ticker}
          />
        )}
        {currentView === 'outlier-analysis' && companiesData && selectedIndex && (
          <OutlierAnalysis
            key="outlier-analysis"
            companies={companiesData.companies}
            onBack={handleBackToHome}
            index={selectedIndex.key}
          />
        )}
        {currentView === 'rankings' && companiesData && selectedIndex && (
          <RankingsPage
            key="rankings"
            companies={companiesData.companies}
            onBack={handleBackToHome}
            onSelectCompany={handleAnalyze}
            index={selectedIndex.key}
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
