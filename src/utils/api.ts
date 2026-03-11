/**
 * API Client for FastAPI Backend
 * Replaces dataLoader.ts - fetches from backend instead of static files
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ChartDataPoint {
  date: string;
  dateLabel: string;
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  isTransitionDate: boolean;
}

export interface StockData {
  ticker: string;
  total_records: number;
  data: ChartDataPoint[];
}

export interface KPIData {
  ticker: string;
  last_updated: string;
  price_metrics?: Record<string, any>;
  volume_metrics?: Record<string, any>;
  risk_metrics?: Record<string, any>;
  transition_impact?: Record<string, any>;
}

export interface Company {
  name: string;
  ticker: string;
  sector: string;
  transitions: Array<{
    transitionDate: string;
    previousCEO: string;
    newCEO: string;
    filingBefore: string;
    filingAfter: string;
  }>;
}

export interface CompaniesData {
  companies: Company[];
}

// Cache for loaded data
const stockDataCache = new Map<string, StockData>();
const kpiCache = new Map<string, KPIData>();
let companiesCache: CompaniesData | null = null;

/**
 * Load companies metadata
 */
export async function loadCompanies(): Promise<CompaniesData> {
  if (companiesCache) return companiesCache;

  try {
    const response = await fetch(`${API_BASE_URL}/companies`);
    if (!response.ok) throw new Error('Failed to load companies');
    companiesCache = await response.json();
    return companiesCache;
  } catch (error) {
    console.error('Error loading companies:', error);
    throw error;
  }
}

/**
 * Load stock data for a ticker
 */
export async function loadStockData(ticker: string): Promise<StockData | null> {
  // Check cache first
  if (stockDataCache.has(ticker)) {
    return stockDataCache.get(ticker)!;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/stocks/${ticker}`);
    if (!response.ok) return null;

    const data = await response.json();

    // Transform API response to ChartDataPoint format
    const chartData: StockData = {
      ticker: data.ticker,
      total_records: data.total_records,
      data: data.data.map((point: any) => ({
        date: point.date,
        dateLabel: formatDateLabel(point.date),
        close: point.close,
        open: point.open,
        high: point.high,
        low: point.low,
        volume: point.volume,
        isTransitionDate: false
      }))
    };

    stockDataCache.set(ticker, chartData);
    return chartData;
  } catch (error) {
    console.error(`Error loading stock data for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load stock data within a date range
 */
export async function loadStockDataRange(
  ticker: string,
  startDate: string,
  endDate: string
): Promise<StockData | null> {
  try {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    const response = await fetch(`${API_BASE_URL}/stocks/${ticker}/range?${params}`);
    if (!response.ok) return null;

    const data = await response.json();

    const chartData: StockData = {
      ticker: data.ticker,
      total_records: data.records,
      data: data.data.map((point: any) => ({
        date: point.date,
        dateLabel: formatDateLabel(point.date),
        close: point.close,
        open: point.open,
        high: point.high,
        low: point.low,
        volume: point.volume,
        isTransitionDate: false
      }))
    };

    return chartData;
  } catch (error) {
    console.error(`Error loading stock range for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load KPI metrics for a ticker
 */
export async function loadKPIs(ticker: string): Promise<KPIData | null> {
  // Check cache first
  if (kpiCache.has(ticker)) {
    return kpiCache.get(ticker)!;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/kpis/${ticker}`);
    if (!response.ok) return null;

    const kpis = await response.json();
    kpiCache.set(ticker, kpis);
    return kpis;
  } catch (error) {
    console.error(`Error loading KPIs for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load price metrics
 */
export async function loadPriceMetrics(ticker: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/kpis/${ticker}/price`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading price metrics for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load volume metrics
 */
export async function loadVolumeMetrics(ticker: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/kpis/${ticker}/volume`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading volume metrics for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load risk metrics
 */
export async function loadRiskMetrics(ticker: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/kpis/${ticker}/risk`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading risk metrics for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load transition impact metrics
 */
export async function loadTransitionImpact(ticker: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/kpis/${ticker}/transition`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading transition impact for ${ticker}:`, error);
    return null;
  }
}

/**
 * Format date for display
 */
function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

/**
 * Format date nicely
 */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

/**
 * Format date short
 */
export function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}

/**
 * Get sectors from companies data
 */
export function getSectors(companies: CompaniesData): string[] {
  const sectors = new Set<string>();
  companies.companies.forEach(c => {
    if (c.sector && c.sector !== 'Unknown') sectors.add(c.sector);
  });
  return [...sectors].sort();
}

/**
 * Clear caches
 */
export function clearCaches() {
  stockDataCache.clear();
  kpiCache.clear();
  companiesCache = null;
}
