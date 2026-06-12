import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface ReadmissionStats {
  period: string;
  total_predictions: number;
  high_risk_rate: number;
  note: string;
}

export function AdminDashboard() {
  const stats = useQuery({
    queryKey: ["readmissions"],
    queryFn: () => api.get<ReadmissionStats>("/dashboard/readmissions"),
  });
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Administrator dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Total predictions
          </div>
          <div className="text-3xl font-bold mt-1">
            {stats.data?.total_predictions ?? "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            High-risk rate
          </div>
          <div className="text-3xl font-bold mt-1 text-risk-high">
            {stats.data ? `${(stats.data.high_risk_rate * 100).toFixed(1)}%` : "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">Period</div>
          <div className="text-3xl font-bold mt-1">{stats.data?.period ?? "—"}</div>
        </div>
      </div>
      <Placeholder title="Readmission outcomes (post-discharge)" />
      <Placeholder title="ROI / cost-of-care estimates" />
      <Placeholder title="Model performance over time" />
      <Placeholder title="Department-level breakdown" />
      {stats.data?.note && (
        <p className="text-xs text-slate-500 italic mt-4">{stats.data.note}</p>
      )}
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
