import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ModelStatsResponse } from "@/lib/api";
import { OutcomesPanel } from "@/components/clinical/OutcomesPanel";
import { StatCard } from "@/components/clinical/StatCard";

export function AdminDashboard() {
  const stats = useQuery({
    queryKey: ["readmissions"],
    queryFn: () =>
      api.get<{ period: string; total_predictions: number; high_risk_rate: number; note: string }>(
        "/dashboard/readmissions"
      ),
  });
  const modelStats = useQuery({
    queryKey: ["model-stats"],
    queryFn: () => api.get<ModelStatsResponse>("/dashboard/model-stats"),
  });

  return (
    <div>
      <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink mb-2">
        Hospital <em className="font-serifit font-normal italic">outcomes.</em>
      </h1>
      <p className="text-sm text-ink/50 mb-8">Model performance, care-transition results, and return on investment.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x md:divide-hairline border-y border-hairline py-6 mb-8 [&>*]:md:px-8 [&>*:first-child]:md:pl-0">
        <StatCard label="Total predictions" value={stats.data?.total_predictions ?? "—"} countUp />
        <StatCard
          label="High-risk rate"
          value={stats.data ? `${(stats.data.high_risk_rate * 100).toFixed(1)}%` : "—"}
          tone="risk"
        />
        <StatCard label="Period" value={stats.data?.period ?? "—"} />
      </div>

      <div className="mb-6">
        <OutcomesPanel />
      </div>
      <RoiCalculator />
      <ModelTransparency data={modelStats.data} isLoading={modelStats.isLoading} />

      {stats.data?.note && (
        <p className="text-xs text-ink/50 italic mt-4">{stats.data.note}</p>
      )}
    </div>
  );
}

