import type { CompaniesData, StockData, StockDataPoint, ChartDataPoint } from './types';

const DATA_BASE = '/data';

let companiesCache: CompaniesData | null = null;
const stockCache = new Map<string, StockData>();

export async function loadCompanies(): Promise<CompaniesData> {
  if (companiesCache) return companiesCache;
  const res = await fetch(`${DATA_BASE}/companies.json`);
  if (!res.ok) throw new Error('Failed to load companies data');
  companiesCache = await res.json();
  return companiesCache!;
}

export async function loadStockData(ticker: string): Promise<StockData | null> {
  if (stockCache.has(ticker)) return stockCache.get(ticker)!;
  try {
    const res = await fetch(`${DATA_BASE}/stocks/${ticker}.json`);
    if (!res.ok) return null;
    const data: StockData = await res.json();
    stockCache.set(ticker, data);
    return data;
  } catch {
    return null;
  }
}

// Get stock data within a date range around a transition
export function getStockDataAroundTransition(
  stockData: StockDataPoint[],
  transitionDate: string,
  daysBefore: number = 365,
  daysAfter: number = 365
): ChartDataPoint[] {
  const transDate = new Date(transitionDate);
  const startDate = new Date(transDate);
  startDate.setDate(startDate.getDate() - daysBefore);
  const endDate = new Date(transDate);
  endDate.setDate(endDate.getDate() + daysAfter);

  const startStr = startDate.toISOString().split('T')[0];
  const endStr = endDate.toISOString().split('T')[0];

  return stockData
    .filter(d => d.d >= startStr && d.d <= endStr)
    .map(d => ({
      date: d.d,
      dateLabel: formatDateLabel(d.d),
      close: d.c,
      open: d.o,
      high: d.h,
      low: d.l,
      volume: d.v,
      isTransitionDate: d.d === findClosestDate(stockData, transitionDate)
    }));
}

// Find the closest trading date to a given date
function findClosestDate(data: StockDataPoint[], targetDate: string): string {
  let closest = data[0]?.d || '';
  let minDiff = Infinity;
  const target = new Date(targetDate).getTime();

  for (const d of data) {
    const diff = Math.abs(new Date(d.d).getTime() - target);
    if (diff < minDiff) {
      minDiff = diff;
      closest = d.d;
    }
    if (diff > minDiff) break; // data is sorted, so we can break early
  }
  return closest;
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

// Calculate impact metrics around a transition
export function calculateTransitionMetrics(
  stockData: StockDataPoint[],
  transitionDate: string
) {
  const transDate = new Date(transitionDate);

  // 90 days before
  const before90 = new Date(transDate);
  before90.setDate(before90.getDate() - 90);
  // 90 days after
  const after90 = new Date(transDate);
  after90.setDate(after90.getDate() + 90);
  // 365 days after
  const after365 = new Date(transDate);
  after365.setDate(after365.getDate() + 365);

  const before90Str = before90.toISOString().split('T')[0];
  const transStr = transitionDate;
  const after90Str = after90.toISOString().split('T')[0];
  const after365Str = after365.toISOString().split('T')[0];

  // Find closest data points
  const priceBefore90 = findClosestPrice(stockData, before90Str);
  const priceAtTransition = findClosestPrice(stockData, transStr);
  const priceAfter90 = findClosestPrice(stockData, after90Str);
  const priceAfter365 = findClosestPrice(stockData, after365Str);

  // Calculate metrics
  const impact90Days = priceAtTransition && priceAfter90
    ? ((priceAfter90 - priceAtTransition) / priceAtTransition) * 100
    : null;

  const impact1Year = priceAtTransition && priceAfter365
    ? ((priceAfter365 - priceAtTransition) / priceAtTransition) * 100
    : null;

  const preTransitionTrend = priceBefore90 && priceAtTransition
    ? ((priceAtTransition - priceBefore90) / priceBefore90) * 100
    : null;

  // Calculate volatility (standard deviation of daily returns around transition)
  const windowData = stockData.filter(d => {
    return d.d >= before90Str && d.d <= after90Str;
  });
  const returns: number[] = [];
  for (let i = 1; i < windowData.length; i++) {
    if (windowData[i].c && windowData[i - 1].c) {
      returns.push((windowData[i].c - windowData[i - 1].c) / windowData[i - 1].c);
    }
  }
  const avgReturn = returns.length > 0 ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
  const variance = returns.length > 0
    ? returns.reduce((a, b) => a + (b - avgReturn) ** 2, 0) / returns.length
    : 0;
  const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized volatility

  return {
    priceAtTransition: priceAtTransition ? Math.round(priceAtTransition * 100) / 100 : null,
    priceAfter90: priceAfter90 ? Math.round(priceAfter90 * 100) / 100 : null,
    priceAfter365: priceAfter365 ? Math.round(priceAfter365 * 100) / 100 : null,
    impact90Days: impact90Days !== null ? Math.round(impact90Days * 100) / 100 : null,
    impact1Year: impact1Year !== null ? Math.round(impact1Year * 100) / 100 : null,
    preTransitionTrend: preTransitionTrend !== null ? Math.round(preTransitionTrend * 100) / 100 : null,
    volatility: Math.round(volatility * 100) / 100,
    volatilityLevel: volatility > 40 ? 'High' : volatility > 25 ? 'Medium' : 'Low'
  };
}

function findClosestPrice(data: StockDataPoint[], targetDate: string): number | null {
  let closest: StockDataPoint | null = null;
  let minDiff = Infinity;
  const target = new Date(targetDate).getTime();

  for (const d of data) {
    const diff = Math.abs(new Date(d.d).getTime() - target);
    if (diff < minDiff) {
      minDiff = diff;
      closest = d;
    }
    if (new Date(d.d).getTime() > target + 7 * 24 * 3600 * 1000) break;
  }
  return closest?.c ?? null;
}

// Get all unique sectors from companies
export function getSectors(companies: CompaniesData): string[] {
  const sectors = new Set<string>();
  companies.companies.forEach(c => {
    if (c.sector && c.sector !== 'Unknown') sectors.add(c.sector);
  });
  return [...sectors].sort();
}

// Format a date string nicely
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

export function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}
