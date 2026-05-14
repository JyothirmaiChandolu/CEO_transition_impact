import { useState, useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, Loader } from 'lucide-react';
import { loadSectorOutliers } from '../utils/api';
import type { Company, SectorOutlierData } from '../utils/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { MetricTooltip } from './MetricTooltip';
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

interface OutlierAnalysisProps {
  companies: Company[];
  onBack: () => void;
  index: string;
}

const SECTOR_IMAGES: Record<string, string> = {
  'Information Technology': '/sectors/information.jpeg',
  'Technology': '/sectors/information.jpeg',
  'Health Care': '/sectors/healthcare.jpeg',
  'Healthcare': '/sectors/healthcare.jpeg',
  'Financials': '/sectors/financials.jpeg',
  'Financial Services': '/sectors/financials.jpeg',
  'Energy': '/sectors/energy.jpeg',
  'Consumer Discretionary': '/sectors/consumer.jpeg',
  'Consumer Cyclical': '/sectors/consumer.jpeg',
  'Consumer Staples': '/sectors/staples.jpeg',
  'Consumer Defensive': '/sectors/staples.jpeg',
  'Communication Services': '/sectors/communication.jpeg',
  'Industrials': '/sectors/industrials.jpeg',
  'Materials': '/sectors/materials.jpeg',
  'Basic Materials': '/sectors/materials.jpeg',
  'Real Estate': '/sectors/real_estate.jpeg',
  'Utilities': '/sectors/utilities.jpeg',
};

function SectorIcon({ sector, width = 280, height = 180 }: { sector: string; width?: number; height?: number }) {
  const src = SECTOR_IMAGES[sector];
  if (!src) return <span style={{ fontSize: 36 }}>📊</span>;
  return (
    <img src={src} alt={sector}
      style={{ width, height, objectFit: 'cover', borderRadius: 8, display: 'block', flexShrink: 0 }}
    />
  );
}

