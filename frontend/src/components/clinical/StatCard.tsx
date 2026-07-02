import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  tone?: 'default' | 'risk' | 'success' | 'brand';
}

const toneColors: Record<string, string> = {
  default: '#1e3a5f',   // navy-700
  risk:    '#dc2626',   // risk-high
  success: '#16a34a',   // risk-low
  brand:   '#0369a1',   // brand-600
};

export function StatCard({ label, value, delta, deltaLabel, tone = 'default' }: StatCardProps) {
  const valueColor = toneColors[tone] ?? toneColors.default;
  const deltaColor = delta === undefined ? undefined
    : delta > 0 ? '#dc2626' : '#16a34a';

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-500 mb-2">
        {label}
      </div>
      <div
        className="font-sans text-4xl font-bold leading-tight"
        style={{ color: valueColor }}
      >
        {value ?? '—'}
      </div>
      {delta !== undefined && (
        <div
          className="font-sans text-xs mt-1"
          style={{ color: deltaColor }}
        >
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}{deltaLabel ? ` ${deltaLabel}` : ''}
        </div>
      )}
    </div>
  );
}
