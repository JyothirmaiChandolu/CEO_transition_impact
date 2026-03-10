import { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Building2, ArrowLeft, ArrowRight, Search, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { formatDateShort } from '../utils/dataLoader';
import type { Company, CEOTransition } from '../utils/types';

interface CompanySelectorProps {
  companies: Company[];
  onBack: () => void;
  onAnalyze: (company: Company, transition: CEOTransition) => void;
}

export function CompanySelector({ companies, onBack, onAnalyze }: CompanySelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [selectedTransition, setSelectedTransition] = useState<CEOTransition | null>(null);
  const [showOnlyWithTransitions, setShowOnlyWithTransitions] = useState(true);

  // Get unique sectors
  const sectors = useMemo(() => {
    const sectorSet = new Set<string>();
    companies.forEach(c => {
      if (c.sector && c.sector !== 'Unknown') sectorSet.add(c.sector);
    });
    return ['all', ...Array.from(sectorSet).sort()];
  }, [companies]);

  // Filter companies
  const filteredCompanies = useMemo(() => {
    return companies.filter(c => {
      const matchesSearch = searchQuery === '' ||
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.ticker.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSector = selectedSector === 'all' || c.sector === selectedSector;
      const matchesTransitions = !showOnlyWithTransitions || c.hasTransitions;
      return matchesSearch && matchesSector && matchesTransitions;
    });
  }, [companies, searchQuery, selectedSector, showOnlyWithTransitions]);

  // Group by sector for display
  const groupedCompanies = useMemo(() => {
    const groups = new Map<string, Company[]>();
    filteredCompanies.forEach(c => {
      const sector = c.sector || 'Other';
      if (!groups.has(sector)) groups.set(sector, []);
      groups.get(sector)!.push(c);
    });
    return new Map([...groups.entries()].sort((a, b) => a[0].localeCompare(b[0])));
  }, [filteredCompanies]);

  const handleCompanyClick = (company: Company) => {
    setSelectedCompany(company);
    setSelectedTransition(null);
  };

  const handleAnalyze = () => {
    if (selectedCompany && selectedTransition) {
      onAnalyze(selectedCompany, selectedTransition);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -100 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-slate-50 font-sans"
    >
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Back Button */}
        <Button
          onClick={onBack}
          variant="ghost"
          className="mb-6 hover:bg-slate-200 text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Company List */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden"
            >
              {/* Header */}
              <div className="bg-slate-900 text-white p-6">
                <h2 className="text-2xl font-bold mb-1">Select a Company</h2>
                <p className="text-slate-400 text-sm">{filteredCompanies.length} companies available</p>
              </div>

              {/* Search & Filters */}
              <div className="p-4 border-b border-slate-200 space-y-3">
                <div className="flex items-center gap-3 border-2 border-slate-300 rounded-xl bg-white shadow-sm focus-within:ring-2 focus-within:ring-slate-500 focus-within:border-slate-500 transition-all px-3 py-3">
                  <Search className="w-5 h-5 text-slate-500 flex-shrink-0" />
                  <input
                    type="text"
                    placeholder="Search by company name or ticker..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full text-sm bg-transparent outline-none placeholder:text-slate-400"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Filter className="w-4 h-4 text-slate-400" />
                  <div className="flex flex-wrap gap-1.5">
                    {sectors.map(sector => (
                      <button
                        key={sector}
                        onClick={() => setSelectedSector(sector)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          selectedSector === sector
                            ? 'bg-slate-900 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {sector === 'all' ? 'All Sectors' : sector}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showOnlyWithTransitions}
                    onChange={(e) => setShowOnlyWithTransitions(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  Show only companies with CEO transitions
                </label>
              </div>

              {/* Company List */}
              <div className="max-h-[500px] overflow-y-auto">
                {filteredCompanies.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    No companies match your search criteria.
                  </div>
                ) : (
                  [...groupedCompanies.entries()].map(([sector, sectorCompanies]) => (
                    <div key={sector}>
                      <div className="px-4 py-2 bg-slate-50 border-b border-slate-100 sticky top-0 z-10">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          {sector} ({sectorCompanies.length})
                        </span>
                      </div>
                      {sectorCompanies.map(company => (
                        <button
                          key={company.ticker}
                          onClick={() => handleCompanyClick(company)}
                          className={`w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 transition-colors flex items-center justify-between gap-3 ${
                            selectedCompany?.ticker === company.ticker ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                          }`}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="w-10 h-10 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                              {company.ticker.slice(0, 3)}
                            </div>
                            <div className="min-w-0">
                              <div className="font-medium text-slate-900 truncate">{company.name}</div>
                              <div className="text-xs text-slate-500">{company.ticker}</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            {company.hasTransitions ? (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                                {company.transitionCount} transition{company.transitionCount !== 1 ? 's' : ''}
                              </span>
                            ) : (
                              <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">
                                No transitions
                              </span>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>

          {/* Right Panel - Transition Selection & Preview */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden sticky top-6"
            >
              {selectedCompany ? (
                <>
                  {/* Selected Company Header */}
                  <div className="bg-slate-800 text-white p-5">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center font-bold text-sm">
                        {selectedCompany.ticker}
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">{selectedCompany.name}</h3>
                        <p className="text-slate-400 text-xs">{selectedCompany.sector}</p>
                      </div>
                    </div>
                  </div>

                  {/* Transitions List */}
                  <div className="p-4">
                    {selectedCompany.hasTransitions ? (
                      <>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                          CEO Transitions ({selectedCompany.transitionCount})
                        </h4>
                        <div className="space-y-2 max-h-[320px] overflow-y-auto">
                          {selectedCompany.transitions.map((transition, idx) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedTransition(transition)}
                              className={`w-full text-left p-3 rounded-lg border transition-all ${
                                selectedTransition === transition
                                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1.5">
                                <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded">
                                  {formatDateShort(transition.transitionDate)}
                                </span>
                              </div>
                              <div className="flex items-center gap-1.5 text-sm">
                                <span className="text-slate-600 truncate">{transition.previousCEO}</span>
                                <ArrowRight className="w-3 h-3 text-slate-400 flex-shrink-0" />
                                <span className="font-semibold text-slate-900 truncate">{transition.newCEO}</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="py-8 text-center">
                        <Building2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-sm text-slate-500">No CEO transitions found in SEC filings for this company.</p>
                      </div>
                    )}
                  </div>

                  {/* Selected Transition Preview */}
                  <AnimatePresence>
                    {selectedTransition && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="border-t border-slate-200"
                      >
                        <div className="p-4 bg-slate-50">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                            Ready to Analyze
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div>
                              <span className="text-slate-500">Company:</span>{' '}
                              <span className="font-medium text-slate-900">{selectedCompany.name}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Outgoing:</span>{' '}
                              <span className="font-medium text-slate-900">{selectedTransition.previousCEO}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Incoming:</span>{' '}
                              <span className="font-medium text-slate-900">{selectedTransition.newCEO}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Est. Date:</span>{' '}
                              <span className="font-medium text-slate-900">{formatDateShort(selectedTransition.transitionDate)}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Analyze Button */}
                  <div className="p-4 border-t border-slate-200">
                    <Button
                      onClick={handleAnalyze}
                      disabled={!selectedTransition}
                      className="w-full h-12 text-base font-medium bg-slate-900 hover:bg-slate-800 text-white shadow-md hover:shadow-lg transition-all rounded-lg"
                    >
                      Analyze Transition
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center">
                  <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="font-bold text-slate-900 mb-1">Select a Company</h3>
                  <p className="text-sm text-slate-500">
                    Choose a company from the list to view its CEO transitions and begin analysis.
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
