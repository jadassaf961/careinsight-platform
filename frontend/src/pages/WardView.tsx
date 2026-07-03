import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, BoardResponse, BoardRow } from "@/lib/api";
import { BoardGroup, groupForRow, todayIso } from "@/lib/board";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";

const GROUP_META: Record<BoardGroup, { title: string; blurb: string; accent: string }> = {
  blocked: {
    title: "Dischargeable today — blocked",
    blurb: "Target discharge date reached but tasks remain open.",
    accent: "border-l-4 border-risk-high",
  },
  on_track: {
    title: "On track",
    blurb: "Transition plan in progress.",
    accent: "border-l-4 border-brand-600",
  },
  unplanned: {
    title: "No transition plan yet",
    blurb: "Start discharge planning to generate the task checklist.",
    accent: "border-l-4 border-slate-300",
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
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-navy-700">
          Discharge Readiness Board
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Every admitted patient, their readmission risk, and what's blocking discharge.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard label="Blocked discharges" value={isLoading ? "—" : grouped.blocked.length} tone="risk" />
        <StatCard label="On track" value={isLoading ? "—" : grouped.on_track.length} tone="success" />
        <StatCard label="Awaiting planning" value={isLoading ? "—" : grouped.unplanned.length} tone="default" />
      </div>

      {isError && (
        <div className="text-risk-high text-sm py-6">Failed to load the discharge board.</div>
      )}

      {(Object.keys(GROUP_META) as BoardGroup[]).map((group) => {
        const meta = GROUP_META[group];
        const groupRows = grouped[group];
        if (!isLoading && groupRows.length === 0) return null;
        return (
          <div key={group} className="mb-6">
            <div className="mb-2">
              <h2 className="font-display text-sm font-semibold text-navy-700">{meta.title}</h2>
              <p className="text-xs text-slate-400">{meta.blurb}</p>
            </div>
            <div className={`bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden ${meta.accent}`}>
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    {["Patient", "MRN", "Department", "Risk", "Target discharge", "Open tasks", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-2.5 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {groupRows.map((r) => (
                    <tr
                      key={r.admission_id}
                      className="hover:bg-slate-50 cursor-pointer transition-colors duration-100"
                      onClick={() => navigate(`/patients/${r.patient_id}`)}
                    >
                      <td className="px-4 py-3 font-sans font-medium text-slate-800">
                        {r.last_name}, {r.first_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{r.mrn}</td>
                      <td className="px-4 py-3 text-slate-600">{r.department}</td>
                      <td className="px-4 py-3">
                        {r.risk_tier ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="font-mono font-semibold text-slate-800">
                              {((r.probability ?? 0) * 100).toFixed(1)}%
                            </span>
                            <RiskBadge tier={r.risk_tier.toLowerCase() as "high" | "medium" | "low"} size="sm" />
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">No prediction</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {r.target_discharge_date ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {r.plan_id ? (
                          r.open_tasks > 0 ? (
                            <span className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 text-amber-800 px-2 py-0.5 text-xs">
                              {r.open_tasks} open · {r.open_task_roles.join(", ")}
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-green-50 border border-green-200 text-green-700 px-2 py-0.5 text-xs">
                              All tasks done
                            </span>
                          )
                        ) : (
                          <button
                            className="text-xs font-medium text-brand-600 hover:text-brand-700 underline"
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
                      <td className="px-4 py-3 text-right">
                        <span className="text-brand-600 hover:text-brand-700 text-xs font-medium">
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

      {isLoading && <div className="text-slate-400 text-sm py-6">Loading board…</div>}
      {!isLoading && rows.length === 0 && !isError && (
        <div className="text-slate-400 text-sm py-6">No active admissions.</div>
      )}
    </div>
  );
}
