import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";

const TIER_BADGE: Record<string, string> = {
  High: "bg-red-100 text-red-800 border border-red-200",
  Medium: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  Low: "bg-green-100 text-green-800 border border-green-200",
};

export function WardView() {
  const navigate = useNavigate();
  const [deptFilter, setDeptFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("");

  const params = new URLSearchParams();
  if (deptFilter) params.set("department", deptFilter);
  if (tierFilter) params.set("risk_tier", tierFilter);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["population", deptFilter, tierFilter],
    queryFn: () =>
      api.get<PopulationResponse>(`/dashboard/population?${params.toString()}`),
  });

  const allDepartments = [
    ...new Set(
      data?.patients
        ? [...data.patients.map((p) => p.department)]
        : []
    ),
  ].sort();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Ward Risk View</h1>
        <p className="text-sm text-slate-500 mt-1">
          All admitted patients ranked by 30-day readmission risk — highest risk first.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card border-l-4 border-red-500">
          <div className="text-xs uppercase tracking-wide text-slate-500">High Risk</div>
          <div className="text-3xl font-bold text-red-600 mt-1">
            {data?.high_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Require immediate attention</div>
        </div>
        <div className="card border-l-4 border-yellow-400">
          <div className="text-xs uppercase tracking-wide text-slate-500">Medium Risk</div>
          <div className="text-3xl font-bold text-yellow-600 mt-1">
            {data?.medium_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Monitor before discharge</div>
        </div>
        <div className="card border-l-4 border-green-500">
          <div className="text-xs uppercase tracking-wide text-slate-500">Low Risk</div>
          <div className="text-3xl font-bold text-green-600 mt-1">
            {data?.low_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Standard discharge protocol</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={deptFilter}
          onChange={(e) => setDeptFilter(e.target.value)}
        >
          <option value="">All departments</option>
          {allDepartments.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
        >
          <option value="">All risk tiers</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        {(deptFilter || tierFilter) && (
          <button
            className="text-sm text-slate-500 underline"
            onClick={() => {
              setDeptFilter("");
              setTierFilter("");
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Patient</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">MRN</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Department</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Risk Score</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Tier</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Top Risk Factor</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400">
                  Loading patients…
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-red-500">
                  Failed to load ward data.
                </td>
              </tr>
            )}
            {!isLoading && !isError && data?.patients.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400">
                  No patients match the current filters.
                </td>
              </tr>
            )}
            {data?.patients.map((p) => (
              <tr
                key={p.patient_id}
                className="hover:bg-slate-50 cursor-pointer"
                onClick={() => navigate(`/patients/${p.patient_id}`)}
              >
                <td className="px-4 py-3 font-medium">
                  {p.first_name} {p.last_name}
                </td>
                <td className="px-4 py-3 text-slate-500 font-mono text-xs">{p.mrn}</td>
                <td className="px-4 py-3 text-slate-600">{p.department}</td>
                <td className="px-4 py-3 font-mono font-semibold">
                  {(p.probability * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      TIER_BADGE[p.risk_tier] ?? ""
                    }`}
                  >
                    {p.risk_tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {p.top_factor ?? "—"}
                </td>
                <td className="px-4 py-3">
                  <span className="text-brand-700 hover:underline text-xs">
                    View chart →
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <div className="px-4 py-2 border-t bg-slate-50 text-xs text-slate-400">
            {data.total} admitted patients with predictions
          </div>
        )}
      </div>
    </div>
  );
}
