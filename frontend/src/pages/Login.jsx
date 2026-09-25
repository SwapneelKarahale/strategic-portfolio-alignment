import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DEMO_ACCOUNTS = [
  { label: "Business Requestor", email: "requestor.finance@globaldata.example" },
  { label: "Project Manager", email: "priya.nair@globaldata.example" },
  { label: "Management", email: "sarah.miller@globaldata.example" },
  { label: "Admin", email: "admin@globaldata.example" },
];

export default function Login() {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("Password123!");

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await login(email, password);
      navigate("/");
    } catch {
      // error surfaced via auth context state
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="sidebar-brand" style={{ color: "var(--color-text)", marginBottom: 20 }}>
          <span className="sidebar-brand-mark">SP</span>
          Strategic Portfolio Alignment
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div className="form-field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p style={{ color: "var(--color-danger)", fontSize: 13 }}>{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", justifyContent: "center" }}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div style={{ marginTop: 20, fontSize: 12, color: "var(--color-text-muted)" }}>
          <p style={{ marginBottom: 6, fontWeight: 600 }}>Demo accounts (password: Password123!)</p>
          {DEMO_ACCOUNTS.map((acc) => (
            <button
              key={acc.email}
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ marginRight: 6, marginBottom: 6 }}
              onClick={() => setEmail(acc.email)}
            >
              {acc.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
