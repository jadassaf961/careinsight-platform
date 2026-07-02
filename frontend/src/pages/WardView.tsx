import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";

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

  const allDepartments = data?.departments ?? [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-navy-700">Ward Risk View</h1>
        <p className="text-sm text-slate-500 mt-1">
          All admitted patients ranked by 30-day readmission risk — highest risk first.
        </p>
      </div>

      {/* Summary stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard
          label="High Risk"
          value={data?.high_count ?? "—"}
          tone="risk"
        />
        <StatCard
          label="Medium Risk"
          value={data?.medium_count ?? "—"}
          tone="default"
        />
        <StatCard
          label="Low Risk"
          value={data?.low_count ?? "—"}
          tone="success"
        />
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select
          className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white font-sans focus:outline-none focus:shadow-focus focus:border-brand-600"
          value={deptFilter}
          onChange={(e) => setDeptFilter(e.target.value)}
        >
          <option value="">All departments</option>
          {allDepartments.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select
          className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white font-sans focus:outline-none focus:shadow-focus focus:border-brand-600"
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
            className="text-sm text-slate-500 hover:text-slate-700 underline transition-colors"
            onClick={() => { setDeptFilter(""); setTierFilter(""); }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Patient table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Patient</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">MRN</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Department</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Risk Score</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Tier</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Top Risk Factor</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400 text-sm">
                  Loading patients…
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-risk-high text-sm">
                  Failed to load ward data.
                </td>
              </tr>
            )}
            {!isLoading && !isError && data?.patients.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400 text-sm">
                  No patients match the current filters.
                </td>
              </tr>
            )}
            {data?.patients.map((p) => (
              <tr
                key={p.patient_id}
                className="hover:bg-slate-50 cursor-pointer transition-colors duration-100"
                onClick={() => navigate(`/patients/${p.patient_id}`)}
              >
                <td className="px-4 py-3 font-sans font-medium text-slate-800">
                  {p.last_name}, {p.first_name}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{p.mrn}</td>
                <td className="px-4 py-3 text-slate-600">{p.department}</td>
                <td className="px-4 py-3 font-mono font-semibold text-slate-800">
                  {(p.probability * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3">
                  <RiskBadge
                    tier={p.risk_tier.toLowerCase() as 'high' | 'medium' | 'low'}
                    size="sm"
                  />
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs max-w-[200px] truncate">
                  {p.top_factor ?? "—"}
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
        {data && (
          <div className="px-4 py-2 border-t border-slate-100 bg-slate-50 text-xs text-slate-400">
            {data.total} admitted patient{data.total !== 1 ? 's' : ''} with predictions
          </div>
        )}
      </div>
    </div>
  );
}
