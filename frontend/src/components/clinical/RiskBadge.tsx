import React from 'react';

interface RiskBadgeProps {
  tier: 'high' | 'medium' | 'low';
  size?: 'sm' | 'md' | 'lg';
}

const tierConfig = {
  high:   { label: '↑ HIGH RISK',   bg: '#fee2e2', color: '#dc2626', dot: '#dc2626', border: 'rgba(220,38,38,0.2)' },
  medium: { label: '~ MEDIUM RISK', bg: '#fef3c7', color: '#d97706', dot: '#d97706', border: 'rgba(217,119,6,0.2)' },
  low:    { label: '↓ LOW RISK',    bg: '#dcfce7', color: '#16a34a', dot: '#16a34a', border: 'rgba(22,163,74,0.2)' },
};

const sizeConfig = {
  sm: { fontSize: '0.65rem',  padding: '0.15rem 0.55rem', gap: '0.3rem', dot: 5 },
  md: { fontSize: '0.72rem',  padding: '0.3rem 0.75rem',  gap: '0.4rem', dot: 6 },
  lg: { fontSize: '0.8125rem', padding: '0.4rem 1rem',    gap: '0.5rem', dot: 7 },
};

export function RiskBadge({ tier, size = 'md' }: RiskBadgeProps) {
  const t = tier.toLowerCase() as keyof typeof tierConfig;
  const v = tierConfig[t] ?? tierConfig.medium;
  const s = sizeConfig[size] ?? sizeConfig.md;

  return (
    <span
      className="inline-flex items-center font-sans font-bold whitespace-nowrap rounded-full"
      style={{
        background: v.bg,
        color: v.color,
        border: `1px solid ${v.border}`,
        fontSize: s.fontSize,
        padding: s.padding,
        gap: s.gap,
        letterSpacing: '0.06em',
      }}
    >
      <span
        style={{
          width: s.dot,
          height: s.dot,
          borderRadius: '50%',
          background: v.dot,
          flexShrink: 0,
          display: 'inline-block',
        }}
      />
      {v.label}
    </span>
  );
}
