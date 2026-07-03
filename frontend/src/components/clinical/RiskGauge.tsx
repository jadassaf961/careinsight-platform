import React from 'react';

interface RiskGaugeProps {
  probability: number;   // 0–1
  threshold?: number;    // 0–1, default 0.5
  riskTier: 'high' | 'medium' | 'low';
  modelName?: string;
  modelVersion?: string;
}

const tierColor: Record<string, string> = {
  high:   '#B42318',
  medium: '#B54708',
  low:    '#067647',
};

export function RiskGauge({
  probability,
  threshold = 0.5,
  riskTier,
  modelName,
  modelVersion,
}: RiskGaugeProps) {
  const pct   = Math.round(probability * 100);
  const tier  = (riskTier ?? 'medium').toLowerCase();
  const color = tierColor[tier] ?? tierColor.medium;

  const radius = 80;
  const cx = 100;
  const cy = 100;

  const arc = (start: number, end: number) => {
    const x1 = cx + radius * Math.cos(start);
    const y1 = cy + radius * Math.sin(start);
    const x2 = cx + radius * Math.cos(end);
    const y2 = cy + radius * Math.sin(end);
    const largeArc = end - start > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  const startAngle = Math.PI;
  const endAngle   = Math.PI + Math.PI * probability;
  const tickAngle  = Math.PI + Math.PI * threshold;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 130" className="w-full max-w-xs">
        {/* Track */}
        <path d={arc(Math.PI, 2 * Math.PI)} stroke="#e2e8f0" strokeWidth={18} fill="none" />
        {/* Fill */}
        {probability > 0 && (
          <path d={arc(startAngle, endAngle)} stroke={color} strokeWidth={18} fill="none" strokeLinecap="round" />
        )}
        {/* Threshold tick */}
        <line
          x1={cx + (radius - 10) * Math.cos(tickAngle)}
          y1={cy + (radius - 10) * Math.sin(tickAngle)}
          x2={cx + (radius + 10) * Math.cos(tickAngle)}
          y2={cy + (radius + 10) * Math.sin(tickAngle)}
          stroke="#475569"
          strokeWidth={2}
          strokeDasharray="3 2"
        />
        {/* Percentage */}
        <text x={cx} y={cy} textAnchor="middle" fontSize="34" fontWeight="700" fill="#0f172a" fontFamily="'IBM Plex Mono', monospace">
          {pct}%
        </text>
        {/* Tier label */}
        <text x={cx} y={cy + 22} textAnchor="middle" fontSize="11" fill={color} fontWeight="600" letterSpacing="1">
          {tier.toUpperCase()} RISK
        </text>
      </svg>
      <div className="text-xs text-ink/50 text-center -mt-1">
        Threshold {Math.round(threshold * 100)}% · 30-day readmission probability
        {modelName && (
          <span className="block mt-0.5 font-mono text-[10px]">
            {modelName}{modelVersion ? ` v${modelVersion}` : ''}
          </span>
        )}
      </div>
    </div>
  );
}
