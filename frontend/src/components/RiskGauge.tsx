interface Props {
  probability: number; // 0-1
  threshold: number;
  riskTier: string;
}

export function RiskGauge({ probability, threshold, riskTier }: Props) {
  const pct = Math.round(probability * 100);
  const isHigh = riskTier.toLowerCase() === "high";
  const color = isHigh ? "#dc2626" : "#16a34a";

  // simple SVG arc gauge — 180 degree
  const radius = 80;
  const cx = 100;
  const cy = 100;
  const startAngle = Math.PI;
  const endAngle = Math.PI + Math.PI * probability;

  const arc = (start: number, end: number) => {
    const x1 = cx + radius * Math.cos(start);
    const y1 = cy + radius * Math.sin(start);
    const x2 = cx + radius * Math.cos(end);
    const y2 = cy + radius * Math.sin(end);
    const largeArc = end - start > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 130" className="w-full max-w-xs">
        <path d={arc(Math.PI, 2 * Math.PI)} stroke="#e2e8f0" strokeWidth={18} fill="none" />
        <path d={arc(startAngle, endAngle)} stroke={color} strokeWidth={18} fill="none"
              strokeLinecap="round" />
        <line
          x1={cx + (radius - 10) * Math.cos(Math.PI + Math.PI * threshold)}
          y1={cy + (radius - 10) * Math.sin(Math.PI + Math.PI * threshold)}
          x2={cx + (radius + 10) * Math.cos(Math.PI + Math.PI * threshold)}
          y2={cy + (radius + 10) * Math.sin(Math.PI + Math.PI * threshold)}
          stroke="#475569" strokeWidth={2}
        />
        <text x={cx} y={cy} textAnchor="middle" fontSize="34" fontWeight="700" fill="#0f172a">
          {pct}%
        </text>
        <text x={cx} y={cy + 22} textAnchor="middle" fontSize="13"
              fill={color} fontWeight="600">
          {riskTier.toUpperCase()} RISK
        </text>
      </svg>
      <div className="text-xs text-slate-500 mt-2">
        Threshold: {Math.round(threshold * 100)}% · 30-day readmission probability
      </div>
    </div>
  );
}
