import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";
import { Card } from "@/components/core/Card";
import { MyTasksWidget } from "@/components/clinical/MyTasksWidget";

interface DashboardMetrics {
  total_patients: number;
  active_admissions: number;
  high_risk_count: number;
  predictions_last_24h: number;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
      {children}
    </div>
  );
}

export function ClinicianDashboard() {
  const navigate = useNavigate();

  const metrics = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => api.get<DashboardMetrics>("/dashboard/metrics"),
  });

  const population = useQuery({
    queryKey: ["population", "", ""],
    queryFn: () => api.get<PopulationResponse>("/dashboard/population"),
  });

  const highRisk = useQuery({
    queryKey: ["population", "", "High"],
    queryFn: () => api.get<PopulationResponse>("/dashboard/population?risk_tier=High"),
  });

  const allPatients = population.data?.patients ?? [];
  const highRiskPatients = highRisk.data?.patients ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-navy-700">Clinician Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Ward overview for today's admitted patients.</p>
      </div>

      {/* Discharge tasks assigned to this clinician's role */}
      <MyTasksWidget />

      {/* Stat row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total patients"
          value={metrics.data?.total_patients ?? "—"}
        />
        <StatCard
          label="Active admissions"
          value={metrics.data?.active_admissions ?? "—"}
          tone="brand"
        />
        <StatCard
          label="High-risk patients"
          value={metrics.data?.high_risk_count ?? "—"}
          tone="risk"
        />
        <StatCard
          label="Predictions / 24h"
          value={metrics.data?.predictions_last_24h ?? "—"}
        />
      </div>

      {/* High-risk watchlist */}
      <Card>
        <SectionLabel>High-Risk Watchlist</SectionLabel>
        {highRiskPatients.length === 0 ? (
          <p className="text-sm text-slate-500">
            {highRisk.isLoading ? "Loading…" : "No high-risk patients currently admitted."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-slate-400">Patient</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-slate-400">MRN</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-slate-400">Dept</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-slate-400">Risk</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-slate-400">Top Factor</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {highRiskPatients.slice(0, 8).map((p) => (
                  <tr
                    key={p.patient_id}
                    className="hover:bg-slate-50 cursor-pointer transition-colors duration-100"
                    onClick={() => navigate(`/patients/${p.patient_id}`)}
                  >
                    <td className="py-2.5 pr-4 font-medium text-slate-800">
                      {p.last_name}, {p.first_name}
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{p.mrn}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{p.department}</td>
                    <td className="py-2.5 pr-4">
                      <span className="font-mono font-semibold text-risk-high">
                        {(p.probability * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-slate-500 text-xs max-w-[180px] truncate">
                      {p.top_factor ?? "—"}
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="text-brand-600 text-xs hover:underline">Chart →</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Patient queue + Discharge readiness side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <SectionLabel>Patient Queue</SectionLabel>
          {allPatients.length === 0 ? (
            <p className="text-sm text-slate-500">
              {population.isLoading ? "Loading…" : "No admitted patients with predictions."}
            </p>
          ) : (
            <div className="space-y-2">
              {allPatients.slice(0, 6).map((p) => (
                <div
                  key={p.patient_id}
                  className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0 cursor-pointer hover:bg-slate-50 -mx-2 px-2 rounded transition-colors"
                  onClick={() => navigate(`/patients/${p.patient_id}`)}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-slate-800 truncate">
                      {p.last_name}, {p.first_name}
                    </div>
                    <div className="text-xs text-slate-400 font-mono">{p.mrn} · {p.department}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="font-mono text-sm font-semibold text-slate-700">
                      {(p.probability * 100).toFixed(0)}%
                    </span>
                    <RiskBadge tier={p.risk_tier.toLowerCase() as 'high' | 'medium' | 'low'} size="sm" />
                  </div>
                </div>
              ))}
              {allPatients.length > 6 && (
                <button
                  className="text-xs text-brand-600 hover:underline mt-1"
                  onClick={() => navigate("/ward")}
                >
                  View all {allPatients.length} patients →
                </button>
              )}
            </div>
          )}
        </Card>

        <Card>
          <SectionLabel>Discharge Readiness</SectionLabel>
          <div className="space-y-4">
            <div>
              <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-1">
                Predictions Run Today
              </div>
              <div className="font-sans text-4xl font-bold text-navy-700">
                {metrics.data?.predictions_last_24h ?? "—"}
              </div>
            </div>
            <div className="border-t border-slate-100 pt-4">
              <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-2">
                Risk Summary
              </div>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-high" />
                  <span className="text-sm text-slate-600">
                    {population.data?.high_count ?? "—"} High
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-medium" />
                  <span className="text-sm text-slate-600">
                    {population.data?.medium_count ?? "—"} Medium
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-low" />
                  <span className="text-sm text-slate-600">
                    {population.data?.low_count ?? "—"} Low
                  </span>
                </div>
              </div>
            </div>
            <p className="text-xs text-slate-400 italic border-t border-slate-100 pt-3">
              Decision-support only — not a substitute for clinical judgment.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
