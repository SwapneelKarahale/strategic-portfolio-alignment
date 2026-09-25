import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import { createDemand, updateDemand } from "../services/demands";
import { listBusinessFunctions } from "../services/lookups";

const REQUEST_TYPES = ["Task", "Automation", "Application", "Analytics/Reporting", "Replication", "Data Solution", "Other"];
const PRIORITIES = ["Low", "Medium", "High"];
const STEPS = ["Basic Information", "Business Details", "Review & Submit"];

const initialForm = {
  title: "",
  business_function_id: "",
  request_type: "Other",
  priority: "Medium",
  problem_statement: "",
  business_need: "",
  support_required: "",
  expected_timeline: "",
  additional_details: "",
};

export default function NewDemand() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [validationError, setValidationError] = useState("");

  const { data: businessFunctions } = useQuery({ queryKey: ["business-functions"], queryFn: listBusinessFunctions });

  const createMutation = useMutation({ mutationFn: createDemand });
  const submitMutation = useMutation({ mutationFn: ({ id }) => updateDemand(id, { status: "Submitted" }) });

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function validateStep() {
    if (step === 0 && (!form.title || !form.business_function_id)) {
      setValidationError("Title and business function are required.");
      return false;
    }
    if (step === 1 && form.problem_statement.trim().length < 10) {
      setValidationError("Problem statement must be at least 10 characters.");
      return false;
    }
    setValidationError("");
    return true;
  }

  function next() {
    if (validateStep()) setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setValidationError("");
    setStep((s) => Math.max(s - 1, 0));
  }

  async function saveDraft() {
    const demand = await createMutation.mutateAsync({ ...form, business_function_id: Number(form.business_function_id) });
    navigate(`/demands/${demand.id}`);
  }

  async function submitNow() {
    const demand = await createMutation.mutateAsync({ ...form, business_function_id: Number(form.business_function_id) });
    await submitMutation.mutateAsync({ id: demand.id });
    navigate(`/demands/${demand.id}`);
  }

  const busy = createMutation.isPending || submitMutation.isPending;

  return (
    <>
      <PageHeader title="New Demand" />
      <div className="content" style={{ maxWidth: 720 }}>
        <div className="filter-bar" style={{ marginBottom: 24 }}>
          {STEPS.map((label, i) => (
            <span key={label} className={`chip ${i === step ? "chip-primary" : "chip-neutral"}`}>
              {i + 1}. {label}
            </span>
          ))}
        </div>

        <div className="card card-pad">
          {step === 0 && (
            <>
              <div className="form-field">
                <label>Request title *</label>
                <input value={form.title} onChange={(e) => update("title", e.target.value)} placeholder="e.g. Customer 360 Analytics Platform" />
              </div>
              <div className="form-grid">
                <div className="form-field">
                  <label>Business unit / function *</label>
                  <select value={form.business_function_id} onChange={(e) => update("business_function_id", e.target.value)}>
                    <option value="">Select…</option>
                    {businessFunctions?.map((bf) => (
                      <option key={bf.id} value={bf.id}>
                        {bf.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label>Request type</label>
                  <select value={form.request_type} onChange={(e) => update("request_type", e.target.value)}>
                    {REQUEST_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-field">
                <label>Priority / urgency</label>
                <select value={form.priority} onChange={(e) => update("priority", e.target.value)}>
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <div className="form-field">
                <label>Problem statement *</label>
                <textarea rows={4} value={form.problem_statement} onChange={(e) => update("problem_statement", e.target.value)} placeholder="What is the current pain point?" />
              </div>
              <div className="form-field">
                <label>Business need / expected outcome</label>
                <textarea rows={3} value={form.business_need} onChange={(e) => update("business_need", e.target.value)} />
              </div>
              <div className="form-grid">
                <div className="form-field">
                  <label>Support required</label>
                  <input value={form.support_required} onChange={(e) => update("support_required", e.target.value)} placeholder="e.g. Power BI, Data Engineering" />
                </div>
                <div className="form-field">
                  <label>Expected timeline</label>
                  <input value={form.expected_timeline} onChange={(e) => update("expected_timeline", e.target.value)} placeholder="e.g. Q2 2026" />
                </div>
              </div>
              <div className="form-field">
                <label>Additional details</label>
                <textarea rows={2} value={form.additional_details} onChange={(e) => update("additional_details", e.target.value)} />
              </div>
            </>
          )}

          {step === 2 && (
            <div className="stack" style={{ fontSize: 14 }}>
              <div>
                <strong>{form.title}</strong>
              </div>
              <div className="muted">
                {businessFunctions?.find((bf) => String(bf.id) === String(form.business_function_id))?.name} · {form.request_type} · {form.priority} priority
              </div>
              <div>{form.problem_statement}</div>
              {form.business_need && <div className="muted">Expected outcome: {form.business_need}</div>}
              {form.expected_timeline && <div className="muted">Timeline: {form.expected_timeline}</div>}
            </div>
          )}

          {validationError && <p style={{ color: "var(--color-danger)", fontSize: 13, marginTop: 8 }}>{validationError}</p>}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={back} disabled={step === 0 || busy}>
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button className="btn btn-primary" onClick={next}>
              Next
            </button>
          ) : (
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-secondary" onClick={saveDraft} disabled={busy}>
                Save as Draft
              </button>
              <button className="btn btn-primary" onClick={submitNow} disabled={busy}>
                {busy ? "Submitting…" : "Submit Demand"}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
