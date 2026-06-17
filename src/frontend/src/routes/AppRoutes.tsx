import { Navigate, Route, Routes } from "react-router-dom";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { BlacklistCandidatePage } from "../pages/BlacklistCandidatePage";
import { DashboardPage } from "../pages/DashboardPage";
import { EarlyWarningPage } from "../pages/EarlyWarningPage";
import { EntitiesPage } from "../pages/EntitiesPage";
import { GraphExplorerPage } from "../pages/GraphExplorerPage";
import { ReportIntakePage } from "../pages/ReportIntakePage";
import { VerificationCasesPage } from "../pages/VerificationCasesPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/report-intake" element={<ReportIntakePage />} />
        <Route path="/graph-explorer" element={<GraphExplorerPage />} />
        <Route path="/entities" element={<EntitiesPage />} />
        <Route path="/early-warning" element={<EarlyWarningPage />} />
        <Route path="/verification-cases" element={<VerificationCasesPage />} />
        <Route path="/blacklist-candidate" element={<BlacklistCandidatePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
