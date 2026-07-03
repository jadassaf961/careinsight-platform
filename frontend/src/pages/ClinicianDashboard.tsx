import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";
import { MyTasksWidget } from "@/components/clinical/MyTasksWidget";

interface DashboardMetrics {
  total_patients: number;
  active_admissions: number;
  high_risk_count: number;
  predictions_last_24h: number;
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
        <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">
          Clinician <em className="font-serifit font-normal italic">overview.</em>
        </h1>
        <p className="text-sm text-ink/50 mt-2">Ward overview for today's admitted patients.</p>
      </div>

      {/* Discharge tasks assigned to this clinician's role */}
      <MyTasksWidget />

      {/* Stat row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 lg:divide-x lg:divide-hairline border-y border-hairline py-6 [&>*]:lg:px-8 [&>*:first-child]:lg:pl-0">
        <StatCard
          label="Total patients"
          value={metrics.data?.total_patients ?? "—"}
          countUp
        />
        <StatCard
          label="Active admissions"
          value={metrics.data?.active_admissions ?? "—"}
          countUp
        />
        <StatCard
          label="High-risk patients"
          value={metrics.data?.high_risk_count ?? "—"}
          tone="risk"
          countUp
        />
        <StatCard
          label="Predictions / 24h"
          value={metrics.data?.predictions_last_24h ?? "—"}
          countUp
        />
      </div>

      {/* High-risk watchlist */}
      <Card>
        <SectionLabel>High-Risk Watchlist</SectionLabel>
        {highRiskPatients.length === 0 ? (
          <p className="text-sm text-ink/50">
            {highRisk.isLoading ? "Loading…" : "No high-risk patients currently admitted."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-hairline">
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-ink/40">Patient</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-ink/40">MRN</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-ink/40">Dept</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-ink/40">Risk</th>
                  <th className="text-left pb-2 font-sans font-medium text-xs uppercase tracking-wide text-ink/40">Top Factor</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline/60">
                {highRiskPatients.slice(0, 8).map((p) => (
                  <tr
                    key={p.patient_id}
                    className="hover:bg-tint cursor-pointer transition-colors duration-100"
                    onClick={() => navigate(`/patients/${p.patient_id}`)}
                  >
                    <td className="py-2.5 pr-4 font-medium text-ink">
                      {p.last_name}, {p.first_name}
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-xs text-ink/50">{p.mrn}</td>
                    <td className="py-2.5 pr-4 text-ink/60">{p.department}</td>
                    <td className="py-2.5 pr-4">
                      <span className="font-mono font-semibold text-risk-high">
                        {(p.probability * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-ink/50 text-xs max-w-[180px] truncate">
                      {p.top_factor ?? "—"}
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="text-ink/40 text-xs hover:text-ink transition-colors">Chart →</span>
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
            <p className="text-sm text-ink/50">
              {population.isLoading ? "Loading…" : "No admitted patients with predictions."}
            </p>
          ) : (
            <div className="space-y-2">
              {allPatients.slice(0, 6).map((p) => (
                <div
                  key={p.patient_id}
                  className="flex items-center justify-between py-2 border-b border-hairline/60 last:border-0 cursor-pointer hover:bg-tint -mx-2 px-2 rounded transition-colors"
                  onClick={() => navigate(`/patients/${p.patient_id}`)}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-ink truncate">
                      {p.last_name}, {p.first_name}
                    </div>
                    <div className="text-xs text-ink/40 font-mono">{p.mrn} · {p.department}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="font-mono text-sm font-semibold text-ink/80">
                      {(p.probability * 100).toFixed(0)}%
                    </span>
                    <RiskBadge tier={p.risk_tier.toLowerCase() as 'high' | 'medium' | 'low'} size="sm" />
                  </div>
                </div>
              ))}
              {allPatients.length > 6 && (
                <button
                  className="text-xs text-ink underline underline-offset-2 hover:text-ink/60 mt-1"
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
              <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-1">
                Predictions Run Today
              </div>
              <div className="font-display text-5xl font-bold leading-none tracking-[-0.03em] text-ink">
                {metrics.data?.predictions_last_24h ?? "—"}
              </div>
            </div>
            <div className="border-t border-hairline pt-4">
              <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
                Risk Summary
              </div>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-high" />
                  <span className="text-sm text-ink/60">
                    {population.data?.high_count ?? "—"} High
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-medium" />
                  <span className="text-sm text-ink/60">
                    {population.data?.medium_count ?? "—"} Medium
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-risk-low" />
                  <span className="text-sm text-ink/60">
                    {population.data?.low_count ?? "—"} Low
                  </span>
                </div>
              </div>
            </div>
            <p className="text-xs text-ink/40 italic border-t border-hairline pt-3">
              Decision-support only — not a substitute for clinical judgment.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
