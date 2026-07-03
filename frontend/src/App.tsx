import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/auth/AuthContext";
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

export default function App() {
  return (
    <AuthProvider>
      <Routes>
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
          <Route index element={<Navigate to="/ward" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/ward" replace />} />
      </Routes>
    </AuthProvider>
  );
}
