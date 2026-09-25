import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", roles: null },
  { to: "/demands", label: "Demands", roles: null },
  { to: "/demands/new", label: "New Demand", roles: ["requestor", "project_manager", "admin"] },
  { to: "/portfolio", label: "Portfolio", roles: ["project_manager", "management", "admin"] },
  { to: "/roadmap", label: "Roadmap", roles: null },
  { to: "/execution", label: "Project Execution", roles: ["project_manager", "management", "admin"] },
  { to: "/audit", label: "Audit History", roles: ["project_manager", "management", "admin"] },
  { to: "/admin", label: "Admin", roles: ["admin"] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(user?.role));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-brand-mark">SP</span>
          Strategic Portfolio Alignment
        </div>
        <nav className="sidebar-nav">
          {visibleItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div>{user?.name}</div>
          <span className="sidebar-role-badge">{user?.role?.replace("_", " ")}</span>
          <div style={{ marginTop: 12 }}>
            <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </div>
      </aside>
      <div className="main-area">
        <Outlet />
      </div>
    </div>
  );
}
