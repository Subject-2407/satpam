import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { ProtectedRoute } from "./ProtectedRoute";
import { LoadingState } from "../components/States";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ReportIntakePage } from "../pages/ReportIntakePage";
import { EntitiesPage } from "../pages/EntitiesPage";
import { EntityDetailPage } from "../pages/EntityDetailPage";
import { EarlyWarningPage } from "../pages/EarlyWarningPage";
import { VerificationCasesPage } from "../pages/VerificationCasesPage";
import { BlacklistCandidatePage } from "../pages/BlacklistCandidatePage";
import { TrafficIntelPage } from "../pages/TrafficIntelPage";
import { AuditLogPage } from "../pages/AuditLogPage";
import { RulesPage } from "../pages/RulesPage";

// Graph Explorer memuat Cytoscape (besar) — di-split agar tidak membebani bundle awal.
const GraphExplorerPage = lazy(() =>
  import("../pages/GraphExplorerPage").then((m) => ({ default: m.GraphExplorerPage })),
);

// Public reporter tidak punya akses dashboard; arahkan ke report intake.
function HomeRoute() {
  const { user } = useAuth();
  if (user?.role === "public_reporter") return <Navigate to="/report-intake" replace />;
  return (
    <ProtectedRoute minRole="analyst">
      <DashboardPage />
    </ProtectedRoute>
  );
}

export function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />

      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<HomeRoute />} />
        <Route path="/report-intake" element={<ReportIntakePage />} />
        <Route
          path="/graph-explorer"
          element={
            <ProtectedRoute minRole="analyst">
              <Suspense fallback={<LoadingState label="Memuat Graph Explorer…" />}>
                <GraphExplorerPage />
              </Suspense>
            </ProtectedRoute>
          }
        />
        <Route
          path="/entities"
          element={
            <ProtectedRoute minRole="analyst">
              <EntitiesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/entities/:nodeType/:nodeId"
          element={
            <ProtectedRoute minRole="analyst">
              <EntityDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/early-warning"
          element={
            <ProtectedRoute minRole="analyst">
              <EarlyWarningPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/verification-cases"
          element={
            <ProtectedRoute minRole="analyst">
              <VerificationCasesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blacklist-candidate"
          element={
            <ProtectedRoute minRole="analyst">
              <BlacklistCandidatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/traffic-intel"
          element={
            <ProtectedRoute minRole="analyst">
              <TrafficIntelPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit-logs"
          element={
            <ProtectedRoute minRole="supervisor">
              <AuditLogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rules"
          element={
            <ProtectedRoute minRole="admin">
              <RulesPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
