import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { LoadingState, ErrorState } from "../components/States";
import { convertDemand, getDemand, reviewDemand, updateDemand } from "../services/demands";
import { useAuth } from "../context/AuthContext";

const REVIEW_ACTIONS_BY_STATUS = {
  Submitted: [{ action: "Under Review", label: "Move to Under Review", variant: "btn-primary" }],
  "Under Review": [
    { action: "Clarification Required", label: "Request Clarification", variant: "btn-secondary" },
    { action: "Validated", label: "Validate", variant: "btn-primary" },
    { action: "Rejected", label: "Reject", variant: "btn-danger" },
  ],
  "Clarification Required": [{ action: "Rejected", label: "Reject", variant: "btn-danger" }],
  Validated: [
    { action: "Approved", label: "Approve", variant: "btn-primary" },
    { action: "Rejected", label: "Reject", variant: "btn-danger" },
  ],
};

export default function DemandDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [comments, setComments] = useState("");

  const { data: demand, isLoading, isError } = useQuery({ queryKey: ["demand", id], queryFn: () => getDemand(id) });

  const submitMutation = useMutation({
    mutationFn: () => updateDemand(id, { status: "Submitted" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["demand", id] }),
  });
  const resubmitMutation = useMutation({
    mutationFn: () => updateDemand(id, { status: "Under Review" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["demand", id] }),
  });
  const reviewMutation = useMutation({
    mutationFn: (action) => reviewDemand(id, action, comments || undefined),
    onSuccess: () => {
      setComments("");
      queryClient.invalidateQueries({ queryKey: ["demand", id] });
    },
  });
  const convertMutation = useMutation({
    mutationFn: () => convertDemand(id),
    onSuccess: (project) => navigate(`/projects/${project.id}`),
  });

  if (isLoading) return <LoadingState />;
  if (isError || !demand) return <ErrorState message="Demand not found or you don't have access." />;

  const isOwner = demand.requestor_id === user.id;
  const isReviewer = ["project_manager", "management", "admin"].includes(user.role);
  const reviewActions = isReviewer ? REVIEW_ACTIONS_BY_STATUS[demand.status] || [] : [];
  const canConvert = isReviewer && demand.status === "Approved" && !demand.has_project && ["project_manager", "admin"].includes(user.role);

  return (
    <>
      <PageHeader title={demand.title} actions={<StatusChip value={demand.status} />} />
      <div className="content grid-2">
        <div className="stack">
          <div className="card card-pad">
            <p className="section-title">Details</p>
            <dl className="stack" style={{ fontSize: 14, gap: 12 }}>
              <div>
                <span className="muted">Business function</span>
                <div>{demand.business_function}</div>
              </div>
              <div>
                <span className="muted">Requestor</span>
                <div>{demand.requestor}</div>
              </div>
              <div>
                <span className="muted">Problem statement</span>
                <div>{demand.problem_statement}</div>
              </div>
              {demand.business_need && (
                <div>
                  <span className="muted">Business need / expected outcome</span>
                  <div>{demand.business_need}</div>
                </div>
              )}
              {demand.support_required && (
                <div>
                  <span className="muted">Support required</span>
                  <div>{demand.support_required}</div>
                </div>
              )}
              <div style={{ display: "flex", gap: 24 }}>
                <div>
                  <span className="muted">Request type</span>
                  <div>{demand.request_type}</div>
                </div>
                <div>
                  <span className="muted">Priority</span>
                  <div>{demand.priority}</div>
                </div>
                {demand.expected_timeline && (
                  <div>
                    <span className="muted">Expected timeline</span>
                    <div>{demand.expected_timeline}</div>
                  </div>
                )}
              </div>
              {demand.additional_details && (
                <div>
                  <span className="muted">Additional details</span>
                  <div>{demand.additional_details}</div>
                </div>
              )}
            </dl>
          </div>

          <div className="card card-pad">
            <p className="section-title">Review History</p>
            {demand.reviews.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>
                No review actions yet.
              </p>
            ) : (
              <div className="stack" style={{ gap: 10 }}>
                {demand.reviews.map((r) => (
                  <div key={r.id} style={{ fontSize: 13, borderLeft: "3px solid var(--color-border)", paddingLeft: 10 }}>
                    <strong>{r.action}</strong> by {r.reviewer} · <span className="muted">{new Date(r.created_at).toLocaleString()}</span>
                    {r.comments && <div className="muted">{r.comments}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="stack">
          {isOwner && demand.status === "Draft" && (
            <div className="card card-pad">
              <p className="section-title">Requestor Actions</p>
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending}>
                Submit Demand
              </button>
            </div>
          )}

          {isOwner && demand.status === "Clarification Required" && (
            <div className="card card-pad">
              <p className="section-title">Requestor Actions</p>
              <p className="muted" style={{ fontSize: 13, marginBottom: 10 }}>
                Update the details above if needed, then resubmit for review.
              </p>
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => resubmitMutation.mutate()} disabled={resubmitMutation.isPending}>
                Resubmit for Review
              </button>
            </div>
          )}

          {reviewActions.length > 0 && (
            <div className="card card-pad">
              <p className="section-title">Review Actions</p>
              <div className="form-field">
                <label>Comments (optional)</label>
                <textarea rows={3} value={comments} onChange={(e) => setComments(e.target.value)} />
              </div>
              <div className="stack" style={{ gap: 8 }}>
                {reviewActions.map((a) => (
                  <button key={a.action} className={`btn ${a.variant}`} onClick={() => reviewMutation.mutate(a.action)} disabled={reviewMutation.isPending}>
                    {a.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {canConvert && (
            <div className="card card-pad">
              <p className="section-title">Portfolio</p>
              <p className="muted" style={{ fontSize: 13, marginBottom: 10 }}>
                This demand is approved. Convert it into a portfolio project to begin requirements and resource planning.
              </p>
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => convertMutation.mutate()} disabled={convertMutation.isPending}>
                Convert to Project
              </button>
            </div>
          )}

          {demand.has_project && (
            <div className="card card-pad">
              <p className="section-title">Portfolio</p>
              <p className="muted" style={{ fontSize: 13 }}>
                This demand has already been converted to a portfolio project.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
