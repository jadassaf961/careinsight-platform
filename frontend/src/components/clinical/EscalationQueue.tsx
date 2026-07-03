import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Escalation } from "@/lib/api";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-risk-high-bg text-risk-high border-risk-high-border",
  medium: "bg-risk-medium-bg text-risk-medium border-risk-medium-border",
  low: "bg-tint text-ink/60 border-hairline",
};

function daysWaiting(createdAt: string): number {
  return Math.floor((Date.now() - new Date(createdAt).getTime()) / 86_400_000);
}

export function EscalationQueue() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [resolving, setResolving] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["escalations", "open"],
    queryFn: () => api.get<Escalation[]>("/escalations?status=open"),
    refetchInterval: 30_000,
  });

  const resolve = useMutation({
    mutationFn: ({ id, resolution_notes }: { id: string; resolution_notes: string }) =>
      api.patch(`/escalations/${id}`, { status: "resolved", resolution_notes }),
    onSuccess: () => {
      setResolving(null);
      setNotes("");
      qc.invalidateQueries({ queryKey: ["escalations"] });
    },
  });

  return (
    <Card>
      <SectionLabel>Escalation Queue — needs action today</SectionLabel>
      {isLoading && <p className="text-sm text-ink/40">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-ink/50">No open escalations. All patients accounted for.</p>
      )}
      <div className="space-y-2">
        {data?.map((e) => {
          const waiting = daysWaiting(e.created_at);
          return (
            <div key={e.id} className="py-3 border-b border-hairline last:border-0 transition-colors">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[0.65rem] font-semibold uppercase rounded-full border px-2 py-0.5 ${PRIORITY_BADGE[e.priority]}`}>
                      {e.priority}
                    </span>
                    {e.patient_name ? (
                      <button
                        className="font-display text-sm font-semibold tracking-tight text-ink hover:underline underline-offset-2"
                        onClick={() => e.patient_id && navigate(`/patients/${e.patient_id}`)}
                      >
                        {e.patient_name}
                      </button>
                    ) : (
                      <span className="text-sm font-medium text-ink/50 italic">Unmatched sender</span>
                    )}
                    <span className="text-xs text-ink/40">
                      {waiting === 0 ? "today" : `${waiting}d waiting`}
                    </span>
                  </div>
                  <p className="text-sm text-ink/60 mt-1">{e.detail}</p>
                </div>
                <button
                  className="text-xs font-medium text-ink underline underline-offset-2 hover:text-ink/60 shrink-0"
                  onClick={() => setResolving(resolving === e.id ? null : e.id)}
                >
                  {resolving === e.id ? "Cancel" : "Resolve"}
                </button>
              </div>
              {resolving === e.id && (
                <form
                  className="mt-2 flex gap-2"
                  onSubmit={(ev) => {
                    ev.preventDefault();
                    if (notes.trim()) resolve.mutate({ id: e.id, resolution_notes: notes.trim() });
                  }}
                >
                  <input
                    autoFocus
                    className="flex-1 border-0 border-b border-hairline rounded-none px-0 py-1.5 text-xs bg-transparent focus:outline-none focus:border-ink placeholder:text-ink/30"
                    placeholder="Outcome notes — e.g. called patient, adjusted meds, PCP booked"
                    value={notes}
                    onChange={(ev) => setNotes(ev.target.value)}
                  />
                  <button
                    type="submit"
                    disabled={resolve.isPending || !notes.trim()}
                    className="text-xs font-display font-semibold lowercase bg-ink text-paper rounded-full px-3.5 py-1.5 hover:bg-ink/85 disabled:opacity-50"
                  >
                    Mark resolved
                  </button>
                </form>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
