import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, Checkin } from "@/lib/api";

/** WhatsApp-styled demo panel: shows outbound check-ins, lets the demo
 * operator type the patient's reply. Rendered only in simulated mode. */
export function SimulatedPhone({ patientId, checkins }: { patientId: string; checkins: Checkin[] }) {
  const qc = useQueryClient();
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  const reply = useMutation({
    mutationFn: ({ checkinId, text }: { checkinId: string; text: string }) =>
      api.post(`/checkins/${checkinId}/simulate-reply`, { text }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["checkins", patientId] });
      qc.invalidateQueries({ queryKey: ["escalations", patientId] });
      qc.invalidateQueries({ queryKey: ["escalations", "open"] });
    },
  });

  const sent = checkins.filter((c) => c.status === "sent" || c.status === "responded");

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-emerald-700">
          Simulated patient phone — demo mode
        </span>
      </div>
      {sent.length === 0 && (
        <p className="text-xs text-slate-500">No check-ins sent yet. Messages appear here once dispatched.</p>
      )}
      <div className="space-y-3">
        {sent.map((c) => (
          <div key={c.id} className="space-y-2">
            <div className="max-w-[85%] rounded-lg rounded-tl-none bg-white border border-slate-200 p-2.5 text-xs text-slate-700 whitespace-pre-wrap">
              {c.sent_body}
            </div>
            {c.responses.map((r) => (
              <div key={r.id} className="max-w-[85%] ml-auto rounded-lg rounded-tr-none bg-emerald-100 border border-emerald-200 p-2.5 text-xs text-slate-800">
                {r.raw_text}
              </div>
            ))}
            {c.status === "sent" && (
              <form
                className="flex gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  const text = drafts[c.id]?.trim();
                  if (text) reply.mutate({ checkinId: c.id, text });
                }}
              >
                <input
                  className="flex-1 border border-slate-300 rounded-md px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:border-brand-600"
                  placeholder="Type the patient's reply…"
                  value={drafts[c.id] ?? ""}
                  onChange={(e) => setDrafts((d) => ({ ...d, [c.id]: e.target.value }))}
                />
                <button
                  type="submit"
                  disabled={reply.isPending}
                  className="text-xs font-medium bg-emerald-600 text-white rounded-md px-3 py-1.5 hover:bg-emerald-700 disabled:opacity-50"
                >
                  Reply
                </button>
              </form>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
