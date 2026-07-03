import React from 'react';

interface ShapBarProps {
  label: string;
  shapValue: number;    // positive = risk-increasing, negative = protective
  rank: number;
  maxAbsValue?: number; // for bar width normalization
}

export function ShapBar({ label, shapValue = 0, rank, maxAbsValue = 0.3 }: ShapBarProps) {
  const isRisk = shapValue > 0;
  const barColor  = isRisk ? '#B42318' : '#067647';
  const chipColor = isRisk ? '#B42318' : '#067647';
  const chipBg    = isRisk ? '#FEF3F2' : '#ECFDF3';
  const pct = Math.min(Math.abs(shapValue) / maxAbsValue, 1) * 100;
  const sign = isRisk ? '+' : '';

  return (
    <div className="grid items-center gap-3" style={{ gridTemplateColumns: '1.25rem 1fr auto' }}>
      <span className="font-mono text-xs text-ink/40 text-right">{rank}</span>

      <div className="flex flex-col gap-0.5">
        <span className="font-sans text-sm text-ink/80 leading-snug">{label}</span>
        <div className="h-1.5 rounded-full bg-tint overflow-hidden">
          <div
            className="h-full rounded-full transition-[width] duration-500"
            style={{ width: `${pct}%`, background: barColor }}
          />
        </div>
      </div>

      <span
        className="font-mono text-xs font-medium whitespace-nowrap rounded"
        style={{ color: chipColor, background: chipBg, padding: '0.1rem 0.4rem' }}
      >
        {sign}{shapValue.toFixed(3)}
      </span>
    </div>
  );
}
