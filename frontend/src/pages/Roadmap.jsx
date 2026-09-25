import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { getRoadmap } from "../services/roadmap";
import { listBusinessFunctions, listUsers } from "../services/lookups";

const QUARTERS = ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"];

export default function Roadmap() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ business_function_id: "", project_manager_id: "" });

  const { data: businessFunctions } = useQuery({ queryKey: ["business-functions"], queryFn: listBusinessFunctions });
  const { data: pms } = useQuery({ queryKey: ["users", "project_manager"], queryFn: () => listUsers("project_manager") });

  const cleanFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const { data, isLoading, isError } = useQuery({ queryKey: ["roadmap", cleanFilters], queryFn: () => getRoadmap(cleanFilters) });

  return (
    <>
      <PageHeader title="Roadmap" />
      <div className="content">
        <div className="filter-bar">
          <select value={filters.business_function_id} onChange={(e) => setFilters((f) => ({ ...f, business_function_id: e.target.value }))}>
            <option value="">All business functions</option>
            {businessFunctions?.map((bf) => (
              <option key={bf.id} value={bf.id}>
                {bf.name}
              </option>
            ))}
          </select>
          <select value={filters.project_manager_id} onChange={(e) => setFilters((f) => ({ ...f, project_manager_id: e.target.value }))}>
            <option value="">All project managers</option>
            {pms?.map((pm) => (
              <option key={pm.id} value={pm.id}>
                {pm.name}
              </option>
            ))}
          </select>
        </div>

        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState />
        ) : data.length === 0 ? (
          <EmptyState title="Nothing on the roadmap yet" message="Schedule a portfolio project from the Portfolio Workspace." />
        ) : (
          <div className="roadmap-grid">
            {QUARTERS.map((quarter) => {
              const items = data.filter((item) => item.quarter === quarter).sort((a, b) => a.sequence - b.sequence);
              return (
                <div key={quarter} className="roadmap-column">
                  <h3>{quarter}</h3>
                  {items.length === 0 ? (
                    <p className="muted" style={{ fontSize: 12 }}>Nothing scheduled.</p>
                  ) : (
                    items.map((item) => (
                      <div key={item.id} className="roadmap-item" onClick={() => navigate(`/projects/${item.project_id}`)}>
                        <strong>{item.project_name}</strong>
                        <div className="muted" style={{ fontSize: 12 }}>{item.planned_start} → {item.planned_end}</div>
                        <div style={{ marginTop: 4 }}>
                          <StatusChip value={item.status} />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}
