import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";
import { EscalationQueue } from "@/components/clinical/EscalationQueue";

interface DashboardMetrics {
  total_patients: number;
  active_admissions: number;
  high_risk_count: number;
  predictions_last_24h: number;
}

export function CaseManagerDashboard() {
  const navigate = useNavigate();

  const metrics = useQuery({
    queryKey: ["case-manager-metrics"],
    queryFn: () => api.get<DashboardMetrics>("/dashboard/metrics"),
  });

  const highRisk = useQuery({
    queryKey: ["population", "", "High"],
    queryFn: () => api.get<PopulationResponse>("/dashboard/population?risk_tier=High"),
  });

  const mediumRisk = useQuery({
    queryKey: ["population", "", "Medium"],
    queryFn: () => api.get<PopulationResponse>("/dashboard/population?risk_tier=Medium"),
  });

  const highRiskPatients = highRisk.data?.patients ?? [];
  const mediumRiskPatients = mediumRisk.data?.patients ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">
          Escalation <em className="font-serifit font-normal italic">queue.</em>
        </h1>
        <p className="text-sm text-ink/50 mt-2">Monitor high and medium-risk patients before discharge.</p>
      </div>

      {/* Post-discharge escalations — the primary worklist */}
      <EscalationQueue />

      {/* Stat row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 sm:divide-x sm:divide-hairline border-y border-hairline py-6 [&>*]:sm:px-8 [&>*:first-child]:sm:pl-0">
        <StatCard
          label="High-risk follow-ups"
          value={metrics.data?.high_risk_count ?? "—"}
          tone="risk"
          countUp
        />
        <StatCard
          label="Medium-risk monitoring"
          value={highRisk.data ? (mediumRisk.data?.patients.length ?? "—") : "—"}
          tone="default"
        />
        <StatCard
          label="Active admissions"
          value={metrics.data?.active_admissions ?? "—"}
          tone="brand"
        />
      </div>

      {/* High-risk monitoring */}
      <Card>
        <SectionLabel>High-Risk Patient Monitoring</SectionLabel>
        {highRiskPatients.length === 0 ? (
          <p className="text-sm text-ink/50">
            {highRisk.isLoading ? "Loading…" : "No high-risk patients currently admitted."}
          </p>
        ) : (
          <div className="space-y-2">
            {highRiskPatients.map((p) => (
              <div
                key={p.patient_id}
                className="flex items-center justify-between py-3 border-b border-hairline last:border-0 hover:bg-tint cursor-pointer transition-all duration-150 -mx-2 px-2 rounded"
                onClick={() => navigate(`/patients/${p.patient_id}`)}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-ink">
                      {p.last_name}, {p.first_name}
                    </span>
                    <span className="font-mono text-xs text-ink/40">{p.mrn}</span>
                  </div>
                  {p.top_factor && (
                    <div className="text-xs text-ink/50 mt-0.5 truncate">
                      Top factor: {p.top_factor}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className="font-mono text-sm font-bold text-risk-high">
                    {(p.probability * 100).toFixed(1)}%
                  </span>
                  <RiskBadge tier="high" size="sm" />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Follow-up tracking + Intervention rate */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <SectionLabel>Follow-Up Tracking</SectionLabel>
          {mediumRiskPatients.length === 0 ? (
            <p className="text-sm text-ink/50">
              {mediumRisk.isLoading ? "Loading…" : "No medium-risk patients currently admitted."}
            </p>
          ) : (
            <div className="space-y-2">
              {mediumRiskPatients.slice(0, 5).map((p) => (
                <div
                  key={p.patient_id}
                  className="flex items-center justify-between py-2 border-b border-hairline/60 last:border-0 cursor-pointer hover:bg-tint -mx-2 px-2 rounded transition-colors"
                  onClick={() => navigate(`/patients/${p.patient_id}`)}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-ink truncate">
                      {p.last_name}, {p.first_name}
                    </div>
                    <div className="text-xs text-ink/40">{p.department}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="font-mono text-sm font-semibold text-risk-medium">
                      {(p.probability * 100).toFixed(1)}%
                    </span>
                    <RiskBadge tier="medium" size="sm" />
                  </div>
                </div>
              ))}
              {mediumRiskPatients.length > 5 && (
                <button
                  className="text-xs text-ink underline underline-offset-2 hover:text-ink/60 mt-1"
                  onClick={() => navigate("/ward")}
                >
                  View all {mediumRiskPatients.length} medium-risk patients →
                </button>
              )}
            </div>
          )}
        </Card>

        <Card>
          <SectionLabel>Intervention Completion Rate</SectionLabel>
          <div className="space-y-4">
            <div className="flex items-end gap-3">
              <div>
                <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-1">
                  Predictions This Period
                </div>
                <div className="font-display text-5xl font-bold leading-none tracking-[-0.03em] text-ink">
                  {metrics.data?.predictions_last_24h ?? "—"}
                </div>
                <div className="text-xs text-ink/40 mt-1">in the last 24 hours</div>
              </div>
            </div>
            <div className="border-t border-hairline pt-4">
              <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-3">
                Risk Distribution
              </div>
              {highRisk.data && mediumRisk.data && (
                <div className="space-y-2">
                  {[
                    { label: 'High', count: highRisk.data.patients.length, color: '#B42318', bg: '#FEF3F2' },
                    { label: 'Medium', count: mediumRisk.data.patients.length, color: '#B54708', bg: '#FFFAEB' },
                    { label: 'Low', count: (highRisk.data.patients.length + mediumRisk.data.patients.length > 0)
                        ? Math.max(0, (metrics.data?.active_admissions ?? 0) - highRisk.data.patients.length - mediumRisk.data.patients.length)
                        : 0, color: '#067647', bg: '#ECFDF3' },
                  ].map(({ label, count, color, bg }) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-xs text-ink/50 w-14">{label}</span>
                      <div className="flex-1 h-2 bg-tint rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${metrics.data?.active_admissions
                              ? Math.min((count / metrics.data.active_admissions) * 100, 100)
                              : 0}%`,
                            background: color,
                          }}
                        />
                      </div>
                      <span className="text-xs font-mono text-ink/60 w-6 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              )}
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
