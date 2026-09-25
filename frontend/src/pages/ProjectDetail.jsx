import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState } from "../components/States";
import {
  addCapability,
  addMilestone,
  addRequirement,
  getProject,
  updateMilestone,
  updateProject,
  updateProjectStatus,
} from "../services/projects";
import { scheduleProject } from "../services/roadmap";
import { listCapabilities, listUsers } from "../services/lookups";
import { useAuth } from "../context/AuthContext";

const NEXT_STATUS_OPTIONS = {
  "In Progress": ["At Risk", "Blocked", "Completed"],
  "At Risk": ["In Progress", "Blocked", "Completed"],
  Blocked: ["In Progress", "At Risk"],
  Planned: ["In Progress"],
};

export default function ProjectDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canManage = ["project_manager", "admin"].includes(user.role);

  const { data: project, isLoading, isError } = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id) });
  const { data: capabilities } = useQuery({ queryKey: ["capabilities"], queryFn: listCapabilities });
  const { data: pms } = useQuery({ queryKey: ["users", "project_manager"], queryFn: () => listUsers("project_manager") });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["project", id] });

  const [requirementText, setRequirementText] = useState("");
  const [capabilityId, setCapabilityId] = useState("");
  const [milestoneForm, setMilestoneForm] = useState({ name: "", due_date: "" });
  const [roadmapForm, setRoadmapForm] = useState({ quarter: "2026-Q1", sequence: 0, planned_start: "", planned_end: "" });
  const [formError, setFormError] = useState("");

  const assignPmMutation = useMutation({ mutationFn: (pmId) => updateProject(id, { project_manager_id: pmId || null }), onSuccess: invalidate });
  const addRequirementMutation = useMutation({
    mutationFn: () => addRequirement(id, { requirement_text: requirementText }),
    onSuccess: () => {
      setRequirementText("");
      invalidate();
    },
  });
  const addCapabilityMutation = useMutation({
    mutationFn: () => addCapability(id, { capability_id: Number(capabilityId) }),
    onSuccess: () => {
      setCapabilityId("");
      invalidate();
    },
  });
  const addMilestoneMutation = useMutation({
    mutationFn: () => addMilestone(id, milestoneForm),
    onSuccess: () => {
      setMilestoneForm({ name: "", due_date: "" });
      invalidate();
    },
  });
  const updateMilestoneMutation = useMutation({
    mutationFn: ({ milestoneId, status }) => updateMilestone(id, milestoneId, { status }),
    onSuccess: invalidate,
  });
  const scheduleMutation = useMutation({
    mutationFn: () => scheduleProject({ project_id: Number(id), ...roadmapForm, sequence: Number(roadmapForm.sequence) }),
    onSuccess: () => {
      setFormError("");
      invalidate();
    },
    onError: (err) => setFormError(err.response?.data?.error || "Could not schedule this project."),
  });
  const statusMutation = useMutation({
    mutationFn: (status) => updateProjectStatus(id, { status }),
    onSuccess: () => {
      setFormError("");
      invalidate();
    },
    onError: (err) => setFormError(err.response?.data?.error || "Could not update status."),
  });

  if (isLoading) return <LoadingState />;
  if (isError || !project) return <ErrorState message="Project not found or you don't have access." />;

  const nextStatuses = NEXT_STATUS_OPTIONS[project.status] || [];

  return (
    <>
      <PageHeader title={project.name} actions={<><StatusChip value={project.status} /> <StatusChip value={project.health} /></>} />
      <div className="content grid-2">
        <div className="stack">
          <div className="card card-pad">
            <p className="section-title">Overview</p>
            <p className="muted" style={{ fontSize: 14 }}>{project.description}</p>
            {project.business_objective && <p style={{ fontSize: 14, marginTop: 8 }}>{project.business_objective}</p>}
            <div style={{ display: "flex", gap: 24, marginTop: 16, fontSize: 13 }}>
              <div>
                <span className="muted">Priority</span>
                <div>{project.priority}</div>
              </div>
              <div>
                <span className="muted">Estimated effort</span>
                <div>{project.estimated_effort || "—"}</div>
              </div>
              <div>
                <span className="muted">Business function</span>
                <div>{project.business_function || "—"}</div>
              </div>
            </div>
          </div>

          <div className="card card-pad">
            <p className="section-title">Requirements</p>
            {project.requirements.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>No requirements added yet.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {project.requirements.map((r) => (
                  <li key={r.id}>{r.requirement_text}</li>
                ))}
              </ul>
            )}
            {canManage && (
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <input
                  placeholder="Add a requirement…"
                  value={requirementText}
                  onChange={(e) => setRequirementText(e.target.value)}
                  style={{ flex: 1, border: "1px solid var(--color-border)", borderRadius: 6, padding: "8px 10px" }}
                />
                <button className="btn btn-primary btn-sm" disabled={!requirementText.trim()} onClick={() => addRequirementMutation.mutate()}>
                  Add
                </button>
              </div>
            )}
          </div>

          <div className="card card-pad">
            <p className="section-title">Milestones</p>
            {project.milestones.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>No milestones yet.</p>
            ) : (
              <div className="stack" style={{ gap: 10 }}>
                {project.milestones.map((m) => (
                  <div key={m.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 14 }}>
                    <div>
                      <strong>{m.name}</strong>
                      <div className="muted">Due {m.due_date}</div>
                    </div>
                    {canManage ? (
                      <select
                        value={m.status}
                        onChange={(e) => updateMilestoneMutation.mutate({ milestoneId: m.id, status: e.target.value })}
                      >
                        {["Planned", "In Progress", "At Risk", "Overdue", "Completed"].map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <StatusChip value={m.status} />
                    )}
                  </div>
                ))}
              </div>
            )}
            {canManage && (
              <div className="form-grid" style={{ marginTop: 12 }}>
                <div className="form-field">
                  <label>Milestone name</label>
                  <input value={milestoneForm.name} onChange={(e) => setMilestoneForm((f) => ({ ...f, name: e.target.value }))} />
                </div>
                <div className="form-field">
                  <label>Due date</label>
                  <input type="date" value={milestoneForm.due_date} onChange={(e) => setMilestoneForm((f) => ({ ...f, due_date: e.target.value }))} />
                </div>
              </div>
            )}
            {canManage && (
              <button
                className="btn btn-secondary btn-sm"
                disabled={!milestoneForm.name || !milestoneForm.due_date}
                onClick={() => addMilestoneMutation.mutate()}
              >
                Add Milestone
              </button>
            )}
          </div>
        </div>

        <div className="stack">
          <div className="card card-pad">
            <p className="section-title">Project Manager</p>
            {canManage ? (
              <select value={project.project_manager_id || ""} onChange={(e) => assignPmMutation.mutate(e.target.value ? Number(e.target.value) : null)}>
                <option value="">Unassigned</option>
                {pms?.map((pm) => (
                  <option key={pm.id} value={pm.id}>
                    {pm.name}
                  </option>
                ))}
              </select>
            ) : (
              <p>{project.project_manager || "Unassigned"}</p>
            )}
          </div>

          <div className="card card-pad">
            <p className="section-title">Required Capabilities</p>
            {project.capabilities.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>None assigned yet.</p>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {project.capabilities.map((c) => (
                  <span key={c.capability_id} className="chip chip-primary">
                    {c.capability}
                  </span>
                ))}
              </div>
            )}
            {canManage && (
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <select value={capabilityId} onChange={(e) => setCapabilityId(e.target.value)}>
                  <option value="">Select capability…</option>
                  {capabilities?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <button className="btn btn-primary btn-sm" disabled={!capabilityId} onClick={() => addCapabilityMutation.mutate()}>
                  Assign
                </button>
              </div>
            )}
          </div>

          <div className="card card-pad">
            <p className="section-title">Roadmap</p>
            {project.roadmap_item ? (
              <div style={{ fontSize: 14 }}>
                <div>
                  <span className="muted">Quarter</span> {project.roadmap_item.quarter}
                </div>
                <div>
                  <span className="muted">Planned</span> {project.roadmap_item.planned_start} → {project.roadmap_item.planned_end}
                </div>
              </div>
            ) : canManage ? (
              <>
                <p className="muted" style={{ fontSize: 13, marginBottom: 10 }}>
                  Requires at least one requirement and one capability before scheduling.
                </p>
                <div className="form-grid">
                  <div className="form-field">
                    <label>Quarter</label>
                    <input value={roadmapForm.quarter} onChange={(e) => setRoadmapForm((f) => ({ ...f, quarter: e.target.value }))} placeholder="2026-Q1" />
                  </div>
                  <div className="form-field">
                    <label>Sequence</label>
                    <input type="number" value={roadmapForm.sequence} onChange={(e) => setRoadmapForm((f) => ({ ...f, sequence: e.target.value }))} />
                  </div>
                  <div className="form-field">
                    <label>Planned start</label>
                    <input type="date" value={roadmapForm.planned_start} onChange={(e) => setRoadmapForm((f) => ({ ...f, planned_start: e.target.value }))} />
                  </div>
                  <div className="form-field">
                    <label>Planned end</label>
                    <input type="date" value={roadmapForm.planned_end} onChange={(e) => setRoadmapForm((f) => ({ ...f, planned_end: e.target.value }))} />
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  disabled={!roadmapForm.quarter || !roadmapForm.planned_start || !roadmapForm.planned_end || scheduleMutation.isPending}
                  onClick={() => scheduleMutation.mutate()}
                >
                  Schedule on Roadmap
                </button>
              </>
            ) : (
              <p className="muted" style={{ fontSize: 13 }}>Not yet scheduled.</p>
            )}
          </div>

          {canManage && nextStatuses.length > 0 && (
            <div className="card card-pad">
              <p className="section-title">Execution Status</p>
              <div className="stack" style={{ gap: 8 }}>
                {nextStatuses.map((s) => (
                  <button
                    key={s}
                    className={`btn ${s === "At Risk" || s === "Blocked" ? "btn-danger" : "btn-primary"}`}
                    onClick={() => statusMutation.mutate(s)}
                    disabled={statusMutation.isPending}
                  >
                    Mark as {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {formError && <p style={{ color: "var(--color-danger)", fontSize: 13 }}>{formError}</p>}
        </div>
      </div>
    </>
  );
}
