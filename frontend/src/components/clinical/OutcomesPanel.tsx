import { useQuery } from "@tanstack/react-query";
import { api, OutcomeMetrics } from "@/lib/api";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <SectionLabel className="mb-1">{label}</SectionLabel>
      <div className="font-display text-5xl font-bold leading-none tracking-[-0.03em] text-ink">{value}</div>
      {sub && <div className="text-xs text-ink/40 mt-2">{sub}</div>}
    </div>
  );
}

export function OutcomesPanel() {
  const { data } = useQuery({
    queryKey: ["outcome-metrics"],
    queryFn: () => api.get<OutcomeMetrics>("/outcomes/metrics"),
  });

  const pct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(1)}%`);

  return (
    <Card>
      <SectionLabel className="mb-4">Care Transition Outcomes</SectionLabel>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Metric label="Discharges tracked" value={data ? String(data.discharges_tracked) : "—"} />
        <Metric label="30-day readmission rate" value={data ? pct(data.readmission_rate) : "—"}
          sub={data ? `${data.readmissions_30d} readmissions` : undefined} />
        <Metric label="Check-in response rate" value={data ? pct(data.checkin_response_rate) : "—"} />
        <Metric label="Escalations resolved" value={data ? String(data.escalations_resolved) : "—"}
          sub={data ? `${data.escalations_open} still open` : undefined} />
      </div>
      {data && data.monthly.length > 0 && (
        <div className="mt-5 border-t border-hairline pt-4">
          <SectionLabel className="mb-2">Monthly trend</SectionLabel>
          <div className="flex gap-3 flex-wrap">
            {data.monthly.map((m) => (
              <div key={m.month} className="text-xs text-ink/60 bg-tint rounded-md px-2.5 py-1.5">
                <span className="font-mono font-medium">{m.month}</span>
                {" · "}{m.discharges} discharged · {m.readmissions} readmitted
              </div>
            ))}
          </div>
        </div>
      )}
      <p className="text-xs text-ink/40 italic mt-4">
        These numbers also retrain the local model — every tracked discharge improves prediction accuracy on this hospital's population.
      </p>
    </Card>
  );
}
