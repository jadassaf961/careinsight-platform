import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth/AuthContext";
import { RequireAuth } from "@/auth/RequireAuth";
import { AppShell } from "@/components/AppShell";
import { Login } from "@/pages/Login";
import { PatientSearch } from "@/pages/PatientSearch";
import { PatientChart } from "@/pages/PatientChart";
import { ClinicianDashboard } from "@/pages/ClinicianDashboard";
import { CaseManagerDashboard } from "@/pages/CaseManagerDashboard";
import { AdminDashboard } from "@/pages/AdminDashboard";
import { ModelLab } from "@/pages/ModelLab";
import { WardView } from "@/pages/WardView";

const Landing = lazy(() => import("@/pages/Landing"));

function PublicHome() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/ward" replace />;
  return (
    <Suspense fallback={null}>
      <Landing />
    </Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<PublicHome />} />
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route path="/patients" element={<PatientSearch />} />
          <Route path="/patients/:id" element={<PatientChart />} />
          <Route path="/dashboard/clinician" element={<ClinicianDashboard />} />
          <Route path="/dashboard/case-manager" element={<CaseManagerDashboard />} />
          <Route path="/dashboard/admin" element={<AdminDashboard />} />
          <Route path="/model-lab" element={<ModelLab />} />
          <Route path="/ward" element={<WardView />} />
        </Route>
        <Route path="*" element={<Navigate to="/ward" replace />} />
      </Routes>
    </AuthProvider>
  );
}