function OutlierBadge({ strength, status }: { strength: string; status: string }) {
  const style: CSSProperties =
    status === 'OUTLIER_HIGH'
      ? strength === 'STRONG'
        ? { background: '#059669', color: '#fff', border: 'none' }
        : { background: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' }
      : status === 'OUTLIER_LOW'
      ? strength === 'STRONG'
        ? { background: '#dc2626', color: '#fff', border: 'none' }
        : { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' }
      : { background: '#e2e8f0', color: '#475569', border: 'none' };
  const stars = strength === 'STRONG' ? '★★★' : strength === 'MODERATE' ? '★★' : '✓';
  return (
    <span style={{
      ...style, padding: '3px 10px', borderRadius: 999,
      fontSize: '0.72rem', fontWeight: 700, whiteSpace: 'nowrap', display: 'inline-block',
    }}>
      {stars} {strength}
    </span>
  );
}

// ── Vertical bar chart ──────────────────────────────────────────────────────

interface BarItem {
  shortLabel: string;
  fullLabel: string;
  value: number;
  status: string;
  strength: string;
}

function VerticalBarChart({
  items, mean, upper, lower, yLabel, yFormatter,
  highColor = '#059669', lowColor = '#dc2626',
}: {
  items: BarItem[];
  mean: number; upper: number; lower: number;
  yLabel: string; yFormatter: (v: number) => string;
  highColor?: string; lowColor?: string;
}) {
  const sorted = [...items].sort((a, b) => b.value - a.value);

  const getColor = (status: string) => {
    if (status === 'OUTLIER_HIGH') return highColor;
    if (status === 'OUTLIER_LOW') return lowColor;
    return '#94a3b8';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload as BarItem;
    const color = getColor(d.status);
    return (
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.8rem', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <p style={{ fontWeight: 700, color: '#0f172a', margin: '0 0 4px' }}>{d.fullLabel}</p>
        <p style={{ color, fontWeight: 600, margin: 0 }}>{yFormatter(d.value)}</p>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sorted} margin={{ top: 16, right: 24, bottom: 44, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="shortLabel"
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          angle={-38}
          textAnchor="end"
          interval={0}
          height={50}
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tickFormatter={yFormatter}
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
          label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: 15, fontSize: 11, fill: '#64748b' }}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <ReferenceLine y={mean} stroke="#64748b" strokeDasharray="5 5" strokeWidth={1.5}
          label={{ value: 'Mean', fontSize: 9, fill: '#64748b', position: 'insideTopRight' }} />
        <ReferenceLine y={upper} stroke={highColor} strokeDasharray="3 3" strokeWidth={1}
          label={{ value: '+2σ', fontSize: 9, fill: highColor, position: 'insideTopRight' }} />
        <ReferenceLine y={lower} stroke={lowColor} strokeDasharray="3 3" strokeWidth={1}
          label={{ value: '-2σ', fontSize: 9, fill: lowColor, position: 'insideTopRight' }} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
          {sorted.map((entry, i) => (
            <Cell
              key={`cell-${i}`}
              fill={getColor(entry.status)}
              fillOpacity={entry.status === 'NORMAL' ? 0.45 : 0.9}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Chart legend ────────────────────────────────────────────────────────────

function BarLegend({ items }: { items: { color: string; label: string; opacity?: number }[] }) {
  return (
    <div style={{ display: 'flex', gap: '1.25rem', justifyContent: 'center', marginTop: '0.5rem', fontSize: '0.78rem', color: '#475569' }}>
      {items.map(it => (
        <span key={it.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 12, height: 12, borderRadius: 3, background: it.color, opacity: it.opacity ?? 1, display: 'inline-block' }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}

// ── Outlier spotlight card ──────────────────────────────────────────────────

function SpotlightCard({
  name, identifier, date, primaryLabel, primaryValue, primaryColor,
  metrics, outlierStatus, outlierStrength, insight, isHigh,
}: {
  name: string; identifier: string; date?: string;
  primaryLabel: string; primaryValue: string; primaryColor: string;
  metrics: { label: string; value: string }[];
  outlierStatus: string; outlierStrength: string; insight: string; isHigh: boolean;
}) {
  const borderColor = isHigh ? '#6ee7b7' : '#fca5a5';
  const bgColor = isHigh ? '#f0fdf4' : '#fef2f2';

  return (
    <div style={{ background: bgColor, border: `2px solid ${borderColor}`, borderRadius: 12, padding: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.78rem', color: '#64748b' }}>{identifier}</span>
          <p style={{ fontWeight: 700, color: '#0f172a', margin: '2px 0 0', fontSize: '0.95rem', lineHeight: 1.3 }}>{name}</p>
          {date && <p style={{ color: '#94a3b8', fontSize: '0.72rem', margin: '2px 0 0' }}>{date}</p>}
        </div>
        <OutlierBadge strength={outlierStrength} status={outlierStatus} />
      </div>

      <div style={{ textAlign: 'center', padding: '0.5rem 0 0.75rem' }}>
        <p style={{ fontSize: '2.4rem', fontWeight: 800, color: primaryColor, margin: 0, lineHeight: 1 }}>{primaryValue}</p>
        <p style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginTop: 4 }}>{primaryLabel}</p>
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', paddingBottom: 12, borderBottom: '1px solid ' + borderColor }}>
        {metrics.map(m => (
          <div key={m.label} style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '0.82rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>{m.value}</p>
            <p style={{ fontSize: '0.68rem', color: '#94a3b8', margin: 0 }}>{m.label}</p>
          </div>
        ))}
      </div>

      <p style={{ fontSize: '0.8rem', color: '#475569', fontStyle: 'italic', margin: '10px 0 0' }}>{insight}</p>
    </div>
  );
}

// ── Normal performers collapsible list ──────────────────────────────────────

function NormalList({ items }: { items: { name: string; ticker: string; date: string; primary: string; primaryColor: string; secondary: string }[] }) {
  if (items.length === 0) return null;
  return (
    <details style={{ marginTop: '1.5rem' }}>
      <summary style={{ cursor: 'pointer', fontSize: '0.875rem', color: '#64748b', fontWeight: 500, userSelect: 'none' }}>
        {items.length} normal performers (within ±2σ) ▾
      </summary>
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 3 }}>
        {items.map((r, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: '1rem', padding: '6px 10px',
            background: i % 2 === 0 ? '#f8fafc' : '#fff', borderRadius: 6, fontSize: '0.8rem',
          }}>
            <span style={{ fontWeight: 600, color: '#0f172a', minWidth: 160 }}>{r.name}</span>
            <span style={{ fontFamily: 'monospace', color: '#64748b', minWidth: 48 }}>{r.ticker}</span>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem', minWidth: 80 }}>{r.date}</span>
            <span style={{ color: r.primaryColor, fontWeight: 600, minWidth: 64 }}>{r.primary}</span>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>{r.secondary}</span>
          </div>
        ))}
      </div>
    </details>
  );
}

// ── Tabs ────────────────────────────────────────────────────────────────────

function PerformanceOutliersTab({ data }: { data: SectorOutlierData }) {
  const mean = data.sector_statistics.ceo_performance.mean_1year;
  const std = data.sector_statistics.ceo_performance.std_1year;
  const allCeos = data.performance_outliers.all_ceos;

  const barItems: BarItem[] = allCeos.map(r => ({
    shortLabel: r.ceo_name.split(' ').slice(-1)[0],
    fullLabel: `${r.ceo_name} (${r.ticker})`,
    value: r.impact_1year_pct || 0,
    status: r.outlier_status,
    strength: r.outlier_strength,
  }));

  const high = data.performance_outliers.high_performers;
  const low = data.performance_outliers.low_performers;
  const normal = allCeos.filter(r => r.outlier_strength === 'NORMAL');
  const fmtReturn = (v?: number | null) => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(1)}%` : '—';

  return (
    <div>
      <h3 className="text-lg font-bold text-slate-900 mb-1">1-Year Return by CEO</h3>
      <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem' }}>
        Sorted highest to lowest. Green = outperformer, red = underperformer, gray = normal range.
      </p>

      <VerticalBarChart
        items={barItems} mean={mean} upper={mean + 2 * std} lower={mean - 2 * std}
        yLabel="Return (%)" yFormatter={(v) => `${v.toFixed(0)}%`}
      />
      <BarLegend items={[
        { color: '#059669', label: 'Outperformer (Z > 2)' },
        { color: '#94a3b8', label: 'Normal Range', opacity: 0.45 },
        { color: '#dc2626', label: 'Underperformer (Z < -2)' },
      ]} />

      <div className="grid grid-cols-3 gap-4 mb-6" style={{ marginTop: '1.5rem' }}>
        <div className="bg-slate-100 rounded-lg p-4 text-center">
          <p className="text-slate-600 text-sm flex items-center justify-center gap-1">
            Sector Mean <MetricTooltip text="Average 1-year return across all CEO transitions in this sector." position="top" />
          </p>
          <p className="text-2xl font-bold text-slate-900">{mean.toFixed(1)}%</p>
        </div>
        <div className="bg-slate-100 rounded-lg p-4 text-center">
          <p className="text-slate-600 text-sm flex items-center justify-center gap-1">
            Std Dev <MetricTooltip text="How spread out returns are. Larger = more variation between CEOs." position="top" />
          </p>
          <p className="text-2xl font-bold text-slate-900">±{std.toFixed(1)}%</p>
        </div>
        <div className="bg-slate-100 rounded-lg p-4 text-center">
          <p className="text-slate-600 text-sm flex items-center justify-center gap-1">
            Outlier Threshold <MetricTooltip text="CEOs above or below this range are flagged as outliers (±2 standard deviations)." position="top" />
          </p>
          <p className="text-sm font-bold text-slate-900">&gt;{(mean + 2 * std).toFixed(0)}% or &lt;{(mean - 2 * std).toFixed(0)}%</p>
        </div>
      </div>

      {high.length === 0 && low.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', background: '#f8fafc', borderRadius: 10 }}>
          <p style={{ fontSize: '1rem', fontWeight: 600 }}>No outliers in this sector</p>
          <p style={{ fontSize: '0.85rem', marginTop: 4 }}>All {allCeos.length} CEOs fall within ±2σ of the sector mean.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <h4 style={{ fontWeight: 700, color: '#065f46', marginBottom: 10, fontSize: '0.9rem' }}>⭐ Outperformers</h4>
            {high.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : high.map(r => (
                <div key={`${r.ticker}-${r.transition_date}`} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.ceo_name} identifier={r.ticker} date={r.transition_date}
                    primaryLabel="1-Year Return" primaryValue={fmtReturn(r.impact_1year_pct)}
                    primaryColor="#059669"
                    metrics={[
                      { label: '90-Day', value: fmtReturn(r.impact_90days_pct) },
                      { label: 'Z-Score', value: (r.z_score_1year || 0).toFixed(2) },
                      { label: 'Percentile', value: `${r.percentile_1year}th` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.ceo_name} outperformed ${r.percentile_1year}% of sector peers in their first year.`}
                    isHigh={true}
                  />
                </div>
              ))}
          </div>
          <div>
            <h4 style={{ fontWeight: 700, color: '#991b1b', marginBottom: 10, fontSize: '0.9rem' }}>⚠️ Underperformers</h4>
            {low.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : low.map(r => (
                <div key={`${r.ticker}-${r.transition_date}`} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.ceo_name} identifier={r.ticker} date={r.transition_date}
                    primaryLabel="1-Year Return" primaryValue={fmtReturn(r.impact_1year_pct)}
                    primaryColor="#dc2626"
                    metrics={[
                      { label: '90-Day', value: fmtReturn(r.impact_90days_pct) },
                      { label: 'Z-Score', value: (r.z_score_1year || 0).toFixed(2) },
                      { label: 'Percentile', value: `${r.percentile_1year}th` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.ceo_name} ranked in the bottom ${100 - (r.percentile_1year || 0)}% of sector peers.`}
                    isHigh={false}
                  />
                </div>
              ))}
          </div>
        </div>
      )}

      <NormalList items={normal.map(r => ({
        name: r.ceo_name, ticker: r.ticker, date: r.transition_date || '',
        primary: fmtReturn(r.impact_1year_pct), primaryColor: (r.impact_1year_pct || 0) >= 0 ? '#059669' : '#dc2626',
        secondary: `Z: ${(r.z_score_1year || 0).toFixed(2)}  ·  ${r.percentile_1year}th pct`,
      }))} />
    </div>
  );
}

function TenureOutliersTab({ data }: { data: SectorOutlierData }) {
  const meanDays = data.sector_statistics.tenure.mean_tenure_days;
  const allCeos = data.tenure_outliers.all_ceos;
  const tenureYears = allCeos.map(r => (r.tenure_days || 0) / 365);
  const mean = meanDays / 365;
  const std = tenureYears.length > 1
    ? Math.sqrt(tenureYears.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / tenureYears.length)
    : mean * 0.5;

  const barItems: BarItem[] = allCeos.map(r => ({
    shortLabel: r.ceo_name.split(' ').slice(-1)[0],
    fullLabel: `${r.ceo_name} (${r.ticker}) — ${r.tenure_label}`,
    value: (r.tenure_days || 0) / 365,
    status: r.outlier_status,
    strength: r.outlier_strength,
  }));

  const long = data.tenure_outliers.long_tenure;
  const short = data.tenure_outliers.short_tenure;
  const normal = allCeos.filter(r => r.outlier_strength === 'NORMAL');
  const fmtReturn = (v?: number | null) => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(1)}%` : '—';

  return (
    <div>
      <h3 className="text-lg font-bold text-slate-900 mb-1">Tenure Length by CEO</h3>
      <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem' }}>
        Sorted longest to shortest. Blue = unusually long tenure, amber = unusually short.
      </p>

      <VerticalBarChart
        items={barItems} mean={mean} upper={mean + 2 * std} lower={Math.max(0, mean - 2 * std)}
        yLabel="Years" yFormatter={(v) => `${v.toFixed(1)}y`}
        highColor="#3b82f6" lowColor="#f59e0b"
      />
      <BarLegend items={[
        { color: '#3b82f6', label: 'Long Tenure (Z > 2)' },
        { color: '#94a3b8', label: 'Normal Range', opacity: 0.45 },
        { color: '#f59e0b', label: 'Short Tenure (Z < -2)' },
      ]} />

      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', background: '#f8fafc', borderRadius: 10, padding: '1rem', display: 'flex', gap: '2rem', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Sector Mean Tenure</p>
          <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>{mean.toFixed(1)} yrs</p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Outlier Threshold</p>
          <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>
            &gt;{(mean + 2 * std).toFixed(1)}y or &lt;{Math.max(0, mean - 2 * std).toFixed(1)}y
          </p>
        </div>
      </div>

      {long.length === 0 && short.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', background: '#f8fafc', borderRadius: 10 }}>
          <p style={{ fontSize: '1rem', fontWeight: 600 }}>No tenure outliers in this sector</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <h4 style={{ fontWeight: 700, color: '#1d4ed8', marginBottom: 10, fontSize: '0.9rem' }}>⏰ Long-Tenure CEOs</h4>
            {long.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : long.map(r => (
                <div key={`${r.ticker}-${r.transition_date}`} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.ceo_name} identifier={r.ticker} date={r.transition_date}
                    primaryLabel="Tenure" primaryValue={r.tenure_label || ''}
                    primaryColor="#2563eb"
                    metrics={[
                      { label: '1-Year Return', value: fmtReturn(r.impact_1year_pct) },
                      { label: 'Z-Score', value: (r.z_score_tenure || 0).toFixed(2) },
                      { label: 'Percentile', value: `${r.percentile_tenure}th` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.ceo_name}'s ${r.tenure_label} tenure ranks in the top ${100 - (r.percentile_tenure || 0)}% of CEO tenures in this sector.`}
                    isHigh={true}
                  />
                </div>
              ))}
          </div>
          <div>
            <h4 style={{ fontWeight: 700, color: '#92400e', marginBottom: 10, fontSize: '0.9rem' }}>⚡ Short-Tenure CEOs</h4>
            {short.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : short.map(r => (
                <div key={`${r.ticker}-${r.transition_date}`} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.ceo_name} identifier={r.ticker} date={r.transition_date}
                    primaryLabel="Tenure" primaryValue={r.tenure_label || ''}
                    primaryColor="#d97706"
                    metrics={[
                      { label: '1-Year Return', value: fmtReturn(r.impact_1year_pct) },
                      { label: 'Z-Score', value: (r.z_score_tenure || 0).toFixed(2) },
                      { label: 'Percentile', value: `${r.percentile_tenure}th` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.ceo_name}'s ${r.tenure_label} is among the shortest in this sector (${r.percentile_tenure}th percentile).`}
                    isHigh={false}
                  />
                </div>
              ))}
          </div>
        </div>
      )}

      <NormalList items={normal.map(r => ({
        name: r.ceo_name, ticker: r.ticker, date: r.transition_date || '',
        primary: r.tenure_label || '', primaryColor: '#0f172a',
        secondary: `Z: ${(r.z_score_tenure || 0).toFixed(2)}  ·  ${r.percentile_tenure}th pct`,
      }))} />
    </div>
  );
}

function CompanyOutliersTab({ data }: { data: SectorOutlierData }) {
  const mean = data.sector_statistics.company.mean_total_return;
  const allCompanies = data.company_outliers.all_companies;
  const returns = allCompanies.map(r => r.total_return_pct || 0);
  const std = returns.length > 1
    ? Math.sqrt(returns.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / returns.length)
    : Math.abs(mean) * 0.5 || 50;

  const barItems: BarItem[] = allCompanies.map(r => ({
    shortLabel: r.ticker,
    fullLabel: `${r.ticker} — ${r.company_name}`,
    value: r.total_return_pct || 0,
    status: r.outlier_status,
    strength: r.outlier_strength,
  }));

  const high = data.company_outliers.high_performers;
  const low = data.company_outliers.low_performers;
  const normal = allCompanies.filter(r => r.outlier_strength === 'NORMAL');
  const fmtPct = (v?: number | null) => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(1)}%` : '—';

  return (
    <div>
      <h3 className="text-lg font-bold text-slate-900 mb-1">Total Return by Company</h3>
      <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem' }}>
        Sorted highest to lowest. Green = strong performer, red = weak performer, gray = normal range.
      </p>

      <VerticalBarChart
        items={barItems} mean={mean} upper={mean + 2 * std} lower={mean - 2 * std}
        yLabel="Total Return (%)" yFormatter={(v) => `${v.toFixed(0)}%`}
      />
      <BarLegend items={[
        { color: '#059669', label: 'Strong Company (Z > 2)' },
        { color: '#94a3b8', label: 'Normal Range', opacity: 0.45 },
        { color: '#dc2626', label: 'Weak Company (Z < -2)' },
      ]} />

      <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem', background: '#f8fafc', borderRadius: 10, padding: '1rem', textAlign: 'center' }}>
        <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Sector Mean Total Return</p>
        <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>{fmtPct(mean)}</p>
      </div>

      {high.length === 0 && low.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', background: '#f8fafc', borderRadius: 10 }}>
          <p style={{ fontSize: '1rem', fontWeight: 600 }}>No company outliers in this sector</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <h4 style={{ fontWeight: 700, color: '#065f46', marginBottom: 10, fontSize: '0.9rem' }}>⭐ Strong Companies</h4>
            {high.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : high.map(r => (
                <div key={r.ticker} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.company_name} identifier={r.ticker}
                    primaryLabel="Total Return" primaryValue={fmtPct(r.total_return_pct)}
                    primaryColor="#059669"
                    metrics={[
                      { label: 'Sharpe', value: r.sharpe_ratio?.toFixed(2) ?? '—' },
                      { label: 'Volatility', value: `${r.volatility_pct?.toFixed(1)}%` },
                      { label: 'Max Drawdown', value: `${r.max_drawdown_pct?.toFixed(1)}%` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.company_name} delivered ${fmtPct(r.total_return_pct)} total return — exceptional long-term value creation.`}
                    isHigh={true}
                  />
                </div>
              ))}
          </div>
          <div>
            <h4 style={{ fontWeight: 700, color: '#991b1b', marginBottom: 10, fontSize: '0.9rem' }}>⚠️ Weak Companies</h4>
            {low.length === 0
              ? <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>None in this sector</p>
              : low.map(r => (
                <div key={r.ticker} style={{ marginBottom: 12 }}>
                  <SpotlightCard
                    name={r.company_name} identifier={r.ticker}
                    primaryLabel="Total Return" primaryValue={fmtPct(r.total_return_pct)}
                    primaryColor="#dc2626"
                    metrics={[
                      { label: 'Sharpe', value: r.sharpe_ratio?.toFixed(2) ?? '—' },
                      { label: 'Volatility', value: `${r.volatility_pct?.toFixed(1)}%` },
                      { label: 'Max Drawdown', value: `${r.max_drawdown_pct?.toFixed(1)}%` },
                    ]}
                    outlierStatus={r.outlier_status} outlierStrength={r.outlier_strength}
                    insight={`${r.company_name} underperformed most sector peers with ${fmtPct(r.total_return_pct)} total return.`}
                    isHigh={false}
                  />
                </div>
              ))}
          </div>
        </div>
      )}

      <NormalList items={normal.map(r => ({
        name: r.company_name, ticker: r.ticker, date: '',
        primary: fmtPct(r.total_return_pct), primaryColor: (r.total_return_pct || 0) >= 0 ? '#059669' : '#dc2626',
        secondary: `Z: ${(r.composite_company_z || 0).toFixed(2)}  ·  Sharpe: ${r.sharpe_ratio?.toFixed(2) ?? '—'}`,
      }))} />
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

export function OutlierAnalysis({ companies, onBack, index }: OutlierAnalysisProps) {
  const [phase, setPhase] = useState<'select' | 'results'>('select');
  const [outlierData, setOutlierData] = useState<SectorOutlierData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('performance');
  const [periodYears, setPeriodYears] = useState<number | null>(null);

  const sectors = useMemo(() => {
    const s = new Set<string>();
    companies.forEach(c => { if (c.sector && c.sector !== 'Unknown') s.add(c.sector); });
    return [...s].sort();
  }, [companies]);

  const handleSectorSelect = async (sector: string) => {
    setLoading(true);
    const data = await loadSectorOutliers(sector, index, periodYears || undefined);
    if (data) { setOutlierData(data); setPhase('results'); }
    setLoading(false);
  };

  const handleBack = () => {
    setPhase('select'); setOutlierData(null); setActiveTab('performance');
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="min-h-screen bg-slate-50">
      {phase === 'select' && (
        <div className="max-w-6xl mx-auto px-6 py-12">
          <button onClick={onBack} className="inline-flex items-center text-slate-600 hover:text-slate-900 font-medium mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
          </button>
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Sector Outlier Analysis</h1>
          <p className="text-lg text-slate-600 mb-8">Select a sector to find statistical outliers in CEO performance, tenure, and company returns.</p>

          <div className="mb-12 bg-white rounded-lg p-6 border border-slate-200">
            <label className="block text-sm font-semibold text-slate-900 mb-3">Company Stock Analysis Period:</label>
            <div className="flex flex-wrap gap-3">
              {([['All Data (1996-2026)', null], ['Last 5 Years', 5], ['Last 10 Years', 10], ['Last 15 Years', 15]] as const).map(([label, val]) => (
                <button key={label} onClick={() => setPeriodYears(val as number | null)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${periodYears === val ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-900 hover:bg-slate-200'}`}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {sectors.map(sector => (
              <motion.button key={sector} onClick={() => handleSectorSelect(sector)}
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="bg-white rounded-lg p-6 border-2 border-slate-200 hover:border-slate-900 transition-colors"
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div style={{ marginBottom: 12 }}><SectorIcon sector={sector} /></div>
                <p className="font-semibold text-slate-900 text-sm">{sector}</p>
              </motion.button>
            ))}
          </div>
        </div>
      )}

      {phase === 'results' && outlierData && (
        <div className="max-w-6xl mx-auto px-6 py-8">
          <button onClick={handleBack} className="inline-flex items-center text-slate-600 hover:text-slate-900 font-medium mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Sectors
          </button>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 mb-2">
              <span className="inline-flex items-center gap-2">
                <SectorIcon sector={outlierData.sector} width={32} height={32} />
                {outlierData.sector} — Outlier Analysis
              </span>
            </h1>
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="font-medium text-slate-900">{outlierData.total_ceos_analyzed} CEO transitions</span>
              <span className="text-slate-600">•</span>
              <span className="font-medium text-slate-900">{outlierData.total_companies_analyzed} companies</span>
              <span className="text-slate-600">•</span>
              <span className="font-medium text-slate-900">{outlierData.outlier_count} outliers found</span>
              {periodYears && <><span className="text-slate-600">•</span><span className="text-slate-600 italic">Company data: last {periodYears} years</span></>}
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <Loader className="w-8 h-8 animate-spin text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600">Loading...</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-slate-200">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="w-full justify-start border-b rounded-none bg-slate-50 px-6">
                  <TabsTrigger value="performance">Performance Outliers</TabsTrigger>
                  <TabsTrigger value="tenure">Tenure Outliers</TabsTrigger>
                  <TabsTrigger value="company">Company Outliers</TabsTrigger>
                </TabsList>
                <div className="p-6">
                  <TabsContent value="performance"><PerformanceOutliersTab data={outlierData} /></TabsContent>
                  <TabsContent value="tenure"><TenureOutliersTab data={outlierData} /></TabsContent>
                  <TabsContent value="company"><CompanyOutliersTab data={outlierData} /></TabsContent>
                </div>
              </Tabs>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