function RoiCalculator() {
  const [beds, setBeds] = useState(300);
  const [monthlyAdmissions, setMonthlyAdmissions] = useState(250);
  const [readmissionRate, setReadmissionRate] = useState(13);
  const [costPerReadmission, setCostPerReadmission] = useState(5000);

  const PRICE_PER_BED_MONTH = 12; // USD — mid-point of $8–15/bed/month

  const annualReadmissions = Math.round((monthlyAdmissions * 12 * readmissionRate) / 100);
  const highRiskCount = Math.round(annualReadmissions * 0.3);
  const preventedLow = Math.round(highRiskCount * 0.15);
  const preventedHigh = Math.round(highRiskCount * 0.20);
  const savingsLow = preventedLow * costPerReadmission;
  const savingsHigh = preventedHigh * costPerReadmission;
  const annualPlatformCost = beds * PRICE_PER_BED_MONTH * 12;
  const netLow = savingsLow - annualPlatformCost;
  const netHigh = savingsHigh - annualPlatformCost;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">ROI Impact Calculator</h2>
      <p className="text-xs text-ink/40 mb-4">
        Projected savings based on published literature on clinical decision support tools
        (15–20% reduction in high-risk readmissions).
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <label className="block">
          <span className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Total beds</span>
          <input
            type="number"
            className="mt-1 w-full border-0 border-b border-hairline rounded-none px-0 py-1.5 text-sm bg-transparent focus:outline-none focus:border-ink"
            value={beds}
            onChange={(e) => setBeds(Number(e.target.value))}
            min={50}
            max={2000}
          />
        </label>
        <label className="block">
          <span className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Monthly admissions</span>
          <input
            type="number"
            className="mt-1 w-full border-0 border-b border-hairline rounded-none px-0 py-1.5 text-sm bg-transparent focus:outline-none focus:border-ink"
            value={monthlyAdmissions}
            onChange={(e) => setMonthlyAdmissions(Number(e.target.value))}
            min={10}
            max={5000}
          />
        </label>
        <label className="block">
          <span className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Readmission rate (%)</span>
          <input
            type="number"
            className="mt-1 w-full border-0 border-b border-hairline rounded-none px-0 py-1.5 text-sm bg-transparent focus:outline-none focus:border-ink"
            value={readmissionRate}
            onChange={(e) => setReadmissionRate(Number(e.target.value))}
            min={1}
            max={40}
          />
        </label>
        <label className="block">
          <span className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Cost per readmission ($)</span>
          <input
            type="number"
            className="mt-1 w-full border-0 border-b border-hairline rounded-none px-0 py-1.5 text-sm bg-transparent focus:outline-none focus:border-ink"
            value={costPerReadmission}
            onChange={(e) => setCostPerReadmission(Number(e.target.value))}
            min={500}
            max={50000}
          />
        </label>
      </div>

      <div className="bg-tint rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Annual readmissions</div>
          <div className="text-2xl font-bold mt-1">{annualReadmissions.toLocaleString()}</div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">
            High-risk patients flagged / year
          </div>
          <div className="text-2xl font-bold mt-1 text-risk-medium">
            ~{highRiskCount.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">
            Estimated annual savings
          </div>
          <div className="text-2xl font-bold mt-1 text-risk-low">
            ${savingsLow.toLocaleString()} – ${savingsHigh.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="mt-4 border-t border-hairline pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Platform cost</div>
          <div className="text-lg font-bold mt-1">
            ${annualPlatformCost.toLocaleString()}<span className="text-sm font-normal text-ink/50">/yr</span>
          </div>
          <div className="text-xs text-ink/40 mt-0.5">
            ${PRICE_PER_BED_MONTH}/bed/month × {beds} beds
          </div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Net ROI</div>
          <div className={`text-lg font-bold mt-1 ${netLow >= 0 ? "text-risk-low" : "text-ink/80"}`}>
            ${netLow.toLocaleString()} – ${netHigh.toLocaleString()}
          </div>
          <div className="text-xs text-ink/40 mt-0.5">savings minus platform cost</div>
        </div>
      </div>
    </div>
  );
}

function ModelTransparency({
  data,
  isLoading,
}: {
  data: ModelStatsResponse | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="card mb-6">
        <h2 className="font-semibold text-lg mb-4">Model Transparency</h2>
        <p className="text-sm text-ink/40">Loading…</p>
      </div>
    );
  }
  if (!data) return null;

  const maxImportance = Math.max(...data.top_features.map((f) => f.avg_importance), 0.001);
  const totalTier = Object.values(data.tier_distribution).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">Model Transparency</h2>
      <p className="text-xs text-ink/40 mb-4">
        Active prediction model performance and global feature influence across all patients.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Algorithm</div>
          <div className="font-semibold mt-1 capitalize">{data.algorithm.replace(/_/g, " ")}</div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Version</div>
          <div className="font-semibold mt-1">{data.version}</div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">CV AUC</div>
          <div className="font-semibold mt-1 text-ink">
            {data.cv_auc != null ? data.cv_auc.toFixed(3) : "—"}
          </div>
        </div>
        <div>
          <div className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-ink/40">Test AUC</div>
          <div className="font-semibold mt-1 text-ink">
            {data.test_auc != null ? data.test_auc.toFixed(3) : "—"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-ink/60 mb-3">
            Top influencing factors (global avg |SHAP|)
          </h3>
          <div className="space-y-2">
            {data.top_features.map((f) => (
              <div key={f.feature_name}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-ink/60">{f.humanized_label}</span>
                  <span className="text-ink/40">{f.avg_importance.toFixed(3)}</span>
                </div>
                <div className="h-2 rounded-full bg-tint">
                  <div
                    className="h-2 rounded-full bg-ink"
                    style={{ width: `${(f.avg_importance / maxImportance) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-ink/60 mb-3">
            Risk tier distribution ({data.total_predictions} predictions)
          </h3>
          <div className="space-y-3">
            {(["High", "Medium", "Low"] as const).map((tier) => {
              const count = data.tier_distribution[tier];
              const pct = Math.round((count / totalTier) * 100);
              const colors: Record<string, string> = {
                High: "bg-risk-high",
                Medium: "bg-risk-medium",
                Low: "bg-risk-low",
              };
              return (
                <div key={tier}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="text-ink/60">{tier} Risk</span>
                    <span className="text-ink/40">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-tint">
                    <div
                      className={`h-2 rounded-full ${colors[tier]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
