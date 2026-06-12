import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function CaseManagerDashboard() {
  const metrics = useQuery({
    queryKey: ["case-manager-metrics"],
    queryFn: () => api.get<{ high_risk_count: number }>("/dashboard/metrics"),
  });
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Case manager dashboard</h1>
      <div className="card mb-4">
        <div className="text-xs uppercase tracking-wide text-slate-500">
          High-risk follow-ups
        </div>
        <div className="text-3xl font-bold text-risk-high mt-1">
          {metrics.data?.high_risk_count ?? "—"}
        </div>
      </div>
      <Placeholder title="Follow-up tracking" />
      <Placeholder title="Intervention completion rate" />
      <Placeholder title="High-risk patient monitoring" />
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="card mb-4">
      <h2 className="font-semibold mb-2">{title}</h2>
      <p className="text-sm text-slate-400 italic">Stub — full implementation pending.</p>
    </div>
  );
}
