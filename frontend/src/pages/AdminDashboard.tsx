import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ModelStatsResponse } from "@/lib/api";

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
      <h1 className="text-2xl font-bold mb-6">Administrator dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">Total predictions</div>
          <div className="text-3xl font-bold mt-1">
            {stats.data?.total_predictions ?? "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">High-risk rate</div>
          <div className="text-3xl font-bold mt-1 text-risk-high">
            {stats.data ? `${(stats.data.high_risk_rate * 100).toFixed(1)}%` : "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">Period</div>
          <div className="text-3xl font-bold mt-1">{stats.data?.period ?? "—"}</div>
        </div>
      </div>

      <RoiCalculator />
      <ModelTransparency data={modelStats.data} isLoading={modelStats.isLoading} />

      {stats.data?.note && (
        <p className="text-xs text-slate-500 italic mt-4">{stats.data.note}</p>
      )}
    </div>
  );
}

function RoiCalculator() {
  const [beds, setBeds] = useState(300);
  const [monthlyAdmissions, setMonthlyAdmissions] = useState(250);
  const [readmissionRate, setReadmissionRate] = useState(13);
  const [costPerReadmission, setCostPerReadmission] = useState(5000);

  const annualReadmissions = Math.round((monthlyAdmissions * 12 * readmissionRate) / 100);
  const highRiskCount = Math.round(annualReadmissions * 0.3);
  const preventedLow = Math.round(highRiskCount * 0.15);
  const preventedHigh = Math.round(highRiskCount * 0.20);
  const savingsLow = preventedLow * costPerReadmission;
  const savingsHigh = preventedHigh * costPerReadmission;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">ROI Impact Calculator</h2>
      <p className="text-xs text-slate-400 mb-4">
        Projected savings based on published literature on clinical decision support tools
        (15–20% reduction in high-risk readmissions).
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Total beds</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={beds}
            onChange={(e) => setBeds(Number(e.target.value))}
            min={50}
            max={2000}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Monthly admissions</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={monthlyAdmissions}
            onChange={(e) => setMonthlyAdmissions(Number(e.target.value))}
            min={10}
            max={5000}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Readmission rate (%)</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={readmissionRate}
            onChange={(e) => setReadmissionRate(Number(e.target.value))}
            min={1}
            max={40}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Cost per readmission ($)</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={costPerReadmission}
            onChange={(e) => setCostPerReadmission(Number(e.target.value))}
            min={500}
            max={50000}
          />
        </label>
      </div>

      <div className="bg-slate-50 rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Annual readmissions</div>
          <div className="text-2xl font-bold mt-1">{annualReadmissions.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            High-risk patients flagged / year
          </div>
          <div className="text-2xl font-bold mt-1 text-yellow-600">
            ~{highRiskCount.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Estimated annual savings
          </div>
          <div className="text-2xl font-bold mt-1 text-green-600">
            ${savingsLow.toLocaleString()} – ${savingsHigh.toLocaleString()}
          </div>
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
        <p className="text-sm text-slate-400">Loading…</p>
      </div>
    );
  }
  if (!data) return null;

  const maxImportance = Math.max(...data.top_features.map((f) => f.avg_importance), 0.001);
  const totalTier = Object.values(data.tier_distribution).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">Model Transparency</h2>
      <p className="text-xs text-slate-400 mb-4">
        Active prediction model performance and global feature influence across all patients.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Algorithm</div>
          <div className="font-semibold mt-1 capitalize">{data.algorithm.replace(/_/g, " ")}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Version</div>
          <div className="font-semibold mt-1">{data.version}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">CV AUC</div>
          <div className="font-semibold mt-1 text-brand-700">
            {data.cv_auc != null ? data.cv_auc.toFixed(3) : "—"}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Test AUC</div>
          <div className="font-semibold mt-1 text-brand-700">
            {data.test_auc != null ? data.test_auc.toFixed(3) : "—"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-slate-600 mb-3">
            Top influencing factors (global avg |SHAP|)
          </h3>
          <div className="space-y-2">
            {data.top_features.map((f) => (
              <div key={f.feature_name}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-slate-600">{f.humanized_label}</span>
                  <span className="text-slate-400">{f.avg_importance.toFixed(3)}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-brand-600"
                    style={{ width: `${(f.avg_importance / maxImportance) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-slate-600 mb-3">
            Risk tier distribution ({data.total_predictions} predictions)
          </h3>
          <div className="space-y-3">
            {(["High", "Medium", "Low"] as const).map((tier) => {
              const count = data.tier_distribution[tier];
              const pct = Math.round((count / totalTier) * 100);
              const colors: Record<string, string> = {
                High: "bg-red-500",
                Medium: "bg-yellow-400",
                Low: "bg-green-500",
              };
              return (
                <div key={tier}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="text-slate-600">{tier} Risk</span>
                    <span className="text-slate-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
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
