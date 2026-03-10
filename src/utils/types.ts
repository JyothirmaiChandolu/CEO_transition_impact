export interface CEOTransition {
  previousCEO: string;
  newCEO: string;
  transitionDate: string; // YYYY-MM-DD (estimated midpoint)
  filingBefore: string;   // Last 10-K filing date with previous CEO
  filingAfter: string;    // First 10-K filing date with new CEO
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
  d: string;  // date YYYY-MM-DD
  c: number;  // close (adjusted)
  o: number | null;  // open
  h: number | null;  // high
  l: number | null;  // low
  v: number | null;  // volume
}

export interface StockData {
  ticker: string;
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
