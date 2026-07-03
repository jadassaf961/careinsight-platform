import { useQuery } from "@tanstack/react-query";
import { api, OutcomeMetrics } from "@/lib/api";
import { Card } from "@/components/core/Card";

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-1">
        {label}
      </div>
      <div className="font-sans text-3xl font-bold text-navy-700">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
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
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-4">
        Care Transition Outcomes
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Metric label="Discharges tracked" value={data ? String(data.discharges_tracked) : "—"} />
        <Metric label="30-day readmission rate" value={data ? pct(data.readmission_rate) : "—"}
          sub={data ? `${data.readmissions_30d} readmissions` : undefined} />
        <Metric label="Check-in response rate" value={data ? pct(data.checkin_response_rate) : "—"} />
        <Metric label="Escalations resolved" value={data ? String(data.escalations_resolved) : "—"}
          sub={data ? `${data.escalations_open} still open` : undefined} />
      </div>
      {data && data.monthly.length > 0 && (
        <div className="mt-5 border-t border-slate-100 pt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
            Monthly trend
          </div>
          <div className="flex gap-3 flex-wrap">
            {data.monthly.map((m) => (
              <div key={m.month} className="text-xs text-slate-600 bg-slate-50 rounded-md px-2.5 py-1.5">
                <span className="font-mono font-medium">{m.month}</span>
                {" · "}{m.discharges} discharged · {m.readmissions} readmitted
              </div>
            ))}
          </div>
        </div>
      )}
      <p className="text-xs text-slate-400 italic mt-4">
        These numbers also retrain the local model — every tracked discharge improves prediction accuracy on this hospital's population.
      </p>
    </Card>
  );
}
