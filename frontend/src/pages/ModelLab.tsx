import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ModelStatsResponse, PopulationResponse, RetrainResult } from "@/lib/api";
import { Button } from "@/components/core/Button";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";
import { tokenStore } from "@/lib/api";

const THRESHOLD_KEY = "careinsight.default_threshold";
const GAP_KEY = "careinsight.medium_gap";

const TIER_COLORS = {
  High:   { text: "#B42318", bg: "#FEF3F2", border: "#FECDCA" },
  Medium: { text: "#B54708", bg: "#FFFAEB", border: "#FEDF89" },
  Low:    { text: "#067647", bg: "#ECFDF3", border: "#ABEFC6" },
} as const;

function getStored(key: string, fallback: number) {
  return parseFloat(localStorage.getItem(key) ?? String(fallback));
}

export function ModelLab() {
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [threshold, setThreshold] = useState(() => getStored(THRESHOLD_KEY, 0.5));
  const [gap, setGap] = useState(() => getStored(GAP_KEY, 0.15));
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [retrainFile, setRetrainFile] = useState<File | null>(null);
  const [retrainResult, setRetrainResult] = useState<RetrainResult | null>(null);

  const modelStats = useQuery({
    queryKey: ["model-stats"],
    queryFn: () => api.get<ModelStatsResponse>("/dashboard/model-stats"),
  });

  const population = useQuery({
    queryKey: ["population-all-ml"],
    queryFn: () => api.get<PopulationResponse>("/dashboard/population"),
  });

  const retrain = useMutation({
    mutationFn: async () => {
      if (!retrainFile) throw new Error("No file selected");
      const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
      const token = tokenStore.get();
      const body = new FormData();
      body.append("file", retrainFile);
      const resp = await fetch(`${base}/admin/model/retrain`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body,
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? `HTTP ${resp.status}`);
      }
      return resp.json() as Promise<RetrainResult>;
    },
    onSuccess: (result) => {
      setRetrainResult(result);
      setRetrainFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      qc.invalidateQueries({ queryKey: ["model-stats"] });
    },
  });

  function saveConfig() {
    localStorage.setItem(THRESHOLD_KEY, String(threshold));
    localStorage.setItem(GAP_KEY, String(gap));
    setSavedAt(Date.now());
  }

  const patients = population.data?.patients ?? [];
  const previewHigh   = patients.filter(p => p.probability >= threshold).length;
  const previewMedium = patients.filter(p => p.probability >= threshold - gap && p.probability < threshold).length;
  const previewLow    = patients.filter(p => p.probability < threshold - gap).length;
  const previewTotal  = patients.length;

  const stats = modelStats.data;
  const maxImportance = Math.max(...(stats?.top_features.map(f => f.avg_importance) ?? [0.01]), 0.01);
  const tierTotal = stats
    ? Object.values(stats.tier_distribution).reduce((a, b) => a + b, 0)
    : 0;

  const isSaved = savedAt !== null && Date.now() - savedAt < 3000;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">
          Model <em className="font-serifit font-normal italic">lab.</em>
        </h1>
        <p className="text-sm text-ink/50 mt-2">
          Configure risk thresholds, monitor model performance, and retrain.
        </p>
      </div>

      {/* ── Threshold Configuration ─────────────────────────────────────────── */}
      <Card>
        <SectionLabel>Risk Threshold Configuration</SectionLabel>
        <p className="text-xs text-ink/40 mb-6">
          Threshold changes apply to all new predictions. The live preview below
          recalculates tiers against stored probabilities for the {previewTotal} currently
          admitted patients with predictions.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sliders */}
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-ink/80">High-risk cutoff</label>
                <span className="font-mono text-xl font-bold text-ink">
                  {(threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range" min="0.20" max="0.90" step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full h-2 bg-hairline rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5
                  [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-risk-high [&::-webkit-slider-thumb]:cursor-pointer
                  [&::-webkit-slider-thumb]:shadow-sm"
              />
              <div className="flex justify-between text-[0.65rem] text-ink/40 mt-1.5">
                <span>20%</span>
                <span className="text-risk-high font-medium">High ≥ {(threshold * 100).toFixed(0)}%</span>
                <span>90%</span>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-ink/80">Medium-risk band width</label>
                <span className="font-mono text-base font-semibold text-ink/60">
                  {((threshold - gap) * 100).toFixed(0)}–{(threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range" min="0.05" max="0.30" step="0.05"
                value={gap}
                onChange={(e) => setGap(parseFloat(e.target.value))}
                className="w-full h-2 bg-hairline rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5
                  [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-risk-medium [&::-webkit-slider-thumb]:cursor-pointer"
              />
              <div className="flex justify-between text-[0.65rem] text-ink/40 mt-1.5">
                <span>±5 pp</span>
                <span className="text-risk-medium font-medium">Gap = {(gap * 100).toFixed(0)} pp</span>
                <span>±30 pp</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="primary" onClick={saveConfig}>
                {isSaved ? "Saved ✓" : "Save Configuration"}
              </Button>
              <span className="text-xs text-ink/40">
                Persisted in this browser
              </span>
            </div>

            <div className="text-xs text-ink/40 border border-hairline rounded-md p-3 bg-tint font-mono space-y-0.5">
              <div>High  ≥ {(threshold * 100).toFixed(0)}%</div>
              <div>Med   {((threshold - gap) * 100).toFixed(0)}% – {(threshold * 100).toFixed(0)}%</div>
              <div>Low   &lt; {((threshold - gap) * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Live tier preview */}
          <div>
            <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-3">
              Live Preview — {previewTotal} patients
            </div>
            {previewTotal === 0 ? (
              <p className="text-sm text-ink/40">
                {population.isLoading ? "Loading…" : "No admitted patients with predictions yet."}
              </p>
            ) : (
              <div className="space-y-2.5">
                {(["High", "Medium", "Low"] as const).map((tier) => {
                  const count = tier === "High" ? previewHigh : tier === "Medium" ? previewMedium : previewLow;
                  const pct = previewTotal > 0 ? Math.round((count / previewTotal) * 100) : 0;
                  const c = TIER_COLORS[tier];
                  return (
                    <div
                      key={tier}
                      className="flex items-center gap-3 p-3 rounded-lg border"
                      style={{ borderColor: c.border, background: c.bg + "90" }}
                    >
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                        style={{ background: c.bg, border: `1.5px solid ${c.border}` }}
                      >
                        <span className="font-mono text-2xl font-bold" style={{ color: c.text }}>
                          {count}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold" style={{ color: c.text }}>
                          {tier} Risk
                        </div>
                        <div className="h-1.5 bg-white/60 rounded-full overflow-hidden mt-1.5">
                          <div
                            className="h-full rounded-full transition-[width] duration-300"
                            style={{ width: `${pct}%`, background: c.text }}
                          />
                        </div>
                      </div>
                      <span className="font-mono text-sm font-bold shrink-0" style={{ color: c.text }}>
                        {pct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* ── Model Stats + Feature Importance ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Active Model */}
        <Card>
          <SectionLabel>Active Model</SectionLabel>
          {!stats ? (
            <p className="text-sm text-ink/40">{modelStats.isLoading ? "Loading…" : "No model data."}</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Algorithm", value: stats.algorithm, mono: true },
                  { label: "Version",   value: stats.version,   mono: true },
                  {
                    label: "CV AUC",
                    value: stats.cv_auc != null ? stats.cv_auc.toFixed(3) : "—",
                    mono: true, large: true,
                  },
                  {
                    label: "Test AUC",
                    value: stats.test_auc != null ? stats.test_auc.toFixed(3) : "—",
                    mono: true, large: true,
                  },
                ].map(({ label, value, mono, large }) => (
                  <div key={label} className="p-3 rounded-lg bg-tint border border-hairline">
                    <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-1">
                      {label}
                    </div>
                    <div className={[
                      large ? "text-2xl font-bold text-ink" : "text-sm font-semibold text-ink/80",
                      mono ? "font-mono" : "font-sans capitalize",
                    ].join(" ")}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 text-sm text-ink/50 border-t border-hairline pt-3">
                <span className="text-xs text-ink/40">Trained</span>
                <span className="font-mono text-xs">
                  {stats.trained_at
                    ? new Date(stats.trained_at).toLocaleString()
                    : "Not yet trained"}
                </span>
              </div>

              <div>
                <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
                  Historical Prediction Distribution ({stats.total_predictions} total)
                </div>
                <div className="space-y-1.5">
                  {(["High", "Medium", "Low"] as const).map((tier) => {
                    const count = stats.tier_distribution[tier] ?? 0;
                    const pct = tierTotal > 0 ? (count / tierTotal) * 100 : 0;
                    return (
                      <div key={tier} className="flex items-center gap-2">
                        <span className="text-xs text-ink/50 w-14">{tier}</span>
                        <div className="flex-1 h-2 bg-tint rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${pct}%`, background: TIER_COLORS[tier].text }}
                          />
                        </div>
                        <span className="font-mono text-xs text-ink/60 w-8 text-right">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* Feature Importance */}
        <Card>
          <SectionLabel>Feature Importance — Avg. |SHAP|</SectionLabel>
          {!stats || stats.top_features.length === 0 ? (
            <p className="text-sm text-ink/40">
              {modelStats.isLoading
                ? "Loading…"
                : "No prediction data yet. Run predictions to populate."}
            </p>
          ) : (
            <div className="space-y-3">
              {stats.top_features.map((f, i) => (
                <div key={f.feature_name} className="flex items-center gap-2.5">
                  <span className="font-mono text-xs text-ink/40 w-4 shrink-0 text-right">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-ink/80 truncate mb-1">{f.humanized_label}</div>
                    <div className="h-2 bg-tint rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-ink transition-[width] duration-500"
                        style={{ width: `${(f.avg_importance / maxImportance) * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="font-mono text-xs text-ink/50 w-12 text-right shrink-0">
                    {f.avg_importance.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* ── Retrain ────────────────────────────────────────────────────────── */}
      <Card>
        <SectionLabel>Retrain Model</SectionLabel>
        <p className="text-xs text-ink/40 mb-4 leading-relaxed">
          Upload a CSV matching the training schema. Expected columns:{" "}
          <span className="font-mono">
            patient_id, age, gender, weight_kg, height_cm, bmi,
            num_previous_admissions, chronic_conditions, medications_count,
            last_hemoglobin, last_glucose, last_creatinine, admission_type,
            length_of_stay, procedures_count, smoking_status, alcohol_use,
            physical_activity, insurance_type, followup_compliance,
            social_support, mental_health_issue, readmission_risk
          </span>.{" "}
          Logistic Regression, Random Forest, and XGBoost are all trained; the best
          by cross-validated AUC is selected and hot-swapped into memory.
        </p>

        <div className="flex items-center gap-4 flex-wrap">
          <div
            className={[
              "flex-1 min-w-[200px] border-2 border-dashed rounded-lg px-4 py-4 cursor-pointer transition-colors",
              retrainFile
                ? "border-ink/40 bg-tint"
                : "border-hairline hover:border-ink/30 bg-tint/50",
            ].join(" ")}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                setRetrainFile(e.target.files?.[0] ?? null);
                setRetrainResult(null);
              }}
            />
            {retrainFile ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-ink font-medium truncate">{retrainFile.name}</span>
                <span className="text-xs text-ink/40 shrink-0">
                  ({(retrainFile.size / 1024).toFixed(0)} KB)
                </span>
              </div>
            ) : (
              <p className="text-sm text-ink/40">Click to select CSV…</p>
            )}
          </div>

          <Button
            variant="secondary"
            disabled={!retrainFile}
            loading={retrain.isPending}
            onClick={() => retrain.mutate()}
          >
            {retrain.isPending ? "Training…" : "Retrain Model"}
          </Button>
        </div>

        {retrain.isPending && (
          <div className="mt-4 text-sm text-ink/50 flex items-center gap-2">
            <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Training in progress — this may take up to a minute…
          </div>
        )}

        {retrain.isError && (
          <div className="mt-3 text-sm text-risk-high bg-risk-high-bg px-3 py-2 rounded-md">
            {(retrain.error as Error).message}
          </div>
        )}

        {retrainResult && (
          <div className="mt-4 p-4 rounded-lg bg-risk-low-bg border border-risk-low-border">
            <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-risk-low mb-3">
              Training Complete
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-ink/40 mb-0.5">Algorithm</div>
                <div className="font-mono text-sm font-semibold text-ink capitalize">
                  {retrainResult.algorithm}
                </div>
              </div>
              <div>
                <div className="text-xs text-ink/40 mb-0.5">CV AUC</div>
                <div className="font-mono text-2xl font-bold text-risk-low">
                  {retrainResult.cv_auc?.toFixed(3) ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-xs text-ink/40 mb-0.5">Test AUC</div>
                <div className="font-mono text-2xl font-bold text-risk-low">
                  {retrainResult.test_auc?.toFixed(3) ?? "—"}
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      <footer className="text-xs text-ink/40 italic border-t border-hairline pt-4">
        Decision-support only — not a substitute for clinical judgment.
      </footer>
    </div>
  );
}
