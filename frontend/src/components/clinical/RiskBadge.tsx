interface RiskBadgeProps {
  tier: 'high' | 'medium' | 'low';
  size?: 'sm' | 'md' | 'lg';
}

const tierConfig = {
  high:   { label: 'high',   color: '#B42318' },
  medium: { label: 'medium', color: '#B54708' },
  low:    { label: 'low',    color: '#067647' },
};

const sizeConfig = {
  sm: { fontSize: '0.7rem',    dot: 5 },
  md: { fontSize: '0.8rem',    dot: 6 },
  lg: { fontSize: '0.9375rem', dot: 7 },
};

export function RiskBadge({ tier, size = 'md' }: RiskBadgeProps) {
  const t = tier.toLowerCase() as keyof typeof tierConfig;
  const v = tierConfig[t] ?? tierConfig.medium;
  const s = sizeConfig[size] ?? sizeConfig.md;

  return (
    <span
      className="inline-flex items-center gap-1.5 font-display font-semibold lowercase whitespace-nowrap"
      style={{ color: v.color, fontSize: s.fontSize }}
    >
      <span
        style={{
          width: s.dot, height: s.dot, borderRadius: '50%',
          background: v.color, flexShrink: 0, display: 'inline-block',
        }}
      />
      {v.label}
    </span>
  );
}
