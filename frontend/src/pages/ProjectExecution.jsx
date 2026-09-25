import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { listProjects } from "../services/projects";

const EXECUTION_STATUSES = ["Planned", "In Progress", "At Risk", "Blocked", "Completed"];

export default function ProjectExecution() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("");

  const filters = Object.fromEntries(Object.entries({ status }).filter(([, v]) => v));
  const { data, isLoading, isError } = useQuery({
    queryKey: ["projects", "execution", filters],
    queryFn: () => listProjects({ ...filters, per_page: 50 }),
  });

  const executionProjects = (data?.data || []).filter((p) => EXECUTION_STATUSES.includes(p.status));

  return (
    <>
      <PageHeader title="Project Execution" />
      <div className="content">
        <div className="filter-bar">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All execution statuses</option>
            {EXECUTION_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="card">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState />
          ) : executionProjects.length === 0 ? (
            <EmptyState title="No projects in execution" message="Projects appear here once scheduled on the roadmap." />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Project Manager</th>
                  <th>Status</th>
                  <th>Health</th>
                  <th>Target Date</th>
                </tr>
              </thead>
              <tbody>
                {executionProjects.map((p) => (
                  <tr key={p.id} onClick={() => navigate(`/projects/${p.id}`)}>
                    <td>{p.name}</td>
                    <td>{p.project_manager || "Unassigned"}</td>
                    <td>
                      <StatusChip value={p.status} />
                    </td>
                    <td>
                      <StatusChip value={p.health} />
                    </td>
                    <td className="muted">{p.target_date || "—"}</td>
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
