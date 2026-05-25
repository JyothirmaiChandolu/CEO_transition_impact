import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { User, BookOpen, Award, Briefcase, Target, ExternalLink, Loader } from 'lucide-react';

interface CEOProfileProps {
  ceoName: string;
  companyName: string;
  companyTicker: string;
  transitionDate: string;
  sector: string;
  impact90Days?: number | null;
  prefetchedData?: ProfileData | null;
}

interface ProfileData {
  name: string;
  bio: string | null;
  image_url: string | null;
  url: string | null;
  background: string;
  focus: string;
  narrative: string | null;
  mandates: string[];
}

export function CEOProfile({ ceoName, companyName, transitionDate, sector, impact90Days, prefetchedData }: CEOProfileProps) {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    setImgError(false);

    // Use prefetched data if already available — no network call needed
    if (prefetchedData) {
      setProfile(prefetchedData);
      setLoading(false);
      return;
    }

    // Fallback: fetch ourselves (e.g. direct navigation without prefetch)
    setLoading(true);
    setProfile(null);
    const params = new URLSearchParams({ name: ceoName, company: companyName });
    if (impact90Days != null)  params.set('impact_90d', String(impact90Days));
    if (transitionDate)        params.set('transition_date', transitionDate);
    if (sector)                params.set('sector', sector);

    fetch(`/api/ceo/profile?${params}`)
      .then(r => r.json())
      .then(setProfile)
      .catch(() => setProfile({
        name: ceoName, bio: null, image_url: null, url: null,
        background: 'Executive Leader', focus: 'Strategic Growth',
        narrative: null, mandates: [],
      }))
      .finally(() => setLoading(false));
  }, [ceoName, companyName, impact90Days, prefetchedData]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6rem 0', gap: '0.75rem', color: '#94a3b8' }}>
        <Loader style={{ width: 22, height: 22, animation: 'spin 1s linear infinite' }} />
        <span style={{ fontSize: '0.875rem' }}>Building CEO profile…</span>
      </div>
    );
  }

  const hasPhoto = !!profile?.image_url && !imgError;
  const narrativeParagraphs = (profile?.narrative || '').split('\n').filter(p => p.trim());

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ display: 'flex', gap: '1.5rem', alignItems: 'stretch' }}
    >
      {/* ── Left column: photo card ── */}
      <div style={{
        width: 300, flexShrink: 0,
        background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0',
        boxShadow: '0 1px 3px rgba(0,0,0,0.07)', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Photo — fixed height so it never stretches awkwardly */}
        <div style={{ position: 'relative', height: 420, flexShrink: 0 }}>
          {hasPhoto ? (
            <img
              src={profile!.image_url!}
              alt={ceoName}
              onError={() => setImgError(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center 15%' }}
            />
          ) : (
            <div style={{
              width: '100%', height: '100%',
              background: 'linear-gradient(135deg, #334155 0%, #0f172a 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <User style={{ width: 72, height: 72, color: '#64748b' }} />
            </div>
          )}
          {/* Gradient name overlay */}
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
            justifyContent: 'flex-end',
            background: 'linear-gradient(to top, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.2) 45%, transparent 100%)',
            padding: '1rem 1.25rem',
          }}>
            <p style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', lineHeight: 1.3, margin: 0 }}>{ceoName}</p>
            <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.7)', letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 600, margin: '3px 0 0' }}>
              Incoming CEO
            </p>
          </div>
        </div>

        {/* Background & Focus — flex: 1 so it fills remaining card height and stays aligned */}
        <div style={{ padding: '1.25rem', borderTop: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
            <Briefcase style={{ width: 16, height: 16, color: '#94a3b8', marginTop: 2, flexShrink: 0 }} />
            <div>
              <p style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#3b82f6', margin: '0 0 2px' }}>Background</p>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>{profile?.background || 'Executive Leader'}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
            <Target style={{ width: 16, height: 16, color: '#94a3b8', marginTop: 2, flexShrink: 0 }} />
            <div>
              <p style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#3b82f6', margin: '0 0 2px' }}>Focus</p>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>{profile?.focus || 'Strategic Growth'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right column: narrative + mandates stacked ── */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.07)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <BookOpen style={{ width: 20, height: 20, color: '#3b82f6', flexShrink: 0 }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Executive Narrative</h3>
          </div>
          {narrativeParagraphs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {narrativeParagraphs.map((para, i) => (
                <p key={i} style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.7, margin: 0 }}>{para}</p>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>No narrative available for this CEO.</p>
          )}
          {profile?.url && (
            <a href={profile.url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8', textDecoration: 'none' }}>
              <ExternalLink style={{ width: 12, height: 12 }} />
              Wikipedia source
            </a>
          )}
        </div>

        {profile?.mandates && profile.mandates.length > 0 && (
          <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.07)', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <Award style={{ width: 20, height: 20, color: '#eab308', flexShrink: 0 }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Key Mandates & Objectives</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {profile.mandates.map((mandate, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '1rem',
                  padding: '0.875rem 0',
                  borderBottom: i < profile.mandates.length - 1 ? '1px solid #f1f5f9' : 'none',
                }}>
                  <span style={{
                    width: 28, height: 28, borderRadius: '50%', background: '#f1f5f9',
                    color: '#475569', fontSize: '0.75rem', fontWeight: 700,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    {i + 1}
                  </span>
                  <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.6, margin: 0 }}>{mandate}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
