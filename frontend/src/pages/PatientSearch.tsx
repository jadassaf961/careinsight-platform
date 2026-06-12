import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, PatientList } from "@/lib/api";

export function PatientSearch() {
  const [q, setQ] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["patients", q],
    queryFn: () => api.get<PatientList>(`/patients?q=${encodeURIComponent(q)}`),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Patients</h1>
        <input
          type="search" placeholder="Search MRN or name…"
          value={q} onChange={(e) => setQ(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-md w-72
                     focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">MRN</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">DOB</th>
              <th className="px-4 py-3">Sex</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={5} className="p-8 text-center text-slate-500">Loading…</td></tr>
            )}
            {!isLoading && data?.items.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-slate-500">
                No patients found.
              </td></tr>
            )}
            {data?.items.map((p) => (
              <tr key={p.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs">{p.mrn}</td>
                <td className="px-4 py-3 font-medium">{p.last_name}, {p.first_name}</td>
                <td className="px-4 py-3 text-slate-600">{p.dob}</td>
                <td className="px-4 py-3 text-slate-600">{p.sex}</td>
                <td className="px-4 py-3 text-right">
                  <Link to={`/patients/${p.id}`} className="text-brand-600 hover:underline">
                    Open chart →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && (
        <div className="mt-3 text-xs text-slate-500">
          Showing {data.items.length} of {data.total}
        </div>
      )}
    </div>
  );
}
