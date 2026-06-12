import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, api, Patient, Recommendation, RiskExplanation, RiskSummary }
  from "@/lib/api";
import { RiskGauge } from "@/components/RiskGauge";

interface ChatTurn { role: "user" | "assistant"; content: string; }

export function PatientChart() {
  const { id } = useParams<{ id: string }>();
  const patientId = id!;
  const qc = useQueryClient();

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
      return api.post("/predictions", { admission_id: admissions.data[0].id, threshold: 0.5 });
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
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  // AI chat
  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [chatInput, setChatInput] = useState("");
  const askAi = useMutation({
    mutationFn: async (message: string) => {
      const resp = await api.post<{ reply: string }>("/chat", {
        patient_id: patientId, message, history: chat,
      });
      return resp.reply;
    },
    onSuccess: (reply, message) => {
      setChat((c) => [...c, { role: "user", content: message },
                            { role: "assistant", content: reply }]);
    },
  });

  function onAsk(e: FormEvent) {
    e.preventDefault();
    if (!chatInput.trim()) return;
    askAi.mutate(chatInput);
    setChatInput("");
  }

  if (patient.isLoading) return <div>Loading patient…</div>;
  if (patient.isError) return <div className="text-red-600">Patient not found.</div>;

  return (
    <div className="space-y-6">
      <header className="card flex flex-wrap items-start gap-4 justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Patient</div>
          <h1 className="text-2xl font-bold">
            {patient.data!.last_name}, {patient.data!.first_name}
          </h1>
          <div className="text-sm text-slate-600 mt-1">
            MRN <span className="font-mono">{patient.data!.mrn}</span> ·
            DOB {patient.data!.dob} · {patient.data!.sex}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            className="btn-secondary"
            onClick={() => generatePrediction.mutate()}
            disabled={generatePrediction.isPending}
          >
            {risk.data ? "Re-run prediction" : "Run prediction"}
          </button>
          <button
            className="btn-primary"
            onClick={() => downloadPdf.mutate()}
            disabled={!risk.data || downloadPdf.isPending}
          >
            Generate PDF
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="card lg:col-span-1">
          <h2 className="font-semibold mb-3">Readmission risk</h2>
          {risk.isError && (
            <div className="text-sm text-slate-500">
              No prediction yet. Click <em>Run prediction</em>.
            </div>
          )}
          {risk.data && (
            <>
              <RiskGauge
                probability={risk.data.probability}
                threshold={risk.data.threshold_used}
                riskTier={risk.data.risk_tier}
              />
              <div className="text-xs text-slate-500 mt-3">
                Model: {risk.data.model_name} v{risk.data.model_version}
              </div>
            </>
          )}
        </section>

        <section className="card lg:col-span-2">
          <h2 className="font-semibold mb-3">Top risk drivers (SHAP)</h2>
          {!explanation.data && (
            <div className="text-sm text-slate-500">
              Run a prediction to see SHAP-based clinical drivers.
            </div>
          )}
          {explanation.data && (
            <ul className="space-y-2">
              {explanation.data.factors.slice(0, 8).map((f, i) => (
                <li key={i} className="flex items-center gap-3">
                  <span className="text-xs font-mono text-slate-400 w-5">{i + 1}.</span>
                  <span className="flex-1 text-sm">{f.humanized_label}</span>
                  <span className={`text-sm font-medium ${
                    f.shap_value > 0 ? "text-risk-high" : "text-risk-low"
                  }`}>
                    {f.shap_value > 0 ? "↑ increases" : "↓ protective"}
                    {" "}({f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(3)})
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card lg:col-span-2">
          <h2 className="font-semibold mb-3">Preventive action checklist</h2>
          {!recs.data && (
            <div className="text-sm text-slate-500">No recommendations yet.</div>
          )}
          {recs.data && (
            <ul className="space-y-2">
              {recs.data.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <input type="checkbox" className="mt-1" />
                  <span>{r.text}</span>
                  {r.source !== "base" && (
                    <span className="text-xs text-slate-400 italic">
                      ({r.source})
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card lg:col-span-1 flex flex-col">
          <h2 className="font-semibold mb-3">Ask AI about this patient</h2>
          <div className="flex-1 overflow-y-auto space-y-2 mb-3 max-h-72">
            {chat.length === 0 && (
              <div className="text-xs text-slate-400 italic">
                Decision-support only — explanations of risk factors, not clinical advice.
              </div>
            )}
            {chat.map((t, i) => (
              <div key={i}
                   className={`text-sm rounded-md px-3 py-2 ${
                     t.role === "user"
                       ? "bg-brand-50 text-brand-700"
                       : "bg-slate-50 text-slate-800"
                   }`}>
                {t.content}
              </div>
            ))}
          </div>
          <form onSubmit={onAsk} className="flex gap-2">
            <input
              value={chatInput} onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask why this patient is high risk…"
              className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-md
                         focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <button className="btn-primary text-sm" disabled={askAi.isPending}>
              Ask
            </button>
          </form>
        </section>
      </div>

      <footer className="text-xs text-slate-400 italic">
        CONFIDENTIAL — Protected Health Information. Decision-support only — not a substitute
        for clinical judgment.
      </footer>
    </div>
  );
}
