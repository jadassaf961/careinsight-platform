import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { DemoBadge } from "@/components/core/DemoBadge";

const links = [
  { to: "/ward",               label: "Ward Risk View",      roles: ["admin", "physician", "resident", "nurse", "case_manager", "analyst"] },
  { to: "/patients",           label: "Patients",            roles: ["admin", "physician", "resident", "nurse", "case_manager"] },
  { to: "/dashboard/clinician",    label: "Clinician",           roles: ["physician", "resident", "nurse"] },
  { to: "/dashboard/case-manager", label: "Case Manager",         roles: ["case_manager"] },
  { to: "/dashboard/admin",    label: "Admin",               roles: ["admin", "analyst"] },
  { to: "/model-lab",          label: "Model Lab",           roles: ["admin", "analyst"] },
];

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

export function AppShell() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const visibleLinks = links.filter(l => l.roles.includes(user.role));

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 flex flex-col bg-gradient-to-b from-brand-700 to-brand-800 text-white shrink-0">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-white/10">
          <img src="/logo-white.svg" alt="CareInsight" className="h-7 w-auto" />
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {visibleLinks.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                [
                  'block px-3 py-2 rounded-md text-sm font-sans transition-colors duration-150',
                  isActive
                    ? 'bg-white/15 text-white font-medium'
                    : 'text-white/75 hover:bg-white/10 hover:text-white',
                ].join(' ')
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-3 border-t border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-brand-500/40 flex items-center justify-center text-[0.65rem] font-bold text-white shrink-0">
              {initials(user.full_name)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-white truncate">{user.full_name}</div>
              <div className="text-[0.65rem] text-white/50 capitalize">{user.role}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-2.5 text-xs text-white/50 hover:text-white transition-colors duration-150 underline underline-offset-2"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <DemoBadge />
        <Outlet />
      </main>
    </div>
  );
}
