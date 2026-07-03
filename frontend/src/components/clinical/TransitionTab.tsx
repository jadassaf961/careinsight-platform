import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ApiError, api, Checkin, Escalation, MetaResponse, TransitionPlan,
} from "@/lib/api";
import { Card } from "@/components/core/Card";
import { Button } from "@/components/core/Button";
import { SectionLabel } from "@/components/core/SectionLabel";
import { SimulatedPhone } from "@/components/clinical/SimulatedPhone";

const CHECKIN_STATUS_STYLE: Record<string, string> = {
  scheduled: "bg-tint text-ink/60",
  sent: "bg-tint text-ink/60 border border-hairline",
  responded: "bg-risk-low-bg text-risk-low border border-risk-low-border",
  no_response: "bg-risk-medium-bg text-risk-medium border border-risk-medium-border",
  send_failed: "bg-risk-high-bg text-risk-high border border-risk-high-border",
  manual: "bg-tint text-ink/60 border border-hairline",
  skipped: "bg-tint text-ink/40",
};

const PRIORITY_STYLE: Record<string, string> = {
  high: "text-risk-high",
  medium: "text-risk-medium",
  low: "text-ink/50",
};

export function TransitionTab({ patientId, admissionId }: { patientId: string; admissionId: string | null }) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["transition-plan", patientId] });
    qc.invalidateQueries({ queryKey: ["checkins", patientId] });
    qc.invalidateQueries({ queryKey: ["escalations", patientId] });
    qc.invalidateQueries({ queryKey: ["transition-board"] });
  };

  const plan = useQuery<TransitionPlan, ApiError>({
    queryKey: ["transition-plan", patientId],
    queryFn: () => api.get<TransitionPlan>(`/transitions/plans/by-patient/${patientId}`),
    retry: false,
  });

  const checkins = useQuery<Checkin[], ApiError>({
    queryKey: ["checkins", patientId],
    queryFn: () => api.get<Checkin[]>(`/checkins?patient_id=${patientId}`),
  });

  const escalations = useQuery<Escalation[], ApiError>({
    queryKey: ["escalations", patientId],
    queryFn: () => api.get<Escalation[]>(`/escalations?patient_id=${patientId}`),
  });

  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: () => api.get<MetaResponse>("/meta"),
    staleTime: Infinity,
  });

  const createPlan = useMutation({
    mutationFn: () => api.post("/transitions/plans", { admission_id: admissionId }),
    onSuccess: invalidate,
  });
  const updateTask = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      api.patch(`/transitions/tasks/${taskId}`, { status }),
    onSuccess: invalidate,
  });
  const discharge = useMutation({
    mutationFn: () => api.post(`/transitions/plans/${plan.data!.id}/discharge`),
    onSuccess: invalidate,
  });
  const refreshTasks = useMutation({
    mutationFn: () => api.post(`/transitions/plans/${plan.data!.id}/refresh-tasks`),
    onSuccess: invalidate,
  });

  if (plan.isError && plan.error.status === 404) {
    return (
      <Card>
        <SectionLabel>Transition Plan</SectionLabel>
        <p className="text-sm text-ink/50 mb-3">
          No discharge planning has started for this patient.
        </p>
        <Button onClick={() => createPlan.mutate()} disabled={!admissionId || createPlan.isPending}>
          Start discharge planning
        </Button>
        {!admissionId && (
          <p className="text-xs text-ink/40 mt-2">Requires an admission on record.</p>
        )}
      </Card>
    );
  }

  const tasks = plan.data?.tasks ?? [];
  const byRole = tasks.reduce<Record<string, typeof tasks>>((acc, t) => {
    (acc[t.role] ??= []).push(t);
    return acc;
  }, {});
  const openCount = tasks.filter((t) => t.status === "open").length;

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <SectionLabel>Transition Checklist</SectionLabel>
            <p className="text-xs text-ink/40 -mt-2 mb-3">
              Plan status: <span className="font-medium text-ink/60">{plan.data?.status ?? "…"}</span>
              {" · "}{openCount} task{openCount !== 1 ? "s" : ""} open
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => refreshTasks.mutate()}
              disabled={!plan.data || refreshTasks.isPending}>
              Refresh from latest risk
            </Button>
            {plan.data?.status === "planning" && (
              <Button onClick={() => discharge.mutate()} disabled={discharge.isPending}>
                Confirm discharge
              </Button>
            )}
          </div>
        </div>
        {plan.isLoading && <p className="text-sm text-ink/40">Loading…</p>}
        {Object.entries(byRole).map(([role, roleTasks]) => (
          <div key={role} className="mb-4 last:mb-0">
            <div className="text-xs font-semibold uppercase tracking-wide text-ink/40 mb-1.5">
              {role.replace("_", " ")}
            </div>
            <div className="space-y-1">
              {roleTasks.map((t) => (
                <label
                  key={t.id}
                  className="flex items-start gap-2.5 p-2 rounded hover:bg-tint cursor-pointer"
                >
                  <input
                    type="checkbox"
                    className="mt-0.5 accent-ink"
                    checked={t.status === "done"}
                    onChange={() =>
                      updateTask.mutate({
                        taskId: t.id,
                        status: t.status === "done" ? "open" : "done",
                      })
                    }
                  />
                  <span className={`text-sm ${t.status === "done" ? "line-through text-ink/40" : "text-ink/80"}`}>
                    {t.title}
                    {t.source !== "default" && (
                      <span className="ml-2 text-[0.65rem] text-ink/60 bg-tint rounded px-1.5 py-0.5">
                        from risk: {t.source}
                      </span>
                    )}
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </Card>

      <Card>
        <SectionLabel>Post-Discharge Follow-Up</SectionLabel>
        {(checkins.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-ink/50">
            Check-ins are scheduled automatically when discharge is confirmed.
          </p>
        ) : (
          <div className="space-y-2">
            {checkins.data!.map((c) => (
              <div key={c.id} className="flex items-start justify-between gap-3 py-2 border-b border-hairline/60 last:border-0">
                <div>
                  <div className="text-sm font-medium text-ink/80">Day {c.day_offset} check-in</div>
                  <div className="text-xs text-ink/40">
                    {new Date(c.scheduled_at).toLocaleDateString()} · {c.language.toUpperCase()}
                  </div>
                  {c.responses.map((r) => (
                    <div key={r.id} className="text-xs mt-1 text-ink/60">
                      Reply: “{r.raw_text}”
                      {r.red_flag && <span className="ml-1.5 text-risk-high font-semibold">RED FLAG</span>}
                      {r.meds_missed && !r.red_flag && <span className="ml-1.5 text-amber-700 font-semibold">MEDS MISSED</span>}
                    </div>
                  ))}
                </div>
                <span className={`text-[0.65rem] font-medium rounded-full px-2 py-0.5 ${CHECKIN_STATUS_STYLE[c.status] ?? ""}`}>
                  {c.status.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {(escalations.data?.length ?? 0) > 0 && (
        <Card>
          <SectionLabel>Escalations</SectionLabel>
          <div className="space-y-2">
            {escalations.data!.map((e) => (
              <div key={e.id} className="text-sm py-1.5 border-b border-hairline/60 last:border-0">
                <span className={`font-semibold uppercase text-xs mr-2 ${PRIORITY_STYLE[e.priority]}`}>
                  {e.priority}
                </span>
                <span className="text-ink/80">{e.detail}</span>
                <span className="ml-2 text-xs text-ink/40">({e.status.replace("_", " ")})</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {meta.data?.messaging_mode === "simulated" && (
        <SimulatedPhone patientId={patientId} checkins={checkins.data ?? []} />
      )}
    </div>
  );
}
