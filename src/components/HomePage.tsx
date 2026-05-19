import { TrendingUp, ArrowRight, ArrowLeft } from 'lucide-react';
import { motion } from 'motion/react';
import type { IndexConfig } from '../utils/types';
import type { ActionView } from '../App';

interface HomePageProps {
  indices: IndexConfig[];
  onSelect: (index: IndexConfig) => void;
  onBack: () => void;
  actionName: ActionView;
}

const ACTION_DISPLAY_NAMES: Record<ActionView, string> = {
  archive: 'Company Archive',
  selector: 'CEO Transition Analysis',
  'outlier-analysis': 'Outlier Analysis',
  rankings: 'Global Rankings',
};

const INDEX_STATS: Record<string, string> = {
  russell2000: '2,000 Small-Cap US Companies',
  sp500: '500 Large-Cap US Companies',
};

const INDEX_DESCRIPTIONS: Record<string, string> = {
  russell2000: 'Tracks the performance of 2,000 small-cap companies in the United States.',
  sp500: 'Measures the performance of 500 leading large-cap U.S. companies.',
};

export function HomePage({ indices, onSelect, onBack, actionName }: HomePageProps) {
  const displayName = ACTION_DISPLAY_NAMES[actionName];

  return (
    <div className="min-h-screen text-slate-900 font-sans" style={{ backgroundImage: "linear-gradient(rgba(248,250,252,0.6), rgba(248,250,252,0.6)), url('/bg.jpg')", backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
      {/* Top nav */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors font-medium text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Actions
          </button>
          <div className="h-4 w-px bg-slate-300" />
          <span className="text-sm font-semibold text-slate-900">{displayName}</span>
        </div>
      </div>

      {/* Index Selection with Video */}
      <div className="flex flex-col items-center px-6 py-12">
        <div className="text-center mb-10 w-full max-w-5xl">
          <div className="inline-flex items-center gap-2 bg-slate-200 text-slate-700 px-4 py-2 rounded-full mb-5 border border-slate-300">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-semibold uppercase tracking-wide">{displayName}</span>
          </div>
          <h1 className="text-5xl font-extrabold mb-3 text-slate-900 tracking-tight">
            Select an Index
          </h1>
          <p className="text-lg text-slate-500 font-light">
            Choose an index to explore {displayName.toLowerCase()}
          </p>
        </div>

        {/* Two-column: index cards left, video right */}
        <div className="flex flex-row items-stretch justify-center" style={{ gap: '5rem' }}>
          {/* Left: index cards */}
          <div className="w-80 flex flex-col gap-4">
            {indices.map((idx) => (
              <motion.button
                key={idx.key}
                onClick={() => onSelect(idx)}
                type="button"
                whileHover={{ y: -6, scale: 1.03, boxShadow: '0 20px 40px rgba(0,0,0,0.12)' }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="bg-white rounded-xl p-6 shadow-sm border-2 border-slate-900 flex flex-col flex-1 items-center text-center"
              >
                <div className="flex flex-col items-center gap-2 mb-3">
                  <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center text-white flex-shrink-0">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 leading-tight">{idx.name}</h2>
                    <p className="text-xs text-slate-500 font-medium">{INDEX_STATS[idx.key] ?? ''}</p>
                  </div>
                </div>
                <p className="text-sm text-slate-600 mb-5 leading-relaxed flex-1">
                  {INDEX_DESCRIPTIONS[idx.key] ?? idx.description}
                </p>
                <span className="inline-flex items-center gap-2 bg-slate-900 text-white px-6 py-3 rounded-lg font-semibold text-sm w-full justify-center">
                  Explore
                  <ArrowRight className="w-4 h-4" />
                </span>
              </motion.button>
            ))}
          </div>

          {/* Right: Video */}
          <div className="w-80 flex-shrink-0 flex items-center">
            <video
              src="/hero.mp4"
              autoPlay
              muted
              loop
              playsInline
              className="w-full rounded-xl shadow-xl object-cover"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
