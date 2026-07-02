import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, api, Patient, Recommendation, RiskExplanation, RiskSummary }
  from "@/lib/api";
import { RiskGauge } from "@/components/RiskGauge";
import { RiskBadge } from "@/components/clinical/RiskBadge";
import { TransitionTab } from "@/components/clinical/TransitionTab";
import { ShapBar } from "@/components/clinical/ShapBar";
import { Card } from "@/components/core/Card";
import { Button } from "@/components/core/Button";
import { Badge } from "@/components/core/Badge";

interface ChatTurn { role: "user" | "assistant"; content: string; }

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
      {children}
    </div>
  );
}

export function PatientChart() {
  const { id } = useParams<{ id: string }>();
  const patientId = id!;
  const qc = useQueryClient();
  const [tab, setTab] = useState<"overview" | "transition">("overview");

  const patient = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.get<Patient>(`/patients/${patientId}`),
  });

  const risk = useQuery<RiskSummary, ApiError>({
    queryKey: ["risk", patientId],
    queryFn: () => api.get<RiskSummary>(`/patients/${patientId}/risk`),
    retry: false,
  });

  const explanation = useQuery<RiskExplanation, ApiError>({
    queryKey: ["explanation", patientId],
    queryFn: () => api.get<RiskExplanation>(`/patients/${patientId}/explanations`),
    enabled: risk.isSuccess,
    retry: false,
  });

  const recs = useQuery<Recommendation[], ApiError>({
    queryKey: ["recs", patientId],
    queryFn: () => api.get<Recommendation[]>(`/patients/${patientId}/recommendations`),
    enabled: risk.isSuccess,
    retry: false,
  });

  const admissions = useQuery({
    queryKey: ["admissions", patientId],
    queryFn: () => api.get<Array<{ id: string }>>(`/patients/${patientId}/admissions`),
  });

  const generatePrediction = useMutation({
    mutationFn: async () => {
      if (!admissions.data?.[0]) throw new Error("No admission found for this patient.");
      const threshold = parseFloat(localStorage.getItem("careinsight.default_threshold") ?? "0.5");
      return api.post("/predictions", { admission_id: admissions.data[0].id, threshold });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["risk", patientId] });
      qc.invalidateQueries({ queryKey: ["explanation", patientId] });
      qc.invalidateQueries({ queryKey: ["recs", patientId] });
    },
  });

  const downloadPdf = useMutation({
    mutationFn: async () => {
      if (!risk.data?.prediction_id) return;
      const blob = await api.post<Blob>("/reports/pdf",
        { prediction_id: risk.data.prediction_id });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `careinsight_${patient.data?.mrn}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 150);
    },
  });

  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [chatInput, setChatInput] = useState("");
  const askAi = useMutation({
    mutationFn: async (message: string) => {
      const resp = await api.post<{ reply: string }>("/chat", {
        patient_id: patientId, message, history: chat,
      });
      return resp.reply;
    },
    onMutate: (message) => {
      setChat((c) => [...c, { role: "user", content: message }]);
    },
    onSuccess: (reply) => {
      setChat((c) => [...c, { role: "assistant", content: reply }]);
    },
    onError: () => {
      setChat((c) => [...c, {
        role: "assistant",
        content: "Could not reach the AI assistant. Please try again.",
      }]);
    },
  });

  function onAsk(e: FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || askAi.isPending) return;
    askAi.mutate(chatInput);
    setChatInput("");
  }

  if (patient.isLoading) return <div className="p-6 text-sm text-slate-500">Loading patient…</div>;
  if (patient.isError) return <div className="p-6 text-sm text-risk-high">Patient not found.</div>;

  const p = patient.data!;
  const riskTier = ((risk.data?.risk_tier ?? 'low').toLowerCase() as 'high' | 'medium' | 'low');

  return (
    <div className="space-y-5">
      {/* Patient header */}
      <Card noPadding>
        <div className="flex flex-wrap items-start gap-4 justify-between p-6">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-display text-xl font-semibold text-navy-700 m-0 leading-tight">
                {p.last_name}, {p.first_name}
              </h1>
              {risk.data && <RiskBadge tier={riskTier} />}
            </div>
            <div className="text-sm text-slate-500 flex items-center gap-2">
              <span>MRN <span className="font-mono text-slate-700">{p.mrn}</span></span>
              <span className="text-slate-300">·</span>
              <span>DOB {p.dob}</span>
              <span className="text-slate-300">·</span>
              <span>{p.sex}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => generatePrediction.mutate()}
              disabled={generatePrediction.isPending}
              icon={generatePrediction.isPending ? <Spinner /> : undefined}
            >
              {risk.data ? "Re-run prediction" : "Run prediction"}
            </Button>
            <Button
              variant="primary"
              onClick={() => downloadPdf.mutate()}
              disabled={!risk.data || downloadPdf.isPending}
            >
              Generate PDF
            </Button>
          </div>
        </div>
      </Card>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-200">
        {(["overview", "transition"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t === "overview" ? "Overview" : "Transition & Follow-Up"}
          </button>
        ))}
      </div>

      {tab === "transition" && (
        <TransitionTab patientId={patientId} admissionId={admissions.data?.[0]?.id ?? null} />
      )}

      {tab === "overview" && (<>
      {/* Main 3-col grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Left col — Risk gauge */}
        <Card className="lg:col-span-1">
          <SectionLabel>Readmission Risk</SectionLabel>

          {generatePrediction.isPending && (
            <div className="space-y-3 animate-pulse">
              <div className="h-32 bg-slate-100 rounded-lg" />
              <div className="h-3 bg-slate-100 rounded w-3/4 mx-auto" />
              <p className="text-xs text-slate-400 text-center">Calculating risk…</p>
            </div>
          )}

          {!generatePrediction.isPending && risk.isError && (
            <p className="text-sm text-slate-500">
              No prediction yet. Click <em>Run Prediction</em> above.
            </p>
          )}

          {generatePrediction.error && (
            <p className="text-sm text-risk-high mt-2">
              {(generatePrediction.error as Error).message}
            </p>
          )}

          {!generatePrediction.isPending && risk.data && (
            <RiskGauge
              probability={risk.data.probability}
              threshold={risk.data.threshold_used}
              riskTier={riskTier}
              modelName={risk.data.model_name}
              modelVersion={risk.data.model_version}
            />
          )}
        </Card>

        {/* Right col — SHAP + Checklist stacked */}
        <div className="lg:col-span-2 flex flex-col gap-5">
          <Card>
            <SectionLabel>Top Risk Drivers</SectionLabel>
            {!explanation.data ? (
              <p className="text-sm text-slate-500">
                Run a prediction to see SHAP-based clinical drivers.
              </p>
            ) : (
              <div className="space-y-2.5">
                {explanation.data.factors.slice(0, 8).map((f, i) => (
                  <ShapBar
                    key={i}
                    rank={i + 1}
                    label={f.humanized_label}
                    shapValue={f.shap_value}
                    maxAbsValue={Math.max(...explanation.data!.factors.map(x => Math.abs(x.shap_value)), 0.1)}
                  />
                ))}
              </div>
            )}
          </Card>

          <Card>
            <SectionLabel>Discharge Checklist</SectionLabel>
            {!recs.data ? (
              <p className="text-sm text-slate-500">No recommendations yet.</p>
            ) : (
              <ul className="space-y-2.5">
                {recs.data.map((r, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <input
                      type="checkbox"
                      className="mt-0.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0"
                    />
                    <span className="text-sm text-slate-700 flex-1 leading-snug">{r.text}</span>
                    {r.source !== "base" && (
                      <Badge variant="outline" size="xs">{r.source}</Badge>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      {/* AI Copilot — full width */}
      <Card>
        <SectionLabel>AI Clinical Copilot</SectionLabel>
        <p className="text-xs text-slate-400 mb-3">
          Decision-support only — not a substitute for clinical judgment.
        </p>
        <div className="min-h-[6rem] max-h-72 overflow-y-auto space-y-2 mb-3">
          {chat.length === 0 && (
            <p className="text-xs text-slate-400 italic">
              Ask about this patient's risk factors, recommended interventions, or clinical context.
            </p>
          )}
          {chat.map((t, i) => (
            <div
              key={i}
              className={[
                "text-sm rounded-md px-3 py-2 whitespace-pre-wrap leading-relaxed",
                t.role === "user"
                  ? "bg-brand-50 text-brand-700 ml-8"
                  : "bg-slate-50 text-slate-800 mr-8",
              ].join(" ")}
            >
              {t.content}
            </div>
          ))}
          {askAi.isPending && (
            <div className="bg-slate-50 rounded-md px-3 py-3 flex items-center gap-1.5 mr-8">
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
            </div>
          )}
        </div>
        <form onSubmit={onAsk} className="flex gap-2">
          <input
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask why this patient is high risk…"
            disabled={askAi.isPending}
            className="flex-1 font-sans text-sm px-3 py-2 border border-slate-300 rounded-md
                       focus:outline-none focus:shadow-focus focus:border-brand-600
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <Button type="submit" disabled={askAi.isPending}>
            Ask
          </Button>
        </form>
      </Card>
      </>)}

      <footer className="text-xs text-slate-400 italic border-t border-slate-200 pt-4">
        CONFIDENTIAL — Protected Health Information. Decision-support only — not a substitute for clinical judgment.
      </footer>
    </div>
  );
}
