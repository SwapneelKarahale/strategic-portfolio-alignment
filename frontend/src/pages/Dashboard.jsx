import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import PageHeader from "../components/PageHeader";
import KpiCard from "../components/KpiCard";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { getAnalytics, getSummary } from "../services/dashboard";
import { listBusinessFunctions, listUsers } from "../services/lookups";
import { listDemands } from "../services/demands";

const FUNNEL_COLORS = ["#8a90c8", "#5a68e8", "#2f3a8f", "#1a8f7b", "#b8791a", "#c2452f"];

export default function Dashboard() {
  const [filters, setFilters] = useState({ business_function_id: "", project_manager_id: "", priority: "" });

  const { data: businessFunctions } = useQuery({ queryKey: ["business-functions"], queryFn: listBusinessFunctions });
  const { data: pms } = useQuery({ queryKey: ["users", "project_manager"], queryFn: () => listUsers("project_manager") });

  const cleanFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));

  const summaryQuery = useQuery({ queryKey: ["dashboard-summary", cleanFilters], queryFn: () => getSummary(cleanFilters) });
  const analyticsQuery = useQuery({ queryKey: ["dashboard-analytics", cleanFilters], queryFn: () => getAnalytics(cleanFilters) });
  const recentQuery = useQuery({
    queryKey: ["recent-demands"],
    queryFn: () => listDemands({ per_page: 5 }),
  });

  if (summaryQuery.isLoading || analyticsQuery.isLoading) return <LoadingState label="Loading dashboard…" />;
  if (summaryQuery.isError || analyticsQuery.isError) return <ErrorState message="Could not load dashboard data." />;

  const summary = summaryQuery.data;
  const analytics = analyticsQuery.data;

  const funnelData = [
    { label: "Demand", value: summary.total_demands },
    { label: "Portfolio", value: summary.portfolio },
    { label: "Roadmap", value: summary.roadmap },
    { label: "Execution", value: summary.execution },
    { label: "At Risk", value: summary.at_risk },
    { label: "Completed", value: summary.completed },
  ];

  return (
    <>
      <PageHeader title="Management Dashboard" />
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
          <select value={filters.priority} onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}>
            <option value="">All priorities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div className="kpi-grid">
          <KpiCard label="Total Demands" value={summary.total_demands} />
          <KpiCard label="Under Review" value={summary.under_review} tone="info" />
          <KpiCard label="Portfolio" value={summary.portfolio} tone="primary" />
          <KpiCard label="Roadmap" value={summary.roadmap} tone="primary" />
          <KpiCard label="Execution" value={summary.execution} tone="primary" />
          <KpiCard label="At Risk" value={summary.at_risk} tone="warning" />
          <KpiCard label="Completed" value={summary.completed} tone="success" />
        </div>

        <div className="grid-2">
          <div className="stack">
            <div className="card card-pad">
              <p className="section-title">Funnel: Demand → Portfolio → Roadmap → Execution</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {funnelData.map((_, i) => (
                      <Cell key={i} fill={FUNNEL_COLORS[i % FUNNEL_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid-2">
              <div className="card card-pad">
                <p className="section-title">Projects by Business Function</p>
                {analytics.by_business_function.length === 0 ? (
                  <EmptyState title="No portfolio projects yet" />
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={analytics.by_business_function} layout="vertical">
                      <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                      <YAxis type="category" dataKey="label" width={110} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="var(--color-primary)" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
              <div className="card card-pad">
                <p className="section-title">Priority Distribution</p>
                {analytics.by_priority.length === 0 ? (
                  <EmptyState title="No projects yet" />
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={analytics.by_priority} dataKey="count" nameKey="label" outerRadius={75}>
                        {analytics.by_priority.map((entry, i) => (
                          <Cell key={entry.label} fill={FUNNEL_COLORS[i % FUNNEL_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>

          <div className="stack">
            <div className="card card-pad">
              <p className="section-title">Upcoming Milestones</p>
              {analytics.upcoming_milestones.length === 0 ? (
                <EmptyState title="No upcoming milestones" />
              ) : (
                <div className="stack" style={{ gap: 10 }}>
                  {analytics.upcoming_milestones.map((m) => (
                    <div key={m.id} style={{ fontSize: 13 }}>
                      <strong style={{ display: "block" }}>{m.name}</strong>
                      <span className="muted">Due {m.due_date} · {m.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card card-pad">
              <p className="section-title">Recently Submitted</p>
              {recentQuery.data?.data?.length ? (
                <div className="stack" style={{ gap: 10 }}>
                  {recentQuery.data.data.map((d) => (
                    <Link key={d.id} to={`/demands/${d.id}`} style={{ fontSize: 13, display: "flex", justifyContent: "space-between" }}>
                      <span>{d.title}</span>
                      <StatusChip value={d.status} />
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState title="No demands yet" />
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
