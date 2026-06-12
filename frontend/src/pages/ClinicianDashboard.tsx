import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface DashboardMetrics {
  total_patients: number;
  active_admissions: number;
  high_risk_count: number;
  predictions_last_24h: number;
}

export function ClinicianDashboard() {
  const { data } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => api.get<DashboardMetrics>("/dashboard/metrics"),
  });
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Clinician dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Stat label="Total patients" value={data?.total_patients} />
        <Stat label="Active admissions" value={data?.active_admissions} />
        <Stat label="High-risk patients" value={data?.high_risk_count} tone="risk" />
        <Stat label="Predictions / 24h" value={data?.predictions_last_24h} />
      </div>
      <Placeholder title="Patient queue" />
      <Placeholder title="High-risk watchlist" />
      <Placeholder title="Discharge readiness" />
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value?: number; tone?: "risk" }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-3xl font-bold mt-1 ${tone === "risk" ? "text-risk-high" : ""}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="card mb-4">
      <h2 className="font-semibold mb-2">{title}</h2>
      <p className="text-sm text-slate-400 italic">
        Stub — full implementation pending. See <code>docs/gaps.md</code>.
      </p>
    </div>
  );
}
