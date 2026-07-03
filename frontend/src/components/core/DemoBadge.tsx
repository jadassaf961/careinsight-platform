import { useQuery } from "@tanstack/react-query";
import { api, MetaResponse } from "@/lib/api";

/** Visible badge whenever messaging runs in simulated mode, so demo
 * messages can never be mistaken for real patient contact. */
export function DemoBadge() {
  const { data } = useQuery({
    queryKey: ["meta"],
    queryFn: () => api.get<MetaResponse>("/meta"),
    staleTime: Infinity,
  });
  if (data?.messaging_mode !== "simulated") return null;
  return (
    <div className="mb-4 flex justify-end">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-risk-low-border bg-risk-low-bg text-risk-low px-2.5 py-0.5 text-[0.65rem] font-display font-semibold uppercase tracking-wide">
        <span className="h-1.5 w-1.5 rounded-full bg-risk-low animate-pulse" />
        Demo mode — simulated messaging
      </span>
    </div>
  );
}
