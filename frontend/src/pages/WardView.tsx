import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, BoardResponse, BoardRow } from "@/lib/api";
import { BoardGroup, groupForRow, todayIso } from "@/lib/board";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";

const GROUP_META: Record<BoardGroup, { title: string; accent: string }> = {
  blocked: {
    title: "Dischargeable today — blocked",
    accent: "border-l-2 border-l-risk-high",
  },
  on_track: {
    title: "On track",
    accent: "",
  },
  unplanned: {
    title: "No transition plan yet",
    accent: "",
  },
};

export function WardView() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const today = todayIso();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["transition-board"],
    queryFn: () => api.get<BoardResponse>("/transitions/board"),
  });

  const createPlan = useMutation({
    mutationFn: (admissionId: string) =>
      api.post("/transitions/plans", { admission_id: admissionId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transition-board"] }),
  });

  const rows = data?.rows ?? [];
  const grouped: Record<BoardGroup, BoardRow[]> = { blocked: [], on_track: [], unplanned: [] };
  for (const row of rows) grouped[groupForRow(row, today)].push(row);

  return (
    <div>
      <div className="mb-10">
        <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">
          Discharge <em className="font-serifit font-normal italic">readiness.</em>
        </h1>
        <p className="text-sm text-ink/50 mt-2">
          Every admitted patient, their readmission risk, and what's blocking discharge.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x md:divide-hairline border-y border-hairline py-6 mb-10 [&>*]:md:px-8 [&>*:first-child]:md:pl-0">
        <StatCard label="Blocked discharges" value={isLoading ? "—" : grouped.blocked.length} tone="risk" />
        <StatCard label="On track" value={isLoading ? "—" : grouped.on_track.length} tone="success" />
        <StatCard label="Awaiting planning" value={isLoading ? "—" : grouped.unplanned.length} />
      </div>

      {isError && (
        <div className="text-risk-high text-sm py-6">Failed to load the discharge board.</div>
      )}

      {(Object.keys(GROUP_META) as BoardGroup[]).map((group) => {
        const meta = GROUP_META[group];
        const groupRows = grouped[group];
        if (!isLoading && groupRows.length === 0) return null;
        return (
          <div key={group} className="mb-12">
            <div className="mb-3 flex items-baseline gap-3">
              <h2 className="font-display text-xl font-bold tracking-tight text-ink">{meta.title}</h2>
              <span className="font-serifit italic text-lg text-ink/40">
                {groupRows.length} patient{groupRows.length !== 1 ? "s" : ""}
              </span>
            </div>
            <div className={`bg-paper border-t border-hairline overflow-hidden ${meta.accent}`}>
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    {["Patient", "MRN", "Department", "Risk", "Target discharge", "Open tasks", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-3 font-display font-semibold text-ink/40 text-[0.6rem] uppercase tracking-[0.2em]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {groupRows.map((r) => (
                    <tr
                      key={r.admission_id}
                      className="group hover:bg-tint cursor-pointer transition-colors duration-100"
                      onClick={() => navigate(`/patients/${r.patient_id}`)}
                    >
                      <td className="px-4 py-3.5 font-sans font-medium text-ink">
                        {r.last_name}, {r.first_name}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-xs text-ink/50">{r.mrn}</td>
                      <td className="px-4 py-3.5 text-ink/60">{r.department}</td>
                      <td className="px-4 py-3.5">
                        {r.risk_tier ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="font-mono font-semibold text-ink">
                              {((r.probability ?? 0) * 100).toFixed(1)}%
                            </span>
                            <RiskBadge tier={r.risk_tier.toLowerCase() as "high" | "medium" | "low"} size="sm" />
                          </span>
                        ) : (
                          <span className="text-xs text-ink/40">No prediction</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-ink/60 text-xs">
                        {r.target_discharge_date ?? "—"}
                      </td>
                      <td className="px-4 py-3.5">
                        {r.plan_id ? (
                          r.open_tasks > 0 ? (
                            <span className="inline-flex items-center rounded-full bg-risk-medium-bg border border-risk-medium-border text-risk-medium px-2 py-0.5 text-xs">
                              {r.open_tasks} open · {r.open_task_roles.join(", ")}
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-risk-low-bg border border-risk-low-border text-risk-low px-2 py-0.5 text-xs">
                              All tasks done
                            </span>
                          )
                        ) : (
                          <button
                            className="text-xs font-medium text-ink underline underline-offset-2 hover:text-ink/60"
                            onClick={(e) => {
                              e.stopPropagation();
                              createPlan.mutate(r.admission_id);
                            }}
                            disabled={createPlan.isPending}
                          >
                            Start discharge planning
                          </button>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="text-ink/40 group-hover:text-ink text-xs font-medium transition-colors">
                          View chart →
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      {isLoading && <div className="text-ink/40 text-sm py-6">Loading board…</div>}
      {!isLoading && rows.length === 0 && !isError && (
        <div className="text-ink/40 text-sm py-6">No active admissions.</div>
      )}
    </div>
  );
}
