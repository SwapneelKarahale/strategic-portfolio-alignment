import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { listProjects } from "../services/projects";

export default function PortfolioWorkspace() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("Portfolio");
  const [search, setSearch] = useState("");

  const filters = Object.fromEntries(Object.entries({ status, search }).filter(([, v]) => v));
  const { data, isLoading, isError } = useQuery({
    queryKey: ["projects", "portfolio", filters],
    queryFn: () => listProjects({ ...filters, per_page: 25 }),
  });

  return (
    <>
      <PageHeader title="Portfolio Workspace" />
      <div className="content">
        <p className="muted" style={{ marginBottom: 16, fontSize: 14 }}>
          Enrich approved demands into portfolio-ready projects: add requirements, assign required capabilities and a
          project manager, then schedule them on the roadmap.
        </p>
        <div className="filter-bar">
          <input placeholder="Search by project name…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="Portfolio">Not yet scheduled (Portfolio)</option>
            <option value="">All statuses</option>
            <option value="Planned">Planned</option>
            <option value="In Progress">In Progress</option>
          </select>
        </div>

        <div className="card">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState />
          ) : data.data.length === 0 ? (
            <EmptyState title="No projects here" message="Approved demands appear here once converted to a project." />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Business Function</th>
                  <th>Project Manager</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>On Roadmap</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((p) => (
                  <tr key={p.id} onClick={() => navigate(`/projects/${p.id}`)}>
                    <td>{p.name}</td>
                    <td>{p.business_function || "—"}</td>
                    <td>{p.project_manager || "Unassigned"}</td>
                    <td>{p.priority}</td>
                    <td>
                      <StatusChip value={p.status} />
                    </td>
                    <td>{p.on_roadmap ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
