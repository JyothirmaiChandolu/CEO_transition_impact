import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { User, ExternalLink, Calendar, Building2, Clock, Briefcase } from 'lucide-react';

interface CEOProfilePanelProps {
  ceoName: string;
  companyName: string;
  ticker: string;
  transitionDate: string;
  endDate?: string;
  role: 'incoming' | 'outgoing';
  accent?: string;
}

interface WikiProfile {
  photo: string | null;
  extract: string | null;
  pageUrl: string | null;
  found: boolean;
}

function useCEOProfile(ceoName: string, companyName: string): { profile: WikiProfile | null; loading: boolean } {
  const [profile, setProfile] = useState<WikiProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ceoName || ceoName === 'Unknown' || ceoName.length < 3) {
      setProfile({ photo: null, extract: null, pageUrl: null, found: false });
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchProfile() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ name: ceoName, company: companyName });
        const res = await fetch(`/api/ceo/bio?${params}`);
        const data = await res.json();
        if (!cancelled) {
          setProfile({
            photo:   data.image_url ?? null,
            extract: data.bio ?? null,
            pageUrl: data.url ?? null,
            found:   data.found ?? false,
          });
        }
      } catch {
        if (!cancelled) setProfile({ photo: null, extract: null, pageUrl: null, found: false });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchProfile();
    return () => { cancelled = true; };
  }, [ceoName, companyName]);

  return { profile, loading };
}

function TenureDisplay({ transitionDate, endDate }: { transitionDate: string; endDate?: string }) {
  const start = new Date(transitionDate);
  const end = endDate && endDate !== 'Present' ? new Date(endDate) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const years = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365));
  const months = Math.floor((diffMs % (1000 * 60 * 60 * 24 * 365)) / (1000 * 60 * 60 * 24 * 30));
  if (years === 0) return <span>{months}mo</span>;
  return <span>{years}y {months}mo</span>;
}

export function CEOProfilePanel({ ceoName, companyName, ticker, transitionDate, endDate, role, accent = '#7c3aed' }: CEOProfilePanelProps) {
  const { profile, loading } = useCEOProfile(ceoName, companyName);
  const isIncoming = role === 'incoming';

  const displayDate = new Date(transitionDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  const displayEndDate = endDate && endDate !== 'Present'
    ? new Date(endDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : 'Present';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-2xl overflow-hidden"
      style={{ border: `1px solid ${accent}25`, background: 'white', boxShadow: `0 4px 24px ${accent}12` }}
    >
      {/* Header band */}
      <div
        className="px-5 py-3 flex items-center justify-between"
        style={{ background: `linear-gradient(135deg, ${accent}18 0%, ${accent}08 100%)`, borderBottom: `1px solid ${accent}15` }}
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: accent }} />
          <span className="text-xs font-bold uppercase tracking-wider" style={{ color: accent }}>
            {isIncoming ? 'Incoming CEO' : 'Outgoing CEO'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Briefcase className="w-3 h-3" />
          {ticker}
        </div>
      </div>

      {/* Main content */}
      <div className="p-5">
        {/* Name + photo row */}
        <div className="flex items-start gap-4 mb-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {loading ? (
              <div className="w-16 h-16 rounded-xl bg-slate-100 animate-pulse" />
            ) : profile?.photo ? (
              <motion.img
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                src={profile.photo}
                alt={ceoName}
                className="w-16 h-16 rounded-xl object-cover"
                style={{ border: `2px solid ${accent}30` }}
              />
            ) : (
              <div
                className="w-16 h-16 rounded-xl flex items-center justify-center"
                style={{ background: `linear-gradient(135deg, ${accent}20, ${accent}08)`, border: `2px solid ${accent}25` }}
              >
                <User className="w-6 h-6" style={{ color: accent }} />
              </div>
            )}
          </div>

          {/* Name & company */}
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-slate-900 text-lg leading-tight truncate">{ceoName}</h3>
            <p className="text-sm text-slate-500 mt-0.5 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{companyName}</span>
            </p>
            {profile?.pageUrl && (
              <a
                href={profile.pageUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-medium mt-1.5 hover:underline"
                style={{ color: accent }}
              >
                Wikipedia <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Tenure metrics */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center rounded-lg py-2.5 px-2" style={{ background: `${accent}08`, border: `1px solid ${accent}15` }}>
            <div className="text-xs text-slate-500 mb-0.5 flex items-center justify-center gap-1">
              <Calendar className="w-3 h-3" />
              {isIncoming ? 'Started' : 'Ended'}
            </div>
            <div className="text-sm font-semibold text-slate-800">{displayDate}</div>
          </div>
          <div className="text-center rounded-lg py-2.5 px-2" style={{ background: `${accent}08`, border: `1px solid ${accent}15` }}>
            <div className="text-xs text-slate-500 mb-0.5 flex items-center justify-center gap-1">
              <Calendar className="w-3 h-3" />
              {isIncoming ? 'Until' : 'Left'}
            </div>
            <div className="text-sm font-semibold text-slate-800">{displayEndDate}</div>
          </div>
          <div className="text-center rounded-lg py-2.5 px-2" style={{ background: `${accent}08`, border: `1px solid ${accent}15` }}>
            <div className="text-xs text-slate-500 mb-0.5 flex items-center justify-center gap-1">
              <Clock className="w-3 h-3" />
              Tenure
            </div>
            <div className="text-sm font-semibold" style={{ color: accent }}>
              <TenureDisplay transitionDate={transitionDate} endDate={endDate} />
            </div>
          </div>
        </div>

        {/* Bio extract */}
        {loading ? (
          <div className="space-y-2">
            <div className="h-3 bg-slate-100 rounded animate-pulse w-full" />
            <div className="h-3 bg-slate-100 rounded animate-pulse w-5/6" />
            <div className="h-3 bg-slate-100 rounded animate-pulse w-4/6" />
          </div>
        ) : profile?.extract ? (
          <p className="text-xs text-slate-500 leading-relaxed line-clamp-4">{profile.extract}</p>
        ) : (
          <p className="text-xs text-slate-400 italic">No Wikipedia biography found</p>
        )}
      </div>
    </motion.div>
  );
}
