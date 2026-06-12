import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const links = [
  { to: "/patients", label: "Patients", roles: ["admin", "physician", "resident", "nurse", "case_manager"] },
  { to: "/dashboard/clinician", label: "Clinician dashboard", roles: ["physician", "resident", "nurse"] },
  { to: "/dashboard/case-manager", label: "Case manager", roles: ["case_manager"] },
  { to: "/dashboard/admin", label: "Admin", roles: ["admin", "analyst"] },
];

export function AppShell() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-brand-700 text-brand-50 flex flex-col">
        <div className="px-5 py-4 border-b border-brand-600">
          <Link to="/patients" className="text-xl font-bold">CareInsight</Link>
          <div className="text-xs text-brand-100 mt-0.5">Platform</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {links
            .filter((l) => l.roles.includes(user.role))
            .map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-md text-sm ${
                    isActive ? "bg-brand-600 text-white" : "hover:bg-brand-600/60"
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
        </nav>
        <div className="p-3 border-t border-brand-600 text-sm">
          <div className="font-medium">{user.full_name}</div>
          <div className="text-brand-100 text-xs">{user.role}</div>
          <button onClick={logout} className="mt-2 text-xs underline">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
