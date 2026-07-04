import { CountUp } from '@/lib/appMotion';

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  tone?: 'default' | 'risk' | 'success' | 'brand';
  countUp?: boolean;
}

const toneColors: Record<string, string> = {
  default: '#0f0f0f',
  risk:    '#B42318',
  success: '#067647',
  brand:   '#0f0f0f',
};

export function StatCard({ label, value, delta, deltaLabel, tone = 'default', countUp = false }: StatCardProps) {
  const valueColor = toneColors[tone] ?? toneColors.default;
  const deltaColor = delta === undefined ? undefined : delta > 0 ? '#B42318' : '#067647';
  const numeric = typeof value === 'number';

  return (
    <div className="py-1">
      <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
        {label}
      </div>
      <div
        className="font-display text-5xl font-bold leading-none tracking-[-0.03em]"
        style={{ color: valueColor }}
      >
        {countUp && numeric ? <CountUp value={value as number} /> : value ?? '—'}
      </div>
      {delta !== undefined && (
        <div className="font-sans text-xs mt-2" style={{ color: deltaColor }}>
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}{deltaLabel ? ` ${deltaLabel}` : ''}
        </div>
      )}
    </div>
  );
}
