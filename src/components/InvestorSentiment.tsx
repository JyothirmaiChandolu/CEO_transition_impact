import { ThumbsUp, ThumbsDown, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import { MetricTooltip } from './MetricTooltip';

interface InvestorSentimentProps {
  impact90Days: number | null;
  impact1Year: number | null;
  preTransitionTrend: number | null;
  companyName: string;
  previousCEO: string;
  newCEO: string;
}

export function InvestorSentiment({
  impact90Days,
  impact1Year,
  preTransitionTrend,
  companyName,
  previousCEO,
  newCEO
}: InvestorSentimentProps) {

  if (impact90Days === null) {
    return (
      <div className="text-center py-8 text-slate-500">
        Insufficient data to determine investor sentiment.
      </div>
    );
  }

  // Determine sentiment based on abnormal return
  const positiveReaction = impact90Days > 2; // More than 2% positive return = positive sentiment
  const negativeReaction = impact90Days < -2;
  const neutralReaction = !positiveReaction && !negativeReaction;

  // Calculate market expectation vs actual
  const preTransitionNegative = (preTransitionTrend ?? 0) < 0;

  let sentimentTitle = '';
  let sentimentDescription = '';
  let sentimentIcon = null;
  let sentimentColor = '';
  let sentimentBgColor = '';

  if (positiveReaction) {
    sentimentTitle = 'POSITIVE INVESTOR REACTION ✓';
    sentimentColor = 'text-emerald-700';
    sentimentBgColor = 'bg-emerald-50 border-emerald-200';
    sentimentIcon = <ThumbsUp className="w-8 h-8 text-emerald-600" />;

    if (preTransitionNegative) {
      sentimentDescription = previousCEO
        ? `The market reacted positively to the leadership transition from ${previousCEO} to ${newCEO}. Despite a negative pre-transition trend, the stock rebounded by ${impact90Days.toFixed(1)}% in 90 days, suggesting investor optimism about new management's direction.`
        : `The market reacted positively to ${newCEO}'s appointment. Despite a negative pre-appointment trend, the stock rebounded by ${impact90Days.toFixed(1)}% in 90 days, suggesting investor optimism about the new leadership's direction.`;
    } else {
      sentimentDescription = `Investors showed confidence in the new CEO ${newCEO}. The stock gained ${impact90Days.toFixed(1)}% in the first 90 days post-transition, indicating market approval of the leadership change at ${companyName}.`;
    }
  } else if (negativeReaction) {
    sentimentTitle = 'NEGATIVE INVESTOR REACTION ✗';
    sentimentColor = 'text-red-700';
    sentimentBgColor = 'bg-red-50 border-red-200';
    sentimentIcon = <ThumbsDown className="w-8 h-8 text-red-600" />;

    sentimentDescription = `The market reacted negatively to the CEO transition. The stock declined by ${Math.abs(impact90Days).toFixed(1)}% in 90 days, indicating investor concerns about new leadership or market uncertainty about the strategic direction under ${newCEO}.`;
  } else {
    sentimentTitle = 'NEUTRAL INVESTOR REACTION';
    sentimentColor = 'text-slate-700';
    sentimentBgColor = 'bg-slate-50 border-slate-200';
    sentimentIcon = <Activity className="w-8 h-8 text-slate-600" />;

    sentimentDescription = `The market showed minimal reaction to the CEO transition. The stock moved only ${impact90Days.toFixed(1)}% in 90 days, suggesting investors viewed this as an ordinary leadership change with neutral expectations for the new CEO ${newCEO}.`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-8 rounded-xl border-2 ${sentimentBgColor}`}
    >
      <div className="flex items-start gap-6">
        <div className="flex-shrink-0">
          {sentimentIcon}
        </div>

        <div className="flex-1">
          <h3 className={`text-lg font-bold mb-3 ${sentimentColor}`}>
            {sentimentTitle}
          </h3>

          <p className="text-slate-600 leading-relaxed mb-6">
            {sentimentDescription}
          </p>

          {/* Key metrics supporting sentiment */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white bg-opacity-60 p-4 rounded-lg">
              <div className="text-xs text-slate-500 mb-2 font-medium uppercase flex items-center">
                90-Day Impact
                <MetricTooltip text="Percentage change in stock price over the 90 days after the CEO took office. Used to gauge the market's immediate reaction to the leadership change." />
              </div>
              <div className={`flex items-center gap-2 font-bold text-lg ${
                impact90Days >= 0 ? 'text-emerald-700' : 'text-red-700'
              }`}>
                {impact90Days >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {impact90Days >= 0 ? '+' : ''}{impact90Days.toFixed(2)}%
              </div>
            </div>

            {impact1Year !== null && (
              <div className="bg-white bg-opacity-60 p-4 rounded-lg">
                <div className="text-xs text-slate-500 mb-2 font-medium uppercase flex items-center">
                  1-Year Impact
                  <MetricTooltip text="Percentage change in stock price over the full first year of the CEO's tenure — a broader view of sustained market confidence." />
                </div>
                <div className={`flex items-center gap-2 font-bold text-lg ${
                  impact1Year >= 0 ? 'text-emerald-700' : 'text-red-700'
                }`}>
                  {impact1Year >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                  {impact1Year >= 0 ? '+' : ''}{impact1Year.toFixed(2)}%
                </div>
              </div>
            )}

            {preTransitionTrend !== null && (
              <div className="bg-white bg-opacity-60 p-4 rounded-lg">
                <div className="text-xs text-slate-500 mb-2 font-medium uppercase flex items-center">
                  Pre-Transition Trend
                  <MetricTooltip text="Stock performance in the 90 days before the CEO changed. Helps determine whether the new CEO inherited momentum or headwinds." />
                </div>
                <div className={`flex items-center gap-2 font-bold text-lg ${
                  preTransitionTrend >= 0 ? 'text-emerald-700' : 'text-red-700'
                }`}>
                  {preTransitionTrend >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                  {preTransitionTrend >= 0 ? '+' : ''}{preTransitionTrend.toFixed(2)}%
                </div>
              </div>
            )}

            {impact1Year !== null && (
              <div className="bg-white bg-opacity-60 p-4 rounded-lg">
                <div className="text-xs text-slate-500 mb-2 font-medium uppercase flex items-center">
                  Momentum
                  <MetricTooltip text="Describes whether the stock's performance improved or declined between the 90-day and 1-year marks. 'Improving' means performance strengthened over time." />
                </div>
                <div className={`font-bold text-lg ${
                  impact1Year > impact90Days ? 'text-emerald-700' : impact1Year < impact90Days ? 'text-red-700' : 'text-slate-700'
                }`}>
                  {impact1Year > impact90Days ? 'Improving ↗' : impact1Year < impact90Days ? 'Declining ↘' : 'Stable →'}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-opacity-20 border-slate-300">
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-slate-900">Interpretation:</span> This sentiment is derived from analyzing the abnormal returns (abnormal return = actual return - expected return) in the period following the CEO transition, compared to pre-transition market performance.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
