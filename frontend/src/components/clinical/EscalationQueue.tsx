import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Escalation } from "@/lib/api";
import { Card } from "@/components/core/Card";

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-red-50 text-red-700 border-red-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  low: "bg-slate-50 text-slate-600 border-slate-200",
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
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
        Escalation Queue — needs action today
      </div>
      {isLoading && <p className="text-sm text-slate-400">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-slate-500">No open escalations. All patients accounted for.</p>
      )}
      <div className="space-y-2">
        {data?.map((e) => {
          const waiting = daysWaiting(e.created_at);
          return (
            <div key={e.id} className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 transition-colors">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[0.65rem] font-semibold uppercase rounded-full border px-2 py-0.5 ${PRIORITY_BADGE[e.priority]}`}>
                      {e.priority}
                    </span>
                    {e.patient_name ? (
                      <button
                        className="text-sm font-medium text-slate-800 hover:text-brand-700 hover:underline"
                        onClick={() => e.patient_id && navigate(`/patients/${e.patient_id}`)}
                      >
                        {e.patient_name}
                      </button>
                    ) : (
                      <span className="text-sm font-medium text-slate-500 italic">Unmatched sender</span>
                    )}
                    <span className="text-xs text-slate-400">
                      {waiting === 0 ? "today" : `${waiting}d waiting`}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">{e.detail}</p>
                </div>
                <button
                  className="text-xs font-medium text-brand-600 hover:text-brand-700 underline shrink-0"
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
                    className="flex-1 border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:border-brand-600"
                    placeholder="Outcome notes — e.g. called patient, adjusted meds, PCP booked"
                    value={notes}
                    onChange={(ev) => setNotes(ev.target.value)}
                  />
                  <button
                    type="submit"
                    disabled={resolve.isPending || !notes.trim()}
                    className="text-xs font-medium bg-brand-600 text-white rounded-md px-3 py-1.5 hover:bg-brand-700 disabled:opacity-50"
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
