import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { listAuditLogs } from "../services/audit";

export default function AuditHistory() {
  const [page, setPage] = useState(1);
  const [resourceType, setResourceType] = useState("");

  const filters = Object.fromEntries(Object.entries({ resource_type: resourceType }).filter(([, v]) => v));
  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-logs", filters, page],
    queryFn: () => listAuditLogs({ ...filters, page, per_page: 30 }),
  });

  return (
    <>
      <PageHeader title="Audit History" />
      <div className="content">
        <div className="filter-bar">
          <select value={resourceType} onChange={(e) => { setPage(1); setResourceType(e.target.value); }}>
            <option value="">All resource types</option>
            <option value="demand">Demands</option>
            <option value="project">Projects</option>
          </select>
        </div>

        <div className="card">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState />
          ) : data.data.length === 0 ? (
            <EmptyState title="No audit entries yet" />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((log) => (
                  <tr key={log.id} style={{ cursor: "default" }}>
                    <td className="muted">{new Date(log.timestamp).toLocaleString()}</td>
                    <td>{log.user}</td>
                    <td>{log.action}</td>
                    <td>
                      {log.resource_type} #{log.resource_id}
                    </td>
                    <td className="muted">
                      {log.old_value && log.new_value ? `${log.old_value} → ${log.new_value}` : log.new_value || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {data && data.meta.pages > 1 && (
          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span className="muted" style={{ alignSelf: "center", fontSize: 13 }}>
              Page {data.meta.page} of {data.meta.pages}
            </span>
            <button className="btn btn-secondary btn-sm" disabled={page >= data.meta.pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        )}
      </div>
    </>
  );
}
