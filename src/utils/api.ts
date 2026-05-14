/**
 * API Client for FastAPI Backend
 * Replaces dataLoader.ts - fetches from backend instead of static files
 */

import type {
  CompaniesData,
  StockData,
  KPIData,
  RecessionImpactAnalysis,
  SectorOutlierData,
  CEORankingsData,
  CompanyRankingsData,
  IndexConfig,
  CompanyMetadata,
} from './types';

const API_BASE_URL = '/api';

// Per-index caches
const stockDataCache = new Map<string, StockData>();   // key: "{index}_{ticker}"
const kpiCache = new Map<string, KPIData>();            // key: "{index}_{ticker}" or "{index}_{ticker}_{date}"
const companiesCache = new Map<string, CompaniesData>(); // key: index
let indicesCache: IndexConfig[] | null = null;

/**
 * Load list of available indices
 */
export async function loadIndices(): Promise<IndexConfig[]> {
  if (indicesCache) return indicesCache;
  try {
    const response = await fetch(`${API_BASE_URL}/indices`);
    if (!response.ok) throw new Error('Failed to load indices');
    indicesCache = await response.json();
    return indicesCache as IndexConfig[];
  } catch (error) {
    console.error('Error loading indices:', error);
    throw error;
  }
}

/**
 * Load companies metadata for an index
 */
export async function loadCompanies(index: string): Promise<CompaniesData> {
  if (companiesCache.has(index)) return companiesCache.get(index)!;

  try {
    const response = await fetch(`${API_BASE_URL}/${index}/companies`);
    if (!response.ok) throw new Error('Failed to load companies');
    const raw = await response.json();
    const data: CompaniesData = {
      companies: raw.companies ?? [],
      stats: {
        totalCompanies: raw.totalCompanies ?? 0,
        companiesWithTransitions: raw.companiesWithTransitions ?? 0,
        totalTransitions: raw.totalTransitions ?? 0,
        dateRange: raw.dateRange ?? '',
        stockDataFiles: raw.stockDataFiles ?? 0,
      },
    };
    companiesCache.set(index, data);
    return data;
  } catch (error) {
    console.error('Error loading companies:', error);
    throw error;
  }
}

/**
 * Load stock data for a ticker within an index
 */
export async function loadStockData(ticker: string, index: string): Promise<StockData | null> {
  const cacheKey = `${index}_${ticker}`;
  if (stockDataCache.has(cacheKey)) return stockDataCache.get(cacheKey)!;

  try {
    const response = await fetch(`${API_BASE_URL}/${index}/stocks/${ticker}`);
    if (!response.ok) return null;

    const data = await response.json();
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
        isTransitionDate: false,
      })),
    };

    stockDataCache.set(cacheKey, chartData);
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
  endDate: string,
  index: string
): Promise<StockData | null> {
  try {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    const response = await fetch(`${API_BASE_URL}/${index}/stocks/${ticker}/range?${params}`);
    if (!response.ok) return null;

    const data = await response.json();
    return {
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
        isTransitionDate: false,
      })),
    };
  } catch (error) {
    console.error(`Error loading stock range for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load KPI metrics for a ticker
 */
export async function loadKPIs(ticker: string, index: string, transitionDate?: string): Promise<KPIData | null> {
  const cacheKey = transitionDate ? `${index}_${ticker}_${transitionDate}` : `${index}_${ticker}`;
  if (kpiCache.has(cacheKey)) return kpiCache.get(cacheKey)!;

  try {
    const url = transitionDate
      ? `${API_BASE_URL}/${index}/kpis/${ticker}?transition_date=${transitionDate}`
      : `${API_BASE_URL}/${index}/kpis/${ticker}`;

    const response = await fetch(url);
    if (!response.ok) return null;

    const kpis = await response.json();
    kpiCache.set(cacheKey, kpis);
    return kpis;
  } catch (error) {
    console.error(`Error loading KPIs for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load price metrics
 */
export async function loadPriceMetrics(ticker: string, index: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/${index}/kpis/${ticker}/price`);
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
export async function loadVolumeMetrics(ticker: string, index: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/${index}/kpis/${ticker}/volume`);
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
export async function loadRiskMetrics(ticker: string, index: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/${index}/kpis/${ticker}/risk`);
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
export async function loadTransitionImpact(ticker: string, index: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/${index}/kpis/${ticker}/transition`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading transition impact for ${ticker}:`, error);
    return null;
  }
}

/**
 * Load index data (e.g., Russell 2000 market index — global, not per-data-index)
 */
export async function loadIndexData(indexTicker: string): Promise<StockData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/index/${indexTicker}`);
    if (!response.ok) return null;

    const data = await response.json();
    return {
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
        isTransitionDate: false,
      })),
    };
  } catch (error) {
    console.error(`Error loading index data for ${indexTicker}:`, error);
    return null;
  }
}

/**
 * Load recession impact analysis
 */
export async function loadRecessionAnalysis(): Promise<RecessionImpactAnalysis | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/recession-impact`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error loading recession impact analysis:', error);
    return null;
  }
}

/**
 * Load sector outlier analysis
 */
export async function loadSectorOutliers(sector: string, index: string, periodYears?: number): Promise<SectorOutlierData | null> {
  try {
    const encodedSector = encodeURIComponent(sector);
    const url = periodYears
      ? `${API_BASE_URL}/${index}/outliers/sector/${encodedSector}?period_years=${periodYears}`
      : `${API_BASE_URL}/${index}/outliers/sector/${encodedSector}`;
    const response = await fetch(url);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(`Error loading outliers for sector ${sector}:`, error);
    return null;
  }
}

/**
 * Load global CEO rankings
 */
export async function loadCEORankings(index: string, topN: number = 20, macroAdjusted: boolean = true): Promise<CEORankingsData | null> {
  try {
    const params = new URLSearchParams({
      top_n: topN.toString(),
      macro_adjusted: macroAdjusted.toString(),
    });
    const response = await fetch(`${API_BASE_URL}/${index}/rankings/ceos?${params}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error loading CEO rankings:', error);
    return null;
  }
}

/**
 * Load global company rankings
 */
export async function loadCompanyRankings(index: string, topN: number = 20): Promise<CompanyRankingsData | null> {
  try {
    const params = new URLSearchParams({ top_n: topN.toString() });
    const response = await fetch(`${API_BASE_URL}/${index}/rankings/companies?${params}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error loading company rankings:', error);
    return null;
  }
}

/**
 * Load company archive (metadata) for an index
 */
export async function loadCompanyArchive(index: string): Promise<CompanyMetadata[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/${index}/archive`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.companies ?? [];
  } catch (error) {
    console.error(`Error loading company archive for ${index}:`, error);
    return [];
  }
}

/**
 * Clear caches for a specific index
 */
export function clearIndexCache(index: string) {
  companiesCache.delete(index);
  for (const key of [...stockDataCache.keys()]) {
    if (key.startsWith(`${index}_`)) stockDataCache.delete(key);
  }
  for (const key of [...kpiCache.keys()]) {
    if (key.startsWith(`${index}_`)) kpiCache.delete(key);
  }
}

/**
 * Clear all caches
 */
export function clearCaches() {
  stockDataCache.clear();
  kpiCache.clear();
  companiesCache.clear();
  indicesCache = null;
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
