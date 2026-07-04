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
    <div className="rounded-xl border border-risk-low-border bg-risk-low-bg/40 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="h-2 w-2 rounded-full bg-risk-low" />
        <span className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-risk-low">
          Simulated patient phone — demo mode
        </span>
      </div>
      {sent.length === 0 && (
        <p className="text-xs text-ink/50">No check-ins sent yet. Messages appear here once dispatched.</p>
      )}
      <div className="space-y-3">
        {sent.map((c) => (
          <div key={c.id} className="space-y-2">
            <div className="max-w-[85%] rounded-lg rounded-tl-none bg-paper border border-hairline p-2.5 text-xs text-ink/80 whitespace-pre-wrap">
              {c.sent_body}
            </div>
            {c.responses.map((r) => (
              <div key={r.id} className="max-w-[85%] ml-auto rounded-lg rounded-tr-none bg-risk-low-bg border border-risk-low-border p-2.5 text-xs text-ink">
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
                  className="flex-1 border-0 border-b border-hairline rounded-none px-0 py-1.5 text-xs bg-transparent focus:outline-none focus:border-ink placeholder:text-ink/30"
                  placeholder="Type the patient's reply…"
                  value={drafts[c.id] ?? ""}
                  onChange={(e) => setDrafts((d) => ({ ...d, [c.id]: e.target.value }))}
                />
                <button
                  type="submit"
                  disabled={reply.isPending}
                  className="text-xs font-display font-semibold lowercase bg-risk-low text-white rounded-full px-3.5 py-1.5 hover:opacity-90 disabled:opacity-50"
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
