import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import DemandList from "./pages/DemandList";
import NewDemand from "./pages/NewDemand";
import DemandDetail from "./pages/DemandDetail";
import PortfolioWorkspace from "./pages/PortfolioWorkspace";
import Roadmap from "./pages/Roadmap";
import ProjectExecution from "./pages/ProjectExecution";
import ProjectDetail from "./pages/ProjectDetail";
import AuditHistory from "./pages/AuditHistory";
import AdminUsers from "./pages/AdminUsers";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/demands" element={<DemandList />} />
        <Route
          path="/demands/new"
          element={
            <ProtectedRoute roles={["requestor", "project_manager", "admin"]}>
              <NewDemand />
            </ProtectedRoute>
          }
        />
        <Route path="/demands/:id" element={<DemandDetail />} />
        <Route
          path="/portfolio"
          element={
            <ProtectedRoute roles={["project_manager", "management", "admin"]}>
              <PortfolioWorkspace />
            </ProtectedRoute>
          }
        />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route
          path="/execution"
          element={
            <ProtectedRoute roles={["project_manager", "management", "admin"]}>
              <ProjectExecution />
            </ProtectedRoute>
          }
        />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route
          path="/audit"
          element={
            <ProtectedRoute roles={["project_manager", "management", "admin"]}>
              <AuditHistory />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminUsers />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
