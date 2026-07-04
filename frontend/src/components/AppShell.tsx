import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { DemoBadge } from "@/components/core/DemoBadge";
import { PageFade } from "@/lib/appMotion";

const links = [
  { to: "/ward",               label: "Ward Risk View",      roles: ["admin", "physician", "resident", "nurse", "case_manager", "pharmacist", "analyst"] },
  { to: "/patients",           label: "Patients",            roles: ["admin", "physician", "resident", "nurse", "case_manager", "pharmacist"] },
  { to: "/dashboard/clinician",    label: "Clinician",           roles: ["physician", "resident", "nurse", "pharmacist"] },
  { to: "/dashboard/case-manager", label: "Case Manager",         roles: ["case_manager"] },
  { to: "/dashboard/admin",    label: "Admin",               roles: ["admin", "analyst"] },
  { to: "/model-lab",          label: "Model Lab",           roles: ["admin", "analyst"] },
];

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

export function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  if (!user) return null;

  const visibleLinks = links.filter(l => l.roles.includes(user.role));

  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="w-60 flex flex-col bg-paper border-r border-hairline shrink-0">
        <div className="px-6 py-5">
          <Link
            to="/"
            aria-label="careinsight — back to home"
            className="font-display text-lg font-bold tracking-tight text-ink hover:text-ink/60 transition-colors duration-150"
          >
            careinsight
          </Link>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          {visibleLinks.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                [
                  'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-sans transition-colors duration-150',
                  isActive
                    ? 'text-ink font-medium'
                    : 'text-ink/50 hover:text-ink hover:bg-tint',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`h-1.5 w-1.5 rounded-full shrink-0 transition-colors ${
                      isActive ? 'bg-ink' : 'bg-transparent'
                    }`}
                  />
                  {l.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-hairline">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-tint border border-hairline flex items-center justify-center text-[0.65rem] font-display font-bold text-ink shrink-0">
              {initials(user.full_name)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-ink truncate">{user.full_name}</div>
              <div className="text-[0.65rem] text-ink/40 capitalize">{user.role}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-2.5 text-xs text-ink/40 hover:text-ink transition-colors duration-150 underline underline-offset-2"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-paper p-8">
        <DemoBadge />
        <PageFade k={location.pathname}>
          <Outlet />
        </PageFade>
      </main>
    </div>
  );
}
