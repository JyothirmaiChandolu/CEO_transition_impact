export interface IndexConfig {
  key: string;
  name: string;
  description: string;
  benchmark_ticker: string;
}

export interface CompanyMetadata {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  country: string;
  employees: number | null;
  marketCap: number | null;
  website: string;
}

export interface CEOTransition {
  previousCEO: string;
  newCEO: string;
  transitionDate: string; // YYYY-MM-DD (verified from SEC filings)
  startDate?: string;     // Previous CEO start date (for context)
  endDate?: string;       // Previous CEO end date (equals transition date)
  filingBefore?: string;  // (Deprecated - kept for compatibility)
  filingAfter?: string;   // (Deprecated - kept for compatibility)
}

export interface Company {
  ticker: string;
  name: string;
  sector: string;
  hasTransitions: boolean;
  transitionCount: number;
  transitions: CEOTransition[];
  dataPoints: number;
}

export interface CompaniesData {
  companies: Company[];
  stats: {
    totalCompanies: number;
    companiesWithTransitions: number;
    totalTransitions: number;
    dateRange: string;
    stockDataFiles: number;
  };
}

export interface StockDataPoint {
  date: string;   // YYYY-MM-DD
  ticker: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockData {
  ticker: string;
  total_records: number;
  data: StockDataPoint[];
}

// Processed chart data point for display
export interface ChartDataPoint {
  date: string;
  dateLabel: string;
  close: number;
  open: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
  isTransitionDate?: boolean;
}

// Macro-economic context
export interface MacroEconomicContextData {
  in_recession: boolean;
  recession_period?: string;
  context: string;
}

// Recession details
export interface RecessionDetail {
  name: string;
  start: string;
  end: string;
  durationMonths: number;
}

// Macro summary statistics
export interface MacroSummary {
  totalRecessionPeriods: number;
  totalRecessionDays: number;
  recessionPercentage: number;
  recessions: RecessionDetail[];
}

// CEO Transition Impact
export interface TransitionImpact {
  transition_date: string;
  transition_price: number;
  impact_90days_pct: number;
  impact_1year_pct: number;
  impact_3year_pct: number | null;
  pre_transition_trend_90d_pct: number;
  macro_economic_context: MacroEconomicContextData;
  analysis_note: string;
}

// KPI Data structure
export interface KPIData {
  ticker: string;
  transition_impact: TransitionImpact;
  macro_summary?: MacroSummary;
  risk_metrics?: {
    daily_volatility_pct: number;
  };
  price_metrics?: {
    volatility_level: string;
  };
}

// Recession Period Details
export interface RecessionPeriod {
  name: string;
  period: {
    start: string;
    end: string;
    duration_months: number;
  };
  peak: {
    date: string;
    price: number;
  };
  trough: {
    date: string;
    price: number;
  };
  decline: {
    amount: number;
    percentage: number;
    vs_benchmark: string;
  };
  recovery: {
    date: string;
    price: number;
    gain_percentage: number;
  };
}

// Recession Impact Analysis
export interface RecessionImpactAnalysis {
  timestamp: string;
  index: string;
  benchmark_decline: string;
  recessions: RecessionPeriod[];
  summary?: {
    total_recessions_analyzed: number;
    average_decline: number;
    max_decline: number;
    min_decline: number;
    within_benchmark: number;
    above_benchmark: number;
    below_benchmark: number;
  };
}

// CEO Outlier Result (for performance and tenure outliers)
export interface CompanyOutlierResult {
  ticker: string;
  company_name: string;
  ceo_name: string;
  transition_date: string;
  tenure_days?: number;
  tenure_label?: string;
  impact_90days_pct?: number;
  impact_1year_pct: number;
  daily_volatility_pct?: number;
  z_score_90days?: number;
  z_score_1year?: number;
  z_score_volatility?: number;
  z_score_tenure?: number;
  composite_z_score: number;
  percentile_90days?: number;
  percentile_1year?: number;
  percentile_tenure?: number;
  is_outlier: boolean;
  outlier_strength: 'STRONG' | 'MODERATE' | 'NORMAL';
  outlier_status: 'OUTLIER_HIGH' | 'OUTLIER_LOW' | 'NORMAL';
  macro_context?: string;
}

// Company Stock Outlier Result
export interface CompanyStockOutlierResult {
  ticker: string;
  company_name: string;
  total_return_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  z_total_return: number;
  z_volatility_ann: number;
  z_sharpe: number;
  z_drawdown: number;
  composite_company_z: number;
  percentile_total_return: number;
  percentile_sharpe: number;
  is_outlier: boolean;
  outlier_strength: 'STRONG' | 'MODERATE' | 'NORMAL';
  outlier_status: 'OUTLIER_HIGH' | 'OUTLIER_LOW' | 'NORMAL';
}

// Full Sector Outlier Analysis Data
export interface SectorOutlierData {
  sector: string;
  total_ceos_analyzed: number;
  total_companies_analyzed: number;
  outlier_count: number;
  sector_statistics: {
    ceo_performance: {
      mean_90day: number;
      std_90day: number;
      mean_1year: number;
      std_1year: number;
    };
    tenure: {
      mean_tenure_days: number;
      std_tenure_days: number;
    };
    company: {
      mean_total_return: number;
      std_total_return: number;
      mean_sharpe: number;
      std_sharpe: number;
    };
  };
  performance_outliers: {
    high_performers: CompanyOutlierResult[];
    low_performers: CompanyOutlierResult[];
    all_ceos: CompanyOutlierResult[];
  };
  tenure_outliers: {
    long_tenure: CompanyOutlierResult[];
    short_tenure: CompanyOutlierResult[];
    all_ceos: CompanyOutlierResult[];
  };
  company_outliers: {
    high_performers: CompanyStockOutlierResult[];
    low_performers: CompanyStockOutlierResult[];
    all_companies: CompanyStockOutlierResult[];
  };
}

// Global CEO Ranking Result
export interface CEORankingResult {
  rank: number;
  ticker: string;
  company_name: string;
  sector: string;
  ceo_name: string;
  transition_date: string;
  impact_1year_pct: number;
  impact_90days_pct: number;
  impact_3year_pct: number | null;
  daily_volatility_pct: number;
  tenure_days: number;
  tenure_label: string;
  tenure_efficiency: number;
  macro_context: string;
  composite_score: number;
  macro_multiplier: number;
  percentile_global: number;
  score_breakdown: {
    z_1year: number;
    z_90day: number;
    z_vol: number;
    z_tenure_eff: number;
  };
}

// Global Company Ranking Result
export interface CompanyRankingResult {
  rank: number;
  ticker: string;
  company_name: string;
  sector: string;
  total_return_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  composite_score: number;
  percentile_global: number;
  score_breakdown: {
    z_return: number;
    z_sharpe: number;
    z_vol: number;
    z_drawdown: number;
  };
}

// CEO Rankings Response
export interface CEORankingsData {
  total_analyzed: number;
  macro_adjusted: boolean;
  top_ceos: CEORankingResult[];
  global_stats: {
    mean_1year: number;
    std_1year: number;
    mean_90day: number;
    std_90day: number;
  };
}

// Company Rankings Response
export interface CompanyRankingsData {
  total_analyzed: number;
  top_companies: CompanyRankingResult[];
  global_stats: {
    mean_return: number;
    std_return: number;
    mean_sharpe: number;
    std_sharpe: number;
  };
}
