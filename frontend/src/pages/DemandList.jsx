import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { listDemands } from "../services/demands";
import { listBusinessFunctions } from "../services/lookups";
import { useAuth } from "../context/AuthContext";

const STATUSES = ["Draft", "Submitted", "Under Review", "Clarification Required", "Validated", "Approved", "Rejected"];

export default function DemandList() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ status: "", business_function_id: "", search: "" });

  const { data: businessFunctions } = useQuery({ queryKey: ["business-functions"], queryFn: listBusinessFunctions });

  const cleanFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const { data, isLoading, isError } = useQuery({
    queryKey: ["demands", cleanFilters, page],
    queryFn: () => listDemands({ ...cleanFilters, page, per_page: 15 }),
  });

  const canCreate = ["requestor", "project_manager", "admin"].includes(user?.role);

  return (
    <>
      <PageHeader
        title="Demands"
        actions={
          canCreate && (
            <button className="btn btn-primary" onClick={() => navigate("/demands/new")}>
              + New Demand
            </button>
          )
        }
      />
      <div className="content">
        <div className="filter-bar">
          <input
            placeholder="Search by title…"
            value={filters.search}
            onChange={(e) => {
              setPage(1);
              setFilters((f) => ({ ...f, search: e.target.value }));
            }}
          />
          <select
            value={filters.status}
            onChange={(e) => {
              setPage(1);
              setFilters((f) => ({ ...f, status: e.target.value }));
            }}
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            value={filters.business_function_id}
            onChange={(e) => {
              setPage(1);
              setFilters((f) => ({ ...f, business_function_id: e.target.value }));
            }}
          >
            <option value="">All business functions</option>
            {businessFunctions?.map((bf) => (
              <option key={bf.id} value={bf.id}>
                {bf.name}
              </option>
            ))}
          </select>
        </div>

        <div className="card">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState />
          ) : data.data.length === 0 ? (
            <EmptyState title="No demands match these filters" />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Business Function</th>
                  <th>Requestor</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((d) => (
                  <tr key={d.id} onClick={() => navigate(`/demands/${d.id}`)}>
                    <td>{d.title}</td>
                    <td>{d.business_function}</td>
                    <td>{d.requestor}</td>
                    <td>{d.priority}</td>
                    <td>
                      <StatusChip value={d.status} />
                    </td>
                    <td className="muted">{d.created_at ? new Date(d.created_at).toLocaleDateString() : "—"}</td>
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
